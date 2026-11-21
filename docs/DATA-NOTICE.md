# 网页影像来源与判读依据

## 滑坡和火山

三组案例均使用 NASA Earth Observatory 发布的 Landsat 8 影像。每组两期取同一地点和相同像素范围，页面保留采集日期及影像方向。灾情说明由项目根据官方事件记录整理，受灾程度描述受影响的河道、路段或农田。

| 案例 | 灾前 → 灾后 | 制图与数据 | 受灾程度的依据 |
| --- | --- | --- | --- |
| 奥索滑坡 | 2014-01-18 → 2014-03-23 | Jesse Allen / NASA Earth Observatory，USGS Landsat | 滑坡堆积物堵塞河道，形成堰塞湖。[NASA 事件记录](https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/) |
| 大苏尔滑坡 | 2017-04-20 → 2017-05-22 | Joshua Stevens / NASA Earth Observatory，USGS Landsat | 塌方毁坏超过 400 米公路，长度取自现场调查。[USGS 调查](https://www.usgs.gov/special-topics/big-sur-landslides/science/mud-creek-landslide-may-20-2017) |
| 拉帕尔马岛火山 | 2021-05-21 → 2021-12-15 | Lauren Dauphin / NASA Earth Observatory，USGS Landsat | 熔岩覆盖沿岸田地并入海，形成两处新的陆地。[NASA 事件记录](https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/) |

原图下载、裁切坐标与再使用条件见[两处滑坡的影像记录](assets/geology/SOURCES.md)和[火山影像记录](assets/geology/volcano/SOURCES.md)。仓库首页的[网页截图](assets/demo-preview.webp)展示奥索滑坡，保留同组影像的制图与数据署名。

## xBD 建筑

两栋建筑的灾前后 RGB 来自 xBD 测试分区，影像归属 Maxar / DigitalGlobe Open Data Program，建筑标注由 Ritwik Gupta 等发布。展示的四张 336 × 336 PNG 与仓库测试清单里的无描边裁图逐字节相同。白框取自本项目对同栋两期影像实际测量的局部窗口。采集日期来自对应图块标注文件的 `metadata.capture_date`，整栋程度直接翻译 xBD 的灾后标注。局部说明来自该栋已保存的图像测量与核验记录。

| 案例 | 目标建筑 | 采集日 | 官方标注文件 |
| --- | --- | --- | --- |
| 哈维飓风 | `b-8d20ecdd66c0` | 2017-02-16 → 2017-08-31 | [灾前](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-harvey_00000304_pre_disaster.json) · [灾后，major-damage](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-harvey_00000304_post_disaster.json) |
| 南加州山火 | `b-abe0ad891f51` | 2018-10-23 → 2018-11-14 | [灾前](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/socal-fire_00000877_pre_disaster.json) · [灾后，no-damage](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/socal-fire_00000877_post_disaster.json) |

xBD 派生影像采用署名、非商业性使用、相同方式共享 4.0 国际许可，底图保留原署名与适用条款。[xBD 论文](https://arxiv.org/abs/1911.09296) · [许可条款](https://creativecommons.org/licenses/by-nc-sa/4.0/) · [八栋原始案例的来源和测量窗口](assets/cases.js)

仓库亦保留 [Ebenezer 屋面板外露的定位对照图](assets/ebenezer-fid39.png)。航片由 GlobalMedic – RescUAV 于 2017-09-24 经 OpenAerialMap 发布，轮廓由 Maja Kucharczyk、Paul R. Nesbit 与 Chris H. Hugenholtz 提供，按 CC BY 4.0 署名。[原影像记录](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [轮廓数据](https://zenodo.org/records/20581719)
