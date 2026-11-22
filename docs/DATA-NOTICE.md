# 网页影像来源与判读依据

**简体中文** · [English](DATA-NOTICE.en.md)

## 滑坡和火山

地质灾害案例使用 NASA Earth Observatory 发布的 Landsat 8 影像，灾前和灾后取同一地点、同一像素范围。程序从两期 RGB 计算局部颜色和纹理的变化，降低亮云和开阔水域的影响。拉帕尔马案例另外用灾后低亮度、低色度且相对灾前明显变暗的连续区域生成像素轮廓，沿熔岩变化区边缘描线。网页保留灾前原图，在同一张灾后图上分别显示橙色单候选基线和绿色改进结果。云影和季节差异也可能影响结果，拉帕尔马轮廓属于影像变化证据边界，不是测量得到的熔岩调查边界。河道受阻、公路损毁和农田被覆盖的判读依据见下表。

在仓库根目录安装 `requirements.txt` 的依赖后，运行 `python scripts/generate_gallery_regions.py --output docs/assets/change_regions.js` 可从十张灾前灾后图重新生成基线候选和改进轮廓。基线只保留最高分候选。拉帕尔马的改进结果由像素变化掩膜矢量化生成。迈克尔和圣罗莎的完整屋顶轮廓来自同一裁切范围内的公开 xBD destroyed 建筑 footprint，用来约束整栋受灾建筑的显示范围，来源记录在下表。它们属于公开标注引导的参考轮廓，不是模型独立预测的损伤掩膜。输出同时记录每张输入图的 SHA-256。[生成区域与影像摘要](assets/change_regions.js)

两套结果来自同一个变化检测器，不代表两个独立训练的模型。网页这样拆开是为了对照单候选和经过复核的候选保留策略。精选案例用于说明候选筛选可能带来的定位改善，不作为总体精度结论。

| 案例 | 灾前 → 灾后 | 制图与数据 | 受灾程度的依据 |
| --- | --- | --- | --- |
| 奥索滑坡 | 2014-01-18 → 2014-03-23 | Jesse Allen / NASA Earth Observatory，USGS Landsat | 滑坡堆积物堵塞河道，形成堰塞湖。[NASA 事件记录](https://science.nasa.gov/earth/earth-observatory/landslide-and-barrier-lake-near-oso-washington-83409/) |
| 大苏尔滑坡 | 2017-04-20 → 2017-05-22 | Joshua Stevens / NASA Earth Observatory，USGS Landsat | 塌方毁坏超过 400 米公路，长度取自现场调查。[USGS 调查](https://www.usgs.gov/special-topics/big-sur-landslides/science/mud-creek-landslide-may-20-2017) |
| 拉帕尔马岛火山 | 2021-05-21 → 2021-12-15 | Lauren Dauphin / NASA Earth Observatory，USGS Landsat | 熔岩覆盖沿岸田地并入海，形成两处新的陆地。[NASA 事件记录](https://science.nasa.gov/earth/earth-observatory/a-changed-landscape-on-la-palma-149231/) |

原图下载、裁切坐标与再使用条件见[两处滑坡的影像记录](assets/geology/SOURCES.md)和[火山影像记录](assets/geology/volcano/SOURCES.md)。在线演示直接从仓库中的原图和生成区域文件读取内容。

## xBD 建筑

两组卫星影像取自 xBD 测试集。影像由 Maxar / DigitalGlobe 提供，建筑轮廓和损伤等级由 Ritwik Gupta 等发布。每组从两期原图的相同像素范围裁出，保留原始方向和颜色。网页中的基线圈由 RGB 变化检测器生成，绿色改进结果沿公开 xBD destroyed 建筑 footprint 画出完整闭合轮廓，解决原先只覆盖局部屋顶的问题。采集日、整栋建筑的等级和轮廓来源来自下表的原始标注。

| 案例 | 灾前 → 灾后 | 原图裁切范围（左、上、右、下，像素） | xBD 建筑 UID 与原始标注 |
| --- | --- | --- | --- |
| 迈克尔飓风 · 厂房 | 2017-11-29 → 2018-10-13 | `(694, 804, 1024, 1024)`，330 × 220 | `71b32e9f-6e85-41c1-8f40-12e15cf00ac4` · [灾前](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_pre_disaster.json) · [灾后](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/hurricane-michael_00000022_post_disaster.json) |
| 圣罗莎山火 · 住宅 | 2017-05-21 → 2017-10-11 | `(84, 84, 288, 220)`，204 × 136 | `2bd13650-52b7-42f1-8b4a-80c026ecebae` · [灾前](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_pre_disaster.json) · [灾后](https://huggingface.co/datasets/ziruihan/xbd_test/blob/361e53f86506e1f221f42a0c0d9619c213220ae5/test/labels/santa-rosa-wildfire_00000359_post_disaster.json) |

xBD 派生影像采用署名、非商业性使用、相同方式共享 4.0 国际许可，底图保留原署名与适用条款。[xBD 论文](https://arxiv.org/abs/1911.09296) · [许可条款](https://creativecommons.org/licenses/by-nc-sa/4.0/) · [数据说明与来源记录](../data/xbd/README.md)

仓库亦保留 [Ebenezer 屋面板外露的定位对照图](assets/ebenezer-fid39.png)。航片由 GlobalMedic – RescUAV 于 2017-09-24 经 OpenAerialMap 发布，轮廓由 Maja Kucharczyk、Paul R. Nesbit 与 Chris H. Hugenholtz 提供，按 CC BY 4.0 署名。[原影像记录](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [轮廓数据](https://zenodo.org/records/20581719)
