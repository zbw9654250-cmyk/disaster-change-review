# Image credits and annotations

[简体中文](DATA-NOTICE.md) · **English**

## Roof damage model comparison

Both panels show the same aerial crop of Ebenezer, Sint Maarten. GlobalMedic / RescUAV captured the orthophoto on September 24, 2017 and shared it through OpenAerialMap. Maja Kucharczyk, Paul R. Nesbit and Chris H. Hugenholtz published the reference outlines and upstream predictions. The project selected outlines from those predictions. The demo draws the original and selected outlines separately on the image. The README previews use the same material. The imagery and outlines are credited under CC BY 4.0. [Crop and outline records](assets/review/SOURCES.md) · [Image record](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [Original labels and predictions](https://zenodo.org/records/20581719)

## Landslides and volcanic eruption

Each pair shows the same area in two Landsat 8 images published by NASA Earth Observatory using USGS data. We cropped both images to the same extent and added circles to point out changes described in the published event reports. The impact shown in the demo refers to the river, road or farmland in the scene.

| Case | Image dates | Image credit | Reported impact |
| --- | --- | --- | --- |
| Oso landslide, Washington | Jan 18 and Mar 23, 2014 | Jesse Allen, NASA Earth Observatory / USGS Landsat | Debris blocked the river and a lake formed upstream. [NASA report](https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/) |
| Mud Creek landslide, Big Sur, California | Apr 20 and May 22, 2017 | Joshua Stevens, NASA Earth Observatory / USGS Landsat | The slide destroyed more than 400 metres of Highway 1, according to the field investigation. [USGS report](https://www.usgs.gov/special-topics/big-sur-landslides/science/mud-creek-landslide-may-20-2017) |
| La Palma eruption, Spain | May 21 and Dec 15, 2021 | Lauren Dauphin, NASA Earth Observatory / USGS Landsat | Lava covered coastal farmland and formed new land in two places along the shore. [NASA report](https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/) |

Original downloads and crop coordinates are listed in the [landslide records](assets/geology/SOURCES.md) and [volcano records](assets/geology/volcano/SOURCES.md). For reuse, see the [NASA Earth Science image guidance](https://science.nasa.gov/earth/faq/).

## Buildings from xBD

The two pairs are crops of xBD test images from the Maxar / DigitalGlobe Open Data Program. Ritwik Gupta and colleagues published the building footprints and damage labels. Each pair uses the same pixel window in both original images, with their original orientation and colors. We added the circles by hand. The capture dates and whole-building grade of `destroyed` come from the linked annotations.

| Case | Image dates | Crop in source pixels (left, top, right, bottom) | xBD building UID and annotations |
| --- | --- | --- | --- |
| Hurricane Michael · industrial building | Nov 29, 2017 and Oct 13, 2018 | `(694, 804, 1024, 1024)`, 330 × 220 | `71b32e9f-6e85-41c1-8f40-12e15cf00ac4` · [Before](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_pre_disaster.json) · [After](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_post_disaster.json) |
| Santa Rosa wildfire · house | May 21 and Oct 11, 2017 | `(84, 84, 288, 220)`, 204 × 136 | `2bd13650-52b7-42f1-8b4a-80c026ecebae` · [Before](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_pre_disaster.json) · [After](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_post_disaster.json) |

The xBD crops are distributed under CC BY-NC-SA 4.0. Keep the original imagery credits and applicable imagery terms when reusing them. [xBD paper](https://arxiv.org/abs/1911.09296) · [License](https://creativecommons.org/licenses/by-nc-sa/4.0/) · [Source records for the eight example buildings](assets/cases.js)

The repository also includes a [roof decking comparison from Ebenezer](assets/ebenezer-fid39.png). GlobalMedic / RescUAV captured the aerial image on September 24, 2017 and published it through OpenAerialMap. The outlines come from Maja Kucharczyk, Paul R. Nesbit and Chris H. Hugenholtz. These materials use CC BY 4.0. [Image record](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [Outline dataset](https://zenodo.org/records/20581719)
