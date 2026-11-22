const GALLERY = [
  {
    "id": "oso",
    "featured": false,
    "en": {
      "name": "Oso landslide",
      "place": "Oso, Washington, USA",
      "type": "Landslide",
      "severity": "River blocked",
      "basis": "River valley · NASA event report",
      "evidence": "The program marks the part of the river valley where the two images differ most. Before the slide, the river bends around fields. Afterward, pale debris crosses the channel and water spreads upstream. NASA records that the slide dammed the river.",
      "credit": "Imagery and event report · NASA Earth Observatory / USGS",
      "beforeAlt": "Before the Oso landslide, a narrow river bends along the base of the slope.",
      "afterAlt": "After the Oso landslide, pale debris crosses the river and water has spread upstream."
    },
    "name": "奥索滑坡",
    "place": "美国 · 华盛顿州奥索",
    "type": "山体滑坡",
    "severity": "河道受阻",
    "basis": "河谷 · NASA 事件记录",
    "evidence": "程序圈出了河谷里变化最集中的一段。灾前，河道弯曲，旁边可见田块。灾后，浅色泥石横过河道，上游水面变宽。NASA 记录了滑坡堵河形成堰塞湖的过程。",
    "credit": "影像与事件记录 · NASA Earth Observatory / USGS",
    "source": "https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/",
    "before": {
      "date": "2014-01-18",
      "file": "geology/oso-pre.png",
      "alt": "奥索滑坡前，河道沿山坡弯曲流过。"
    },
    "after": {
      "date": "2014-03-23",
      "file": "geology/oso-post.png",
      "alt": "奥索滑坡后，泥土和碎屑伸入河道，上游出现更宽的水面。"
    }
  },
  {
    "id": "mud-creek",
    "featured": false,
    "en": {
      "name": "Big Sur landslide",
      "place": "Big Sur, California, USA",
      "type": "Coastal landslide",
      "severity": "Over 400 m of highway destroyed",
      "basis": "Highway segment · USGS survey",
      "evidence": "The program marks a patch of slope beside the coastal highway. The pale road follows the shore before the slide. Gray-brown debris covers the slope afterward and extends beyond the old shoreline. The length of road lost comes from the USGS field survey.",
      "credit": "Imagery · NASA Earth Observatory / USGS",
      "beforeAlt": "Before the Big Sur landslide, the road follows a narrow slope along the coast.",
      "afterAlt": "After the Big Sur landslide, debris covers the road and forms a new bulge in the shoreline."
    },
    "name": "大苏尔滑坡",
    "place": "美国 · 加利福尼亚州大苏尔",
    "type": "海岸边坡滑塌",
    "severity": "超过 400 米公路被毁",
    "basis": "公路路段 · USGS 调查",
    "evidence": "程序圈出了沿海公路旁变化明显的一块坡面。灾前能沿海岸辨认浅色的公路，灾后灰褐色土石覆盖坡面，岸线也向海中凸出。公路损毁长度取自 USGS 现场调查。",
    "credit": "影像 · NASA Earth Observatory / USGS",
    "source": "https://science.nasa.gov/earth/earth-observatory/landslide-buries-scenic-california-highway-90281/",
    "before": {
      "date": "2017-04-20",
      "file": "geology/mud-creek-pre.png",
      "alt": "大苏尔滑坡前的沿海边坡和曲折海岸线。"
    },
    "after": {
      "date": "2017-05-22",
      "file": "geology/mud-creek-post.png",
      "alt": "大苏尔滑坡后，土石堆积伸入海中，海岸轮廓向外突出。"
    }
  },
  {
    "id": "la-palma",
    "en": {
      "name": "La Palma eruption",
      "place": "La Palma, Spain",
      "type": "Volcanic eruption",
      "severity": "Large areas of coastal farmland covered by lava",
      "basis": "Coastal area · NASA image interpretation",
      "evidence": "Use the small harbor at upper left as a landmark. The program marks two changes along the coast to its south. Fields and greenhouses are visible before the eruption. In the later image, dark lava covers parts of the fields and reaches the sea.",
      "credit": "Imagery and event report · NASA Earth Observatory / USGS",
      "beforeAlt": "Before the La Palma eruption, fields and greenhouses line the coast south of the harbor.",
      "afterAlt": "After the La Palma eruption, two dark lava flows cover farmland and form new land along the shore."
    },
    "name": "拉帕尔马火山",
    "place": "西班牙 · 拉帕尔马岛",
    "type": "火山熔岩覆盖",
    "severity": "大片沿岸农田被覆盖",
    "basis": "沿岸区域 · NASA 影像解读",
    "evidence": "以左上方的小港口为参照。程序在港口以南的海岸圈出两处变化。灾前沿岸分布着田块和温室，灾后深色熔岩覆盖部分田块，一直延伸到海边。",
    "credit": "影像与事件记录 · NASA Earth Observatory / USGS",
    "source": "https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/",
    "before": {
      "date": "2021-05-21",
      "file": "geology/volcano/la-palma-before.png",
      "alt": "拉帕尔马岛灾前，左上方港口以南的沿海平地上分布着农田和温室。"
    },
    "after": {
      "date": "2021-12-15",
      "file": "geology/volcano/la-palma-after.png",
      "alt": "拉帕尔马岛灾后，两条深灰色熔岩带到达海边，覆盖农田，形成新的陆地。"
    }
  },
  {
    "id": "hurricane-michael",
    "oursCandidateIndices": [1],
    "en": {
      "name": "Hurricane Michael",
      "place": "Florida, USA",
      "type": "Hurricane",
      "severity": "Destroyed",
      "basis": "Whole building · xBD reference label",
      "evidence": "Look for the two rows of skylights on the building at the top. Below them, the long tan roof inside the circle is visible before the hurricane. Afterward, scattered panels and debris cover the same spot.",
      "credit": "Imagery and building labels · xBD / Maxar",
      "beforeAlt": "A long tan factory roof fills the circle below a building with two rows of skylights.",
      "afterAlt": "Panels and debris are scattered where the long tan roof stood. The rows of skylights above are still visible."
    },
    "name": "迈克尔飓风",
    "place": "美国 · 佛罗里达州",
    "type": "飓风",
    "severity": "毁坏",
    "basis": "整栋建筑 · xBD 原始标注",
    "evidence": "先找上方屋顶的两排采光窗。它们下方的圈内，灾前是一整片浅褐色长屋顶。灾后这片屋顶消失，原处散落着板状碎片。",
    "credit": "影像与建筑标注 · xBD / Maxar",
    "source": "https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_post_disaster.json",
    "before": {
      "date": "2017-11-29",
      "file": "buildings/michael-plant-before.png",
      "alt": "上方屋顶有两排采光窗，圈内是它下方一片连续的浅褐色厂房屋顶。"
    },
    "after": {
      "date": "2018-10-13",
      "file": "buildings/michael-plant-after.png",
      "alt": "上方两排采光窗仍可辨认，下方厂房原来的浅褐色屋顶位置散落着板状碎片。"
    }
  },
  {
    "id": "santa-rosa",
    "oursCandidateIndices": [1],
    "en": {
      "name": "Santa Rosa wildfire",
      "place": "Santa Rosa, California, USA",
      "type": "Wildfire",
      "severity": "Destroyed",
      "basis": "Whole building · xBD reference label",
      "evidence": "Use the blue pool at lower left and the rounded end of the street on the right to find the house. Before the fire, a brown roof with several ridges spans the circle. Afterward, pale debris fills its footprint.",
      "credit": "Imagery and building labels · xBD / Maxar",
      "beforeAlt": "A brown roof with several ridges stands between a blue pool and the rounded end of the street.",
      "afterAlt": "Pale debris fills the former roof footprint between the pool and the rounded end of the street."
    },
    "name": "圣罗莎山火",
    "place": "美国 · 加利福尼亚州圣罗莎",
    "type": "山火",
    "severity": "毁坏",
    "basis": "整栋建筑 · xBD 原始标注",
    "evidence": "用左下方的蓝色泳池和右侧的圆形路端找准这栋住宅。灾前，圈内的棕色屋顶上能看清几条屋脊。灾后，屋顶的轮廓消失，原址只见成片的浅色残迹。",
    "credit": "影像与建筑标注 · xBD / Maxar",
    "source": "https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_post_disaster.json",
    "before": {
      "date": "2017-05-21",
      "file": "buildings/santa-rosa-before.png",
      "alt": "蓝色泳池与圆形路端之间有一栋住宅，圈内棕色屋顶上的几条屋脊清晰可见。"
    },
    "after": {
      "date": "2017-10-11",
      "file": "buildings/santa-rosa-after.png",
      "alt": "泳池和圆形路端仍清晰可辨，圈内原有的棕色屋顶变成大片浅色残迹。"
    }
  }
];
