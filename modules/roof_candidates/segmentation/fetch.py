"""Fetch or verify the original EMD and checkpoint for either published roof model."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import hashlib
import io
import os
from pathlib import Path
import struct
import tempfile
import time
import zipfile
import zlib

import requests

MODEL = "Dominica_SintMaarten_TheBahamas_USVI_RoofHole"
ASSETS = Path(__file__).parent / "weights"
MODELS = {
    "hole": {
        "stem": MODEL, "size": 1600506862,
        ".emd": "e74548d8f530a7e4edad329db0f6d68baa44d0d0edee7fcbd9cb52f8bfe8fd22",
        ".pth": "5e4f63951e85f98a704d181aa14980da5220482009b897aaf63ee1a2beeace39",
    },
    "dual": {
        "stem": "Dominica_SintMaarten_RoofDecking_RoofHole", "size": 1594342404,
        ".emd": "aa13b240c0280ca731a3856ccc67a6c4017ce14528bf160479d127f6f005babf",
        ".pth": "ea2e036a652ac8b6c94b73bd8a2a0a808f9ccbcdc14c903c88c13ac8697656d8",
    },
}


def get_range(url, size, span):
    start, stop = span
    for attempt in range(5):
        try:
            response = requests.get(url, params={"part": f"{start}-{stop}"},
                                    headers={"Range": f"bytes={start}-{stop}"}, timeout=(12, 90))
            response.raise_for_status()
            if (response.headers.get("Content-Range") != f"bytes {start}-{stop}/{size}"
                    or len(response.content) != stop - start + 1):
                raise ValueError("Server returned an incomplete or mismatched byte range")
            return response.content
        except (ValueError, requests.RequestException):
            if attempt == 4:
                raise
            time.sleep(2**attempt)


def fetch(directory, model="hole"):
    directory.mkdir(parents=True, exist_ok=True)
    entry = MODELS[model]
    missing = []
    for suffix in (".emd", ".pth"):
        target = directory / (entry["stem"] + suffix)
        if not target.exists():
            missing.append(target.name)
            continue
        with target.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != entry[suffix]:
                raise ValueError(f"Existing file has an unexpected SHA-256: {target}")
        print(f"Verified existing {target.name} SHA256 {entry[suffix]}")
    if not missing:
        return
    size = entry["size"]
    read_bytes = partial(get_range, f"https://zenodo.org/records/20581719/files/{entry['stem']}.zip", size)
    tail = read_bytes((size-8192, size-1))
    # ZipFile resolves central-directory offsets relative to the partial buffer.
    with zipfile.ZipFile(io.BytesIO(tail)) as archive:
        members = [archive.getinfo(name) for name in missing]
    for info in members:
        target = directory / info.filename
        offset = info.header_offset + size - len(tail)
        header = read_bytes((offset, offset+29))
        if header[:4] != b"PK\x03\x04" or info.compress_type != zipfile.ZIP_DEFLATED:
            raise ValueError("Unexpected archive member format")
        start = offset+30+sum(struct.unpack_from("<HH", header, 26))
        end = start+info.compress_size
        spans = [(i, min(i+(8<<20), end)-1) for i in range(start, end, 8<<20)]
        decoder, checksum, digest = zlib.decompressobj(-15), 0, hashlib.sha256()
        with tempfile.TemporaryDirectory(dir=directory) as tmp:
            staged = Path(tmp) / target.name
            with staged.open("wb") as out, ThreadPoolExecutor(8) as pool:
                for index, chunk in enumerate(pool.map(read_bytes, spans), 1):
                    data = decoder.decompress(chunk)
                    checksum = zlib.crc32(data, checksum)
                    digest.update(data)
                    out.write(data)
                    if index % 10 == 0:
                        print(f"{info.filename}: {index}/{len(spans)}", flush=True)
            if not decoder.eof or checksum != info.CRC or staged.stat().st_size != info.file_size:
                raise ValueError(f"Size or CRC does not match the Zenodo ZIP for {info.filename}")
            if digest.hexdigest() != entry[target.suffix]:
                raise ValueError(f"Unexpected SHA-256 for {info.filename}")
            # Publish atomically without overwriting a concurrent run.
            os.link(staged, target)
        print(f"{info.filename} SHA256 {digest.hexdigest()}", flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--assets-dir", type=Path, default=ASSETS)
    cli.add_argument("--model", choices=tuple(MODELS), default="hole")
    args = cli.parse_args()
    fetch(args.assets_dir, args.model)
