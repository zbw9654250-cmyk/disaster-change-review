# Disaster change mapping and building damage review

[简体中文](README.md)

The project takes aligned RGB images from before and after a disaster. It returns change candidates, affected-area contours and building damage observations. The web demo places the before image, the post-disaster baseline and the reviewed result in one row so you can check coverage and contour location.

[Open the live demo](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en)

## Three baselines

The project compares three change-localization methods. All three take the same aligned before and after RGB pair and return a change region. The web demo currently draws the first baseline. The other two run through the optional command-line entry point.

| Baseline | Method | Output | Role |
| --- | --- | --- | --- |
| RGB-rule-v1 | Color, local texture and brightness residuals with connected-component filtering | Ellipse candidates | Explainable CPU baseline |
| FC-Siam-Diff | Shared-weight Siamese bi-temporal encoder and difference decoder | Binary change mask | Main deep-learning baseline |
| BIT | Bi-temporal CNN, semantic tokens and Transformer blocks | Binary change mask | Global-change baseline |

The orange dashed outline in the web demo is RGB-rule-v1. FC-Siam-Diff and BIT use the public implementation and checkpoint entry points from [Open-CD](https://github.com/likyoo/open-cd) / [Open-CD Lite](https://github.com/taktpixel/opencd-lite). The weights remain upstream artifacts and are not reported as this project's disaster-damage accuracy. The xBD footprints in this repository describe building extent, not pixel-level damage masks, so they are not used to invent FC-Siam-Diff or BIT pixel IoU.

Run the shared output command:

```sh
python scripts/run_change_baselines.py \
  --model rgb \
  --before docs/assets/geology/volcano/la-palma-before.png \
  --after docs/assets/geology/volcano/la-palma-after.png \
  --output artifacts/baselines/la-palma/rgb
```

The command writes `mask.png`, `overlay.png`, `regions.geojson` and `metrics.json`. FC-Siam-Diff and BIT require the optional package and a compatible checkpoint:

```sh
python -m pip install "opencd-lite[torch]"
python scripts/run_change_baselines.py --model fc_siam_diff \
  --before BEFORE.png --after AFTER.png --checkpoint fc_siam_diff.pth \
  --output artifacts/baselines/example/fc_siam_diff --device cuda
```

The common evaluation should report change IoU, precision, recall, F1, building-footprint coverage, miss rate, p50/p95 latency and peak memory. Four-level building damage grades require a separate xView2 two-stage localization and classification baseline.

## The reviewed result

The reviewed result adds a pixel-change mask, contour vectorization and a complete-building constraint for the building examples.

- Geological-disaster images use brightness, color and before-after differences to build a continuous change mask. Morphological processing and `find_contours` then produce a green closed contour along the change boundary.
- Building images use the public xBD `destroyed` building footprint to constrain the affected building area. The green contour covers the full industrial building or house, so you can check whether the baseline candidate missed part of the roof.

The baseline and reviewed result use the same post-disaster image. The contour sources and data licenses are listed in [Data notes](docs/DATA-NOTICE.en.md).

## Examples in the demo

The default page shows three examples.

| Example | Image type | Output shown in the demo |
| --- | --- | --- |
| La Palma eruption | Landsat 8 before and after images | Pixel contour around the main lava-change zone |
| Hurricane Michael | xBD industrial-building before and after images | Complete affected-building footprint contour |
| Santa Rosa wildfire | xBD house before and after images | Complete affected-building footprint contour |

[View the three examples](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en)

## Run the web demo locally

The web page is static. It does not need a backend service or a GPU. The commands below use Python 3.12.

```sh
git clone https://github.com/zbw9654250-cmyk/disaster-change-review.git
cd disaster-change-review
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_gallery_regions.py --output docs/assets/change_regions.js
python -m http.server 8000 --directory docs
```

Open `http://127.0.0.1:8000/?lang=en` in a browser. `generate_gallery_regions.py` regenerates the candidate and contour file from the before and after images in the repository.

## Run the building image example

The following command processes eight building samples on a CPU and writes one observation for each building.

```sh
python -m pip install -r modules/observations/requirements.txt
python modules/observations/run_roofs.py --cases data/xbd/confirm/cases.jsonl --output observations.jsonl
```

The output is written to `observations.jsonl`. A sample output file is [confirm-measure.jsonl](results/observations/out/confirm-measure.jsonl).

## Deploy the project

GitHub Pages publishes the `docs` directory. The repository includes `.github/workflows/pages.yml`. After you push to the `main` branch, GitHub runs the tests and publishes the page.

```sh
git add .
git commit -m "update demo"
git push origin main
```

For a new repository, open `Settings`, `Pages` and `Build and deployment`, then set the source to `GitHub Actions`. The Pages settings show the public URL after deployment. You can also upload the `docs` directory to another static hosting service.

## Dataset contents

| Data | Contents | Use |
| --- | --- | --- |
| `docs/assets/geology` | Three before and after geological-disaster pairs for the Oso landslide, Mud Creek landslide and La Palma eruption | Change detection and web examples |
| `docs/assets/buildings` | Two xBD building pairs for the Hurricane Michael industrial building and the Santa Rosa wildfire house | Whole-building contour examples |
| `data/xbd/confirm` | Eight building samples with eight before and after crop pairs, 16 masks and damage grades. The events include hurricanes, wildfire and several damage levels | CPU observation example and regression checks |
| `data/xbd/context-confirm` | Eight cross-disaster scenes with images and masks for flooding, wildfire, tsunami, hurricanes and an earthquake | Context review |
| `data/xbd/stress` | Thirty-two stress samples with 64 paired images, masks and reference change images | Misalignment, blur and external-change tests |
| `data/xbd/library/windows` | 132 building windows with retrieval indexes | Retrieval and evaluation |
| `data/ebenezer` | Eight aerial roof images, building footprints, damage GeoJSON and an orthophoto | Roof damage contour module |
| `data/roof_candidates` | Three GeoJSON candidate layers named `strong`, `same` and `dual` | Roof candidate fusion module |

The geological-disaster images come from NASA Earth Observatory and USGS. The building images and labels come from xBD. See [Data notes](docs/DATA-NOTICE.en.md), [NOTICE.md](NOTICE.md) and the README files in each data directory for sources, crop ranges and licenses.

## Code modules

| Module | Purpose |
| --- | --- |
| [Change region generation](scripts/generate_gallery_regions.py) | Generate the baseline candidates and reviewed contours used by the web page |
| [Three-baseline runner](scripts/run_change_baselines.py) | Run RGB-rule-v1, FC-Siam-Diff and BIT with one output contract |
| [Roof damage localization](modules/roof_candidates/README.md) | Merge segmentation predictions and export roof damage GeoJSON |
| [Building damage assessment](modules/buildings/README.md) | Measure damage area inside a building footprint |
| [Local change observations](modules/observations/README.md) | Compare two roof images and return evidence locations and text |

The project code uses the [MIT license](LICENSE). Public images, labels and models follow their own licenses.

