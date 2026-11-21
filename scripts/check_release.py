"""Check repository links, the static Pages site and a real CPU inference from the bundled data."""
from html.parser import HTMLParser
from datetime import date
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit
from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import unary_union


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


def check_gallery():
    # A classic script with a JSON array also works when the page is opened via file://.
    gallery = SITE / "assets" / "gallery.js"
    records = json.loads(gallery.read_text(encoding="utf-8").strip().removeprefix("const GALLERY = ").removesuffix(";"))
    if not records or len({row["id"] for row in records}) != len(records):
        raise ValueError("Gallery needs cases with unique IDs")
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
        counts = []
        for photo in (before, after):
            check_url(gallery, photo["file"], SITE, asset=True)
            with Image.open(gallery.parent / photo["file"]) as image:
                image.load()
                sizes.append(image.size)
            rings = photo.get("rings", row.get("rings", []))
            if not rings:
                raise ValueError(f"Missing change annotation: {photo['file']}")
            for x, y, width, height, *angle in rings:
                if not (0 <= x < x + width <= 100 and 0 <= y < y + height <= 100
                        and len(angle) <= 1 and all(-180 <= a <= 180 for a in angle)):
                    raise ValueError(f"Invalid change annotation: {photo['file']}")
            counts.append(len(rings))
        if counts[0] != counts[1]:
            raise ValueError(f"Unpaired change annotations: {row['id']}")
        if sizes[0] != sizes[1] or before["file"] == after["file"]:
            raise ValueError(f"Expected two equally sized views: {row['id']}")
    print(f"Verified {len(records)} before-and-after image pairs.")


def outline_polygon(path):
    # Each displayed polygon is an absolute M/L/Z exterior followed by any holes.
    rings = []
    for subpath in path.removesuffix("Z").split("Z"):
        vertices = subpath.removeprefix("M").split("L")
        rings.append([tuple(map(float, vertex.split())) for vertex in vertices])
    return Polygon(rings[0], rings[1:])


def check_model_examples():
    script = SITE / "assets" / "review" / "cases.js"
    data = script.read_text(encoding="utf8").strip()
    cases = json.loads(data.removeprefix("const REVIEW_CASES = ").removesuffix(";"))
    if not cases or len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Model comparison needs examples with unique IDs")
    report = json.loads((ROOT / "results" / "roof_objects.json").read_bytes())
    matched = report["scenes"]["s_ebenezer"]["equal_budget"]["classes"]
    for case in cases:
        recovered = case["baselineIou"] < 0.5 <= case["currentIou"]
        if recovered and case["fid"] not in matched[case["category"]]["new_reference_fids"]:
            raise ValueError(f"Recovered example missing from the reported new matches: {case['id']}")
        check_url(SITE / "index.html", case["image"], SITE, asset=True)
        with Image.open(SITE / case["image"]) as image:
            image.load()
            if image.size != (case["width"], case["height"]):
                raise ValueError(f"Overlay dimensions do not match the image: {case['id']}")
        reference = unary_union([outline_polygon(path) for path in case["reference"]])
        for method in ("baseline", "current"):
            shapes = [outline_polygon(path) for path in case[method]]
            best = max((p.intersection(reference).area / p.union(reference).area for p in shapes), default=0)
            # Display coordinates are rounded to 0.01 px; the UI shows three decimal places.
            if round(best, 3) != round(case[method + "Iou"], 3):
                raise ValueError(f"Overlap differs from the displayed score: {case['id']} / {method}")
    print(f"Verified displayed outlines and overlap scores for {len(cases)} model examples.")


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
    check_gallery()
    check_model_examples()
    check_inference()
