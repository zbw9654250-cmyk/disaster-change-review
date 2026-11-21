# Post-disaster roof damage review

[简体中文](README.md) · **English**

Find roof holes and exposed decking that need a closer look in aerial imagery after a storm. Across five sites, our method found **22 additional damage features** and kept all 501 baseline matches, with the same number of outlines for reviewers to inspect.

[Open the roof damage comparison](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en) · [Results by site](results/roof_objects.json) · [Original models and data](https://github.com/maja-kucharczyk/roof-damage-assessment)

![The same roof in Ebenezer with damage outlines from the original models and the current method](docs/assets/demo-preview.en.webp)

A roof in Ebenezer on Sint Maarten has an L-shaped patch of exposed decking. The baseline split it into two pieces. The larger piece covers mostly the lower right corner. Our method picked a more complete outline from another model's predictions. The best overlap with the reference outline rose from **0.328 to 0.879** on the intersection over union (IoU) scale, where 1 is an exact match. On another roof, our method recovered a hole the baseline missed, with an IoU of **0.858**. Toggle the human reference or click either image to enlarge it. [Compare the exposed decking](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en&sample=ebenezer-39) · [Compare the roof hole](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en&sample=ebenezer-7)

## What changed at the same review count

The baseline uses separate Mask2Former models for roof holes and exposed decking. Both methods submit the same number of outlines at each site. The 880 reference annotations count individual damage features, so a building can contribute several. A match requires the correct class and an IoU of at least 0.50. Each reference can match one prediction.

| Five sites combined | Outlines to inspect | Matches | False positives | Missed features | F1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 1,269 | 501 | 768 | 379 | 46.63% |
| Current method | 1,269 | **523** | **746** | **357** | **48.67%** |

The additional matches include **13 patches of exposed decking and 9 roof holes**. We replaced 79 very small baseline outlines with candidates from two other sets of predictions. The ranking uses outline shape, overlap with other models and the number of nearby candidates. It also removes duplicates. In a follow-up comparison on the same five sites, filling the 79 slots by area alone recovered 14 features. The full ranking recovered 22. [Ranking comparison](results/roof_ranking_ablation.json)

## Reproduce the result

Download the repository and open [docs/index.html](docs/index.html) to try the demo offline. To run the selection on a CPU, use Python 3.12 and run the commands below from the repository root. All three sets of model predictions for Ebenezer are included.

```sh
python -m pip install -r modules/roof_candidates/requirements.txt
python modules/roof_candidates/apply_recall.py --strong data/roof_candidates/strong.geojson --same data/roof_candidates/same.geojson --dual data/roof_candidates/dual.geojson --mode equal_budget --output candidates.geojson
```

Open `candidates.geojson` in QGIS to inspect 178 outlines, 87 labeled as exposed decking and 91 as holes. Run `python scripts/replay_results.py` to recalculate the table from the saved site counts. [Selection code and inputs](modules/roof_candidates/README.md)

## More examples and tools

- **Before and after imagery.** The five examples use preset circles to show where to look. Descriptions of the landslides and eruption draw on NASA and USGS reports. Building damage grades for the hurricane and wildfire come from xBD. [Compare the images](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=en&view=gallery) · [Image credits](docs/DATA-NOTICE.en.md)
- **Explain roof changes.** The tool compares color, brightness and contrast at corresponding locations in two images, then describes what changed. Qwen3-VL can check the description. Two AI reviewers judged the explanations specific and supported by the images for 20 of 20 buildings, compared with 1 of 20 for the earlier retrieval-assisted generator. Image measurements alone also scored 20 of 20. [Methods and review criteria](modules/observations/README.md)
- **Assess individual buildings.** Given building footprints, the tools measure damaged area per roof and can use Qwen3-VL to assign a preliminary grade. In a separate evaluation of 40 buildings, 14 grades matched xBD and 7 buildings remained ungraded. [Building assessment](modules/buildings/README.md) · [Evaluation details](results/README.md)

The code uses the [MIT license](LICENSE). The roof outlines and the Ebenezer aerial image use CC BY 4.0. The xBD image crops use CC BY-NC-SA 4.0. [Data, imagery and model notices](NOTICE.md)
