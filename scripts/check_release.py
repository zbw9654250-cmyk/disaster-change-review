"""Check repository links, the static Pages site and a real CPU inference from the bundled data."""
from html.parser import HTMLParser
from datetime import date
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit
import numpy as np
from PIL import Image

from detect_geology_changes import detect_changes


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs"


def check_url(page, url, boundary, asset=False):
    parts = urlsplit(url)
    if parts.scheme == "data":
        return
    if parts.scheme in {"https", "http", "mailto"} or parts.netloc:
        if asset:
            raise ValueError(f"Offline demo requires a local asset: {page.name} -> {url}")
        return
    if parts.scheme or parts.path.startswith(("/", "\\")):
        raise ValueError(f"Use a relative link: {page.name} -> {url}")
    if not parts.path:
        return
    target = (page.parent / unquote(parts.path)).resolve()
    if not target.is_relative_to(boundary) or not target.exists():
        raise ValueError(f"Unreachable local link: {page.relative_to(ROOT)} -> {url}")


class SiteLinks(HTMLParser):
    def __init__(self, page):
        super().__init__()
        self.page = page

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("src", "href", "poster"):
            if attrs.get(key):
                asset = key != "href" or (tag == "link" and attrs.get("rel") in {"stylesheet", "icon"})
                check_url(self.page, attrs[key], SITE, asset)


def check_links():
    if not (SITE / "index.html").is_file():
        raise FileNotFoundError("docs/index.html")
    for page in SITE.rglob("*.html"):
        SiteLinks(page).feed(page.read_text(encoding="utf8"))
    for page in SITE.rglob("*.css"):
        for url in re.findall(r"url\(\s*['\"]?([^)'\"]+)['\"]?\s*\)", page.read_text(encoding="utf8")):
            check_url(page, url.strip(), SITE, asset=True)
    documentation = list(ROOT.glob("*.md"))
    for folder in ("docs", "data", "modules", "results"):
        documentation.extend((ROOT / folder).rglob("*.md"))
    for page in documentation:
        body = re.sub(r"```.*?```", "", page.read_text(encoding="utf-8-sig"), flags=re.S)
        for enclosed, plain in re.findall(r"!?(?:\[[^\]\n]*\])\((?:<([^>]+)>|([^\s)]+))\)", body):
            check_url(page, enclosed or plain, ROOT)


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def read_regions(path):
    text = path.read_text(encoding="utf-8").strip()
    return json.loads(text.removeprefix("const CHANGE_REGIONS = ").removesuffix(";"))


def check_detector_controls():
    before = np.full((120, 180, 3), 60, dtype=np.uint8)
    if detect_changes(before, before) or detect_changes(before, before + 10):
        raise ValueError("Unchanged or uniformly brightened scenes should have no circles")
    for x in (36, 106):
        after = before.copy()
        after[40:72, x:x+32] = [150, 72, 35]
        center_x, center_y = (x + 16) * 100 / 180, 56 * 100 / 120
        rings = detect_changes(before, after)
        if not any(left < center_x < left + width and top < center_y < top + height
                   for left, top, width, height in rings):
            raise ValueError("A local RGB change should move the detected region with it")


def check_gallery():
    # A classic script with a JSON array also works when the page is opened via file://.
    gallery = SITE / "assets" / "gallery.js"
    records = json.loads(gallery.read_text(encoding="utf-8").strip().removeprefix("const GALLERY = ").removesuffix(";"))
    if not records or len({row["id"] for row in records}) != len(records):
        raise ValueError("Gallery needs cases with unique IDs")
    manifest = gallery.parent / "change_regions.js"
    regions = read_regions(manifest)
    with TemporaryDirectory() as temp:
        regenerated = Path(temp) / "change_regions.js"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "generate_gallery_regions.py"),
                        "--output", str(regenerated)], cwd=ROOT, check=True)
        if read_regions(regenerated) != regions:
            raise ValueError("Published gallery regions differ from the image detector output")
    if regions.keys() != {row["id"] for row in records}:
        raise ValueError("Each gallery case needs generated baseline and model regions")
    for row in records:
        before, after = row["before"], row["after"]
        fields = ("name", "place", "type", "severity", "basis", "evidence", "credit")
        for language, labels in (("zh", row), ("en", row["en"])):
            for field in fields:
                if not labels[field].strip():
                    raise ValueError(f"Missing {language} {field} for {row['id']}")
        for phase in ("before", "after"):
            if not row[phase]["alt"].strip() or not row["en"][phase + "Alt"].strip():
                raise ValueError(f"Missing bilingual image description: {row['id']} / {phase}")
        if date.fromisoformat(before["date"]) >= date.fromisoformat(after["date"]):
            raise ValueError(f"Invalid image chronology: {row['id']}")
        sizes = []
        for phase, photo in (("before", before), ("after", after)):
            check_url(gallery, photo["file"], SITE, asset=True)
            with Image.open(gallery.parent / photo["file"]) as image:
                image.load()
                sizes.append(image.size)
            result = regions[row["id"]]
            if hashlib.sha256((gallery.parent / photo["file"]).read_bytes()).hexdigest() != result[phase + "Sha256"]:
                raise ValueError(f"Displayed image differs from the detector input: {photo['file']}")
        result = regions[row["id"]]
        if "rings" in row or "rings" in before or "rings" in after:
            raise ValueError(f"Use generated baseline/model regions instead of inline circles: {row['id']}")
        baseline = result.get("baseline", {}).get("rings", [])
        ours = result.get("ours", {}).get("rings", [])
        if not baseline or not ours or len(baseline) > len(ours):
            raise ValueError(f"Invalid baseline/model regions: {row['id']}")
        for label, rings in (("baseline", baseline), ("ours", ours)):
            for x, y, width, height, *angle in rings:
                if not (0 <= x < x + width <= 100 and 0 <= y < y + height <= 100
                        and len(angle) <= 1 and all(-180 <= a <= 180 for a in angle)):
                    raise ValueError(f"Invalid {label} annotation: {row['id']}")
        if sizes[0] != sizes[1] or before["file"] == after["file"]:
            raise ValueError(f"Expected two equally sized views: {row['id']}")
    print(f"Verified {len(records)} image pairs and reproduced baseline/model regions from RGB.")


def check_inference():
    cases = ROOT / "data" / "xbd" / "confirm" / "cases.jsonl"
    input_ids = [r["building_id"] for r in read_rows(cases)]
    with TemporaryDirectory() as temp:
        output = Path(temp) / "observations.jsonl"
        subprocess.run([
            sys.executable, str(ROOT / "modules/observations/run_roofs.py"),
            "--cases", str(cases), "--output", str(output),
        ], cwd=temp, check=True)
        observations = read_rows(output)
    if not input_ids or input_ids != [r["building_id"] for r in observations]:
        raise ValueError("CPU output does not cover the example input buildings")
    for row in observations:
        if row["status"] != "ok" or not row["explanation_zh"] or not row["evidence_region"]["post_xyxy"]:
            raise ValueError(f"Incomplete observation for {row['building_id']}")
    print(f"Public links verified; CPU observations generated for {len(input_ids)} buildings.")


if __name__ == "__main__":
    check_links()
    check_detector_controls()
    check_gallery()
    check_inference()
