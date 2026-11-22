# Image credits and annotations

[简体中文](DATA-NOTICE.md) · **English**

## Landslides and volcanic eruption

Each geological-disaster pair shows the same area in two Landsat 8 images published by NASA Earth Observatory using USGS data. A program compares local color and texture and reduces the influence of bright clouds and open water. For La Palma, a separate rule finds later-image pixels that are dark, low-chroma and substantially darker than before, then vectorizes the connected zone into an edge-following contour. The viewer keeps the before image plain and shows an orange single-candidate baseline and a green reviewed result on the same post-disaster image. Clouds, shadows and seasonal changes can also affect the result. The La Palma contour is an image-change evidence boundary, not a surveyed lava boundary. The reports below explain the impact on the river, road or farmland.

From the repository root, install the dependencies in `requirements.txt` and run `python scripts/generate_gallery_regions.py --output docs/assets/change_regions.js` to regenerate the baseline candidates and reviewed contours from the ten before/after images. The baseline keeps the highest-scoring candidate. La Palma uses a vectorized pixel-change mask. The complete roof contours in the Michael and Santa Rosa examples use the public xBD destroyed-building footprints in the same crop to constrain the whole affected building. They are reference contours guided by public labels, not independent model damage masks. The output also records a SHA-256 hash for each input. [Generated regions and image hashes](assets/change_regions.js)

| Case | Image dates | Image credit | Reported impact |
| --- | --- | --- | --- |
| Oso landslide, Washington | Jan 18 and Mar 23, 2014 | Jesse Allen, NASA Earth Observatory / USGS Landsat | Debris blocked the river and a lake formed upstream. [NASA report](https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/) |
| Mud Creek landslide, Big Sur, California | Apr 20 and May 22, 2017 | Joshua Stevens, NASA Earth Observatory / USGS Landsat | The slide destroyed more than 400 metres of Highway 1, according to the field investigation. [USGS report](https://www.usgs.gov/special-topics/big-sur-landslides/science/mud-creek-landslide-may-20-2017) |
| La Palma eruption, Spain | May 21 and Dec 15, 2021 | Lauren Dauphin, NASA Earth Observatory / USGS Landsat | Lava covered coastal farmland and formed new land in two places along the shore. [NASA report](https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/) |

The README preview images show Oso and carry the same credits as the Oso image pair. Original downloads and crop coordinates are listed in the [landslide records](assets/geology/SOURCES.md) and [volcano records](assets/geology/volcano/SOURCES.md). For reuse, see the [NASA Earth Science image guidance](https://science.nasa.gov/earth/faq/).

## Buildings from xBD

The two pairs are crops of xBD test images from the Maxar / DigitalGlobe Open Data Program. Ritwik Gupta and colleagues published the building footprints and damage labels. Each pair uses the same pixel window in both original images, with their original orientation and colors. The baseline circles come from the RGB change detector. The green reviewed result follows the complete public xBD destroyed-building footprint in the crop, so the entire affected roof can be inspected. The capture dates, whole-building grades and contour source come from the linked annotations.

| Case | Image dates | Crop in source pixels (left, top, right, bottom) | xBD building UID and annotations |
| --- | --- | --- | --- |
| Hurricane Michael · industrial building | Nov 29, 2017 and Oct 13, 2018 | `(694, 804, 1024, 1024)`, 330 × 220 | `71b32e9f-6e85-41c1-8f40-12e15cf00ac4` · [Before](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_pre_disaster.json) · [After](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_post_disaster.json) |
| Santa Rosa wildfire · house | May 21 and Oct 11, 2017 | `(84, 84, 288, 220)`, 204 × 136 | `2bd13650-52b7-42f1-8b4a-80c026ecebae` · [Before](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_pre_disaster.json) · [After](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_post_disaster.json) |

The xBD crops are distributed under CC BY-NC-SA 4.0. Keep the original imagery credits and applicable imagery terms when reusing them. [xBD paper](https://arxiv.org/abs/1911.09296) · [License](https://creativecommons.org/licenses/by-nc-sa/4.0/) · [Data notes and source records](../data/xbd/README.md)

The online demo reads the original images and generated region file directly from the repository. The repository also includes a [roof decking comparison from Ebenezer](assets/ebenezer-fid39.png). GlobalMedic / RescUAV captured the aerial image on September 24, 2017 and published it through OpenAerialMap. The outlines come from Maja Kucharczyk, Paul R. Nesbit and Chris H. Hugenholtz. These materials use CC BY 4.0. [Image record](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [Outline dataset](https://zenodo.org/records/20581719)
