# 网页影像来源与判读依据

**简体中文** · [English](DATA-NOTICE.en.md)

## 滑坡和火山

三组案例均使用 NASA Earth Observatory 发布的 Landsat 8 影像。每组两期取同一地点和相同像素范围，页面保留采集日期及影像方向。两期影像的对照圈由项目人工标在相同的图上位置，帮助找到下文描述的变化。灾情说明由项目根据官方事件记录整理，受灾程度描述受影响的河道、路段或农田。

| 案例 | 灾前 → 灾后 | 制图与数据 | 受灾程度的依据 |
| --- | --- | --- | --- |
| 奥索滑坡 | 2014-01-18 → 2014-03-23 | Jesse Allen / NASA Earth Observatory，USGS Landsat | 滑坡堆积物堵塞河道，形成堰塞湖。[NASA 事件记录](https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/) |
| 大苏尔滑坡 | 2017-04-20 → 2017-05-22 | Joshua Stevens / NASA Earth Observatory，USGS Landsat | 塌方毁坏超过 400 米公路，长度取自现场调查。[USGS 调查](https://www.usgs.gov/special-topics/big-sur-landslides/science/mud-creek-landslide-may-20-2017) |
| 拉帕尔马岛火山 | 2021-05-21 → 2021-12-15 | Lauren Dauphin / NASA Earth Observatory，USGS Landsat | 熔岩覆盖沿岸田地并入海，形成两处新的陆地。[NASA 事件记录](https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/) |

原图下载、裁切坐标与再使用条件见[两处滑坡的影像记录](assets/geology/SOURCES.md)和[火山影像记录](assets/geology/volcano/SOURCES.md)。仓库首页的[网页截图](assets/demo-preview.webp)展示奥索滑坡，保留同组影像的制图与数据署名。

## xBD 建筑

两组卫星影像取自 xBD 测试集。影像由 Maxar / DigitalGlobe 提供，建筑轮廓和损伤等级由 Ritwik Gupta 等发布。每组从两期原图的相同像素范围裁出，保留原始方向和颜色。黄圈由人工标出，采集日和整栋建筑的“毁坏”（`destroyed`）等级来自下表的原始标注。

| 案例 | 灾前 → 灾后 | 原图裁切范围（左、上、右、下，像素） | xBD 建筑 UID 与原始标注 |
| --- | --- | --- | --- |
| 迈克尔飓风 · 厂房 | 2017-11-29 → 2018-10-13 | `(694, 804, 1024, 1024)`，330 × 220 | `71b32e9f-6e85-41c1-8f40-12e15cf00ac4` · [灾前](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_pre_disaster.json) · [灾后](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_post_disaster.json) |
| 圣罗莎山火 · 住宅 | 2017-05-21 → 2017-10-11 | `(84, 84, 288, 220)`，204 × 136 | `2bd13650-52b7-42f1-8b4a-80c026ecebae` · [灾前](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_pre_disaster.json) · [灾后](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_post_disaster.json) |

xBD 派生影像采用署名、非商业性使用、相同方式共享 4.0 国际许可，底图保留原署名与适用条款。[xBD 论文](https://arxiv.org/abs/1911.09296) · [许可条款](https://creativecommons.org/licenses/by-nc-sa/4.0/) · [八栋原始案例的来源和测量窗口](assets/cases.js)

仓库亦保留 [Ebenezer 屋面板外露的定位对照图](assets/ebenezer-fid39.png)。航片由 GlobalMedic – RescUAV 于 2017-09-24 经 OpenAerialMap 发布，轮廓由 Maja Kucharczyk、Paul R. Nesbit 与 Chris H. Hugenholtz 提供，按 CC BY 4.0 署名。[原影像记录](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [轮廓数据](https://zenodo.org/records/20581719)
