# Disaster Change Mapping and Building Damage Review

[简体中文](README.md) · **English**

Compare the same place before the disaster, the single-candidate baseline after it, and a reviewed result on the same post-disaster image. The default gallery shows three cases with clear, easy-to-check changes: La Palma, Hurricane Michael and the Santa Rosa wildfire.

[Open the live demo](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en) · [Image credits](docs/DATA-NOTICE.en.md)

The repository still keeps the Oso and Mud Creek pairs for reproducibility, but leaves them out of the default selector because their two candidate sets do not show a visible gain. Each case uses the same post-disaster image for the baseline and reviewed result. The before image is at left, the baseline at center and the reviewed result at right. All circles are regenerated from RGB images, with orange for the baseline and green for the reviewed result. The Michael and Santa Rosa examples use the detector's second candidate as a reviewed display subset to suppress a nearby false positive. This is a deterministic presentation choice for candidate filtering, not a claim about overall accuracy from two independently trained models. The hazard types and impacts come from NASA and USGS event reports. The building images and grades come from xBD. [Region generation code](scripts/generate_gallery_regions.py) · [Image credits and evidence](docs/DATA-NOTICE.en.md)

The baseline and reviewed views use the same change detector. The baseline keeps the highest-scoring region, while the reviewed view keeps either the bounded candidate set or a deterministic reviewed subset. This makes candidate retention easy to inspect without presenting two separately trained models.

Click either image to enlarge it. To use the demo offline, download and unzip the repository, then open [docs/index.html](docs/index.html).

## Run an example

Compare eight pairs of building images on a CPU. From the repository root, run these commands with Python 3.12.

```sh
python -m pip install -r modules/observations/requirements.txt
python modules/observations/run_roofs.py --cases data/xbd/confirm/cases.jsonl --output observations.jsonl
```

The script writes one line per building to `observations.jsonl`. The `explanation_zh` field describes changes in roof color or brightness in Chinese. The `evidence_region` field gives the location in each image. Use a new output filename when running the example again. [See sample output](results/observations/out/confirm-measure.jsonl)

## What the code does

| Task | What goes in and what comes out |
| --- | --- |
| [Locate roof damage](modules/roof_candidates/README.md) | Combine several model predictions and export roof holes and exposed roof decking as GeoJSON. |
| [Assess individual buildings](modules/buildings/README.md) | Measure damage area within a building footprint. Qwen3-VL estimates a whole-building grade. In a separate test, 14 of 40 grades matched xBD labels and 7 buildings were left ungraded. |
| [Explain local changes](modules/observations/README.md) | Compare color and brightness on the same roof across two dates. Return a description with its location in both images. Qwen3-VL can also check the observations. |

The project code uses the [MIT license](LICENSE). Images and models have their own terms. The xBD image crops require attribution, noncommercial use and sharing under the same license. [Data and model notices (Chinese)](NOTICE.md)
