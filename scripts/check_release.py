"""Check repository links, the static Pages site and a real CPU inference from the bundled data."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote, urlsplit


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
    check_inference()
