# Image credits and annotations

[简体中文](DATA-NOTICE.md) · **English**

## Landslides and volcanic eruption

Each pair shows the same area in two Landsat 8 images published by NASA Earth Observatory using USGS data. We cropped both images to the same extent and added circles to point out changes described in the published event reports. The impact shown in the demo refers to the river, road or farmland in the scene.

| Case | Image dates | Image credit | Reported impact |
| --- | --- | --- | --- |
| Oso landslide, Washington | Jan 18 and Mar 23, 2014 | Jesse Allen, NASA Earth Observatory / USGS Landsat | Debris blocked the river and a lake formed upstream. [NASA report](https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/) |
| Mud Creek landslide, Big Sur, California | Apr 20 and May 22, 2017 | Joshua Stevens, NASA Earth Observatory / USGS Landsat | The slide destroyed more than 400 metres of Highway 1, according to the field investigation. [USGS report](https://www.usgs.gov/special-topics/big-sur-landslides/science/mud-creek-landslide-may-20-2017) |
| La Palma eruption, Spain | May 21 and Dec 15, 2021 | Lauren Dauphin, NASA Earth Observatory / USGS Landsat | Lava covered coastal farmland and formed new land in two places along the shore. [NASA report](https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/) |

The README preview images show Oso and carry the same credits as the Oso image pair. Original downloads and crop coordinates are listed in the [landslide records](assets/geology/SOURCES.md) and [volcano records](assets/geology/volcano/SOURCES.md). For reuse, see the [NASA Earth Science image guidance](https://science.nasa.gov/earth/faq/).

## Buildings from xBD

The Hurricane Harvey and Southern California wildfire cases use satellite imagery from Maxar / DigitalGlobe and building annotations from xBD by Ritwik Gupta and colleagues. Each view is a 336 × 336 pixel crop. The circle marks the roof area measured in that image. Capture dates and whole-building grades come from the xBD annotations. The descriptions of local appearance come from the project's image measurements and review records.

| Case and building | Image dates | xBD building label |
| --- | --- | --- |
| Hurricane Harvey · `b-8d20ecdd66c0` | Feb 16 and Aug 31, 2017 | Major damage. [Before](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-harvey_00000304_pre_disaster.json) · [After](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-harvey_00000304_post_disaster.json) |
| Southern California wildfire · `b-abe0ad891f51` | Oct 23 and Nov 14, 2018 | No damage. [Before](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/socal-fire_00000877_pre_disaster.json) · [After](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/socal-fire_00000877_post_disaster.json) |

The xBD crops are distributed under CC BY-NC-SA 4.0. Keep the original imagery credits and applicable imagery terms when reusing them. [xBD paper](https://arxiv.org/abs/1911.09296) · [License](https://creativecommons.org/licenses/by-nc-sa/4.0/) · [Source records for the eight example buildings](assets/cases.js)

The repository also includes a [roof decking comparison from Ebenezer](assets/ebenezer-fid39.png). GlobalMedic / RescUAV captured the aerial image on September 24, 2017 and published it through OpenAerialMap. The outlines come from Maja Kucharczyk, Paul R. Nesbit and Chris H. Hugenholtz. These materials use CC BY 4.0. [Image record](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [Outline dataset](https://zenodo.org/records/20581719)
