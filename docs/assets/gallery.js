const GALLERY = [
  {
    "id": "oso",
    "name": "奥索滑坡",
    "place": "美国 · 华盛顿州奥索",
    "type": "山体滑坡",
    "severity": "河道受阻",
    "basis": "河谷 · NASA 事件记录",
    "evidence": "先看画面中央弯曲的河道。灾后，一条浅灰色的泥石带从山坡一直伸进河谷，横过原来的河道。右侧河湾的水面变宽，形成了堰塞湖。",
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
    "name": "大苏尔滑坡",
    "place": "美国 · 加利福尼亚州大苏尔",
    "type": "海岸边坡滑塌",
    "severity": "超过 400 米公路被毁",
    "basis": "公路路段 · USGS 调查",
    "evidence": "灾前，浅色公路沿海岸连续通过。灾后，画面中央的灰褐色土石盖住了这段公路，一直堆到海里，海岸线在这里向外凸出。",
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
    "name": "拉帕尔马火山",
    "place": "西班牙 · 拉帕尔马岛",
    "type": "火山熔岩覆盖",
    "severity": "大片沿岸农田被覆盖",
    "basis": "沿岸区域 · NASA 影像解读",
    "evidence": "以左上方的小港口为参照。灾前，沿岸是绿色农田和白色温室。灾后，两条深灰色熔岩带穿过农田、延伸入海，海岸线上多出两处突起。",
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
    "id": "harvey",
    "name": "哈维飓风",
    "place": "美国 · 德克萨斯州",
    "type": "飓风",
    "severity": "严重受损",
    "basis": "整栋建筑 · xBD 原始标注",
    "evidence": "白框标出同一块屋面。灾前框内呈绿色，灾后接近白色，整块区域明显变亮。",
    "credit": "影像与建筑标注 · xBD / Maxar",
    "source": "https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-harvey_00000304_post_disaster.json",
    "before": {
      "date": "2017-02-16",
      "file": "buildings/b-8d20ecdd66c0-pre.png",
      "alt": "哈维飓风前的建筑，白框标出用于对照的屋面位置。",
      "box": [
        41.369,
        43.4524,
        13.0952,
        16.6667
      ]
    },
    "after": {
      "date": "2017-08-31",
      "file": "buildings/b-8d20ecdd66c0-post.png",
      "alt": "哈维飓风后的同一栋建筑，白框标出相应的屋面位置。",
      "box": [
        40.1786,
        43.4524,
        13.0952,
        16.6667
      ]
    }
  },
  {
    "id": "socal-fire",
    "name": "南加州山火",
    "place": "美国 · 加利福尼亚州",
    "type": "山火",
    "severity": "无明显损伤",
    "basis": "整栋建筑 · xBD 原始标注",
    "evidence": "白框内的屋面从棕褐色变为灰褐色。灾后，同一区域内的深浅差异更容易分辨。",
    "credit": "影像与建筑标注 · xBD / Maxar",
    "source": "https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/socal-fire_00000877_post_disaster.json",
    "before": {
      "date": "2018-10-23",
      "file": "buildings/b-abe0ad891f51-pre.png",
      "alt": "南加州山火前的建筑，白框标出用于对照的屋面位置。",
      "box": [
        50.8929,
        49.4048,
        14.5833,
        11.0119
      ]
    },
    "after": {
      "date": "2018-11-14",
      "file": "buildings/b-abe0ad891f51-post.png",
      "alt": "南加州山火后的同一栋建筑，白框标出相应的屋面位置。",
      "box": [
        52.9762,
        51.4881,
        14.5833,
        11.0119
      ]
    }
  }
];
