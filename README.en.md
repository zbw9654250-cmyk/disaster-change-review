# Disaster Change Mapping and Building Damage Review

[简体中文](README.md) · **English**

Compare two images of the same place before and after a disaster. In the Oso landslide example, follow the river to see how debris from the slope reached the valley floor.

[Open the live demo](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en) · [Image credits](docs/DATA-NOTICE.en.md)

![Oso before and after the landslide, with automatically detected changes circled](docs/assets/demo-preview.en.webp)

The demo has five cases. For the two landslides and the La Palma eruption, a program compares the before and after RGB images and circles areas of visible change. The circles can be regenerated from the images. The hazard types and impacts come from NASA and USGS event reports. The two building cases use preset circles to show a factory after a hurricane and a house after a wildfire. Their damage grades come from xBD. [Change detection code](scripts/detect_geology_changes.py) · [Image credits and evidence](docs/DATA-NOTICE.en.md)

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

## How roof damage selection improves on the baseline

Across five sites, each method returned 1,269 candidates for review. We ranked outlines by their shape and agreement across models. This kept all 501 baseline matches and recovered 13 more patches of exposed decking and 9 more roof holes. Correct matches rose from **501 to 523**, and false positives fell from **768 to 746**. These counts measure individual roof damage features. [Open the comparison in the demo](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en#baseline-comparison) · [Results by site](results/roof_objects.json)

The project code uses the [MIT license](LICENSE). Images and models have their own terms. The xBD image crops require attribution, noncommercial use and sharing under the same license. [Data and model notices (Chinese)](NOTICE.md)
