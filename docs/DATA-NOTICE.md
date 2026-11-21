# 网页示例中的数据与署名

## xBD 双期建筑案例

影像与建筑多边形来自 Ritwik Gupta 等的 xBD / xView2，卫星影像来自 Maxar / DigitalGlobe Open Data Program。此页使用固定版本的公开测试镜像。以下影像、派生裁图与足迹轮廓沿用署名、非商业性使用、相同方式共享 4.0 国际许可。仓库的代码许可证单独适用于软件。[xBD 论文](https://arxiv.org/abs/1911.09296) · [xView2 项目](https://www.sei.cmu.edu/projects/xview-2-challenge/) · [固定测试镜像](https://huggingface.co/datasets/ziruihan/xbd_test/tree/361e53f86506e1f221f42a0c0d9619c213220ae5/test) · [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

| 网页建筑 ID | 原测试图块 |
| --- | --- |
| b-8d20ecdd66c0 | hurricane-harvey_00000304 |
| b-bbc5120e609a | hurricane-michael_00000082 |
| b-ce3f795ffe12 | hurricane-florence_00000396 |
| b-abe0ad891f51 | socal-fire_00000877 |
| b-a9482fc5ef0d | hurricane-harvey_00000096 |
| b-2862a8406b72 | hurricane-michael_00000481 |
| b-d64bce19fe1a | hurricane-florence_00000087 |
| b-feb573029a9b | hurricane-michael_00000395 |

每栋在 assets 中各有两期 RGB 场景裁图、两张透明的建筑足迹描边、两张灰底的证据选区裁图。文件名前缀为建筑 ID，时相为 pre 或 post。场景裁图保留原始颜色，取自原 1024 像素图块，边长在 180 至 336 像素之间。描边由原建筑足迹生成。证据选区取自实际推理用的 336 × 336 建筑裁图，足迹外以灰色填充。虚线框叠加在显示层，浏览器截图中的渲染像素用于观看。

逐栋 UID、每幅源影像和标注的相对路径、源影像 SHA-256、场景裁切坐标、建筑裁切坐标、两期测量窗口、中文结果与分级标签均在 [cases.js](assets/cases.js)。源文件路径相对于固定镜像的仓库根目录。xBD 原始分级由数据作者提供；三种中文说明分别来自本项目同栋同选区的旧视觉 RAG、CPU 图像测量和 Qwen3-VL 核验。

## Ebenezer 屋面板外露案例

[ebenezer-fid39.png](assets/ebenezer-fid39.png) 使用 GlobalMedic – RescUAV 于 2017-09-24 采集并通过 OpenAerialMap 发布的 *St. Maarten – Ebenezer* 正射影像。Maja Kucharczyk、Paul R. Nesbit 与 Chris H. Hugenholtz 提供人工参考多边形和 Mask2Former 模型预测。图中展示原正射图的 284 × 284 像素裁区、基线与参考轮廓，以及在等预算模式下补入的完整轮廓。图像使用 CC BY 4.0。[原影像记录](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [作者数据与模型](https://zenodo.org/records/20581719) · [作者论文](https://doi.org/10.3390/rs17203456) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

原始参考对象为 Ebenezer 图层 FID 39，投影坐标系 EPSG:32620。原始影像 SHA-256 为 1506d0c1473849d20b5730e1e502d2193829c0453c399c5235bc8efdc2e17dda。图中 F1、IoU 的作用范围在网页评测页分别标明。

[工作台截图](assets/demo-preview.webp) 由浏览器打开此网页生成，展示上述 xBD 影像的派生裁图，沿用相同的 xBD 署名与 CC BY-NC-SA 4.0 许可。
