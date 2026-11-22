# Disaster change mapping and building damage review

[简体中文](README.md)

The project takes an aligned RGB image pair from before and after a disaster. It draws the changed area as a contour. The web page places the before image, a baseline result and a reviewed result together so you can check whether the detected area is complete.

[Open the live demo](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en)

## The baselines

The page provides three baselines. All three take the same aligned before and after image pair.

| Baseline | Method | Output |
| --- | --- | --- |
| RGB-rule-v1 | Computes color, texture and brightness differences, then filters connected regions | Orange candidate rings |
| FC-Siam-Diff | Uses a shared-weight Siamese network and feature differences for bi-temporal change localization | Binary change mask and green contour |
| BIT | Uses a bi-temporal CNN, semantic tokens and Transformer blocks for global change modeling | Binary change mask and green contour |

RGB-rule-v1 is the CPU baseline. FC-Siam-Diff and BIT use the [Open-CD Lite](https://github.com/taktpixel/opencd-lite) inference interface and the LEVIR-CD checkpoints from the [Open-CD Model Zoo](https://huggingface.co/likyoo/Open-CD_Model_Zoo). The FC-Siam-Diff and BIT results on the page were generated on an RTX 5090 for the five demo pairs. The page stores contours and metrics, and does not store model weights.

Both deep checkpoints were trained on LEVIR-CD building-change data. The geological-disaster and xBD images on the page are cross-dataset inputs, so the results are zero-shot change-localization examples. They are not disaster-damage accuracy results. An xBD footprint describes building extent, not a pixel-level damage mask, so it is not used to invent pixel IoU.

## Results on the page

Choose a case first, then choose RGB-rule-v1, FC-Siam-Diff or BIT in the baseline section. If a deep model produces no positive pixels for a case, the page shows an empty contour and keeps the model latency and mask fraction. The empty contour is part of the actual model output.

The page opens with three featured cases.

| Case | Input | Page content |
| --- | --- | --- |
| La Palma eruption | Landsat 8 before and after images | Change contour around the lava-covered area |
| Hurricane Michael | xBD industrial-building before and after images | Contour for the affected building |
| Santa Rosa wildfire | xBD house before and after images | Contour for the affected house |

The Oso landslide and Mud Creek landslide are also available from the case buttons.

[View the live demo](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en)

## Output files

All three baselines use `scripts/run_change_baselines.py`. Each run writes the following files.

- `mask.png` is a binary change mask.
- `overlay.png` draws the contour on the post-disaster image.
- `regions.geojson` stores the contour in image-percentage coordinates.
- `metrics.json` stores the model, input image hashes, mask fraction, contour count and latency.

RGB-rule-v1 runs without a GPU.

```sh
python scripts/run_change_baselines.py \
  --model rgb \
  --before docs/assets/geology/volcano/la-palma-before.png \
  --after docs/assets/geology/volcano/la-palma-after.png \
  --output artifacts/baselines/la-palma/rgb
```

FC-Siam-Diff requires its matching config and checkpoint.

```sh
python -m pip install "opencd-lite[torch]"
python scripts/run_change_baselines.py --model fc_siam_diff \
  --config opencd-lite/configs/fcsn/fc_siam_diff_256x256_40k_levircd.py \
  --before BEFORE.png --after AFTER.png \
  --checkpoint fc_siam_diff_256x256_40k_levircd.pth \
  --output artifacts/baselines/example/fc_siam_diff --device cuda
```

Run BIT with the same command by changing `--model` to `bit` and using `opencd-lite/configs/bit/bit_r18_256x256_40k_levircd.py`. Download the checkpoint from Open-CD Model Zoo. Do not commit model weights to this repository.

## Run the web page locally

The web page is static and does not need a backend service. Run the following commands, then open `http://127.0.0.1:8000/?lang=en` in a browser.

```sh
git clone https://github.com/zbw9654250-cmyk/disaster-change-review.git
cd disaster-change-review
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m http.server 8000 --directory docs
```

Run the following command if you regenerate the gallery contours.

```sh
python scripts/generate_gallery_regions.py --output docs/assets/change_regions.js
```

`docs/assets/baseline_outputs.js` stores the FC-Siam-Diff and BIT contours and metrics generated on the RTX 5090. After running a deep model again, update the same fields in this file. Keep the model weights on the local machine or the server.

For the five demo pairs, FC-Siam-Diff took about 2.64 to 2.70 seconds per image pair, and BIT took about 2.78 to 2.88 seconds. FC-Siam-Diff returned contours for La Palma and Mud Creek. BIT returned zero positive contours for all five cross-dataset cases. The page keeps these raw outputs so the cross-dataset behavior can be checked.

## Deploy the project

GitHub Pages publishes the `docs` directory. The repository includes `.github/workflows/pages.yml`. After a commit reaches the `main` branch, GitHub Actions runs the tests and publishes the page.

```sh
git add .
git commit -m "update change detection demo"
git push origin main
```

You can also publish the `docs` directory on another static hosting service. Deep-model inference needs a GPU and a checkpoint. The web page only displays the generated contours and metrics.

## Dataset contents

| Path | Contents | Use |
| --- | --- | --- |
| `docs/assets/geology` | Three before and after pairs for the Oso landslide, Mud Creek landslide and La Palma eruption | Geological-disaster change localization and web cases |
| `docs/assets/buildings` | Two xBD pairs for the Hurricane Michael industrial building and Santa Rosa wildfire house | Whole-building contour cases |
| `data/xbd/confirm` | Eight building samples with paired crops, masks and damage grades | CPU review and regression checks |
| `data/xbd/context-confirm` | Scenes for flooding, wildfire, tsunami, hurricanes and an earthquake | Context review |
| `data/xbd/stress` | Stress samples with misalignment, blur and external changes | Robustness tests |
| `data/xbd/library/windows` | Building windows and retrieval indexes | Retrieval and evaluation |
| `data/ebenezer` | Aerial roof images, building footprints, damage GeoJSON and an orthophoto | Roof damage contour module |
| `data/roof_candidates` | Three GeoJSON candidate layers named `strong`, `same` and `dual` | Roof candidate fusion module |

The geological-disaster images come from NASA Earth Observatory and USGS. The building images and labels come from xBD. See [Data notes](docs/DATA-NOTICE.en.md), [NOTICE.md](NOTICE.md) and the README files in each data directory for sources, crop ranges and licenses.

## Code modules

| Module | Purpose |
| --- | --- |
| [Change region generation](scripts/generate_gallery_regions.py) | Generate the RGB candidates and reviewed contours used by the page |
| [Three-baseline runner](scripts/run_change_baselines.py) | Run RGB-rule-v1, FC-Siam-Diff and BIT with one output contract |
| [Roof damage localization](modules/roof_candidates/README.md) | Merge segmentation predictions and export roof damage GeoJSON |
| [Building damage assessment](modules/buildings/README.md) | Measure damage area inside a building footprint |
| [Local change observations](modules/observations/README.md) | Compare two roof images and return evidence locations and text |

The project code uses the [MIT license](LICENSE). Public images, labels and models follow their own licenses.

