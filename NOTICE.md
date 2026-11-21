# 代码、模型与数据来源

本仓库的项目代码采用 MIT 许可。影像、派生裁图、建筑足迹和第三方模型各有自己的发布条件。[代码许可](LICENSE)

| 内容 | 来源、改动和使用条件 |
| --- | --- |
| xBD 影像、建筑标注及派生数据 | Ritwik Gupta 等，xBD / xView2；底图来自 Maxar / DigitalGlobe Open Data Program。使用公开训练和测试镜像的固定版本，裁出建筑、栅格化足迹，制作局部取样及受控图像对。随附 xBD 派生数据按 CC BY-NC-SA 4.0 标注；保留底层影像署名及适用的非商业使用条件。详见 [xBD 来源清单](data/xbd/README.md)。 |
| 加勒比屋面损伤轮廓与训练所得参数 | Maja Kucharczyk、Paul R. Nesbit、Chris H. Hugenholtz 的四地区屋面研究。样例从已公布模型的 Ebenezer 图层提取，统一为 WGS84，保留类别；衍生数据及从该数据拟合的候选策略保留 CC BY 4.0 署名。[研究仓库](https://github.com/maja-kucharczyk/roof-damage-assessment) · [带版本的模型与数据](https://zenodo.org/records/20581719) · [许可](https://creativecommons.org/licenses/by/4.0/) |
| Ebenezer 2017 年航片 | GlobalMedic – RescUAV，通过 OpenAerialMap 发布；使用地理裁片，按影像手工描绘 8 栋建筑示范范围，并据此生成模型输入。保留 CC BY 4.0。[原始影像记录](https://api.openaerialmap.org/meta/59e62be63d6412ef7220c38b) · [样例说明](data/ebenezer/README.md) |
| Qwen3-VL-4B-Instruct | 可选模型。部署者从发布方获取权重，并按模型卡使用。[模型卡和许可](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct) |
| 用户界面中的示例影像 | 本地静态裁图分别沿用以上来源的条件。网页提供相应署名和修改说明。[网页资产说明](docs/DATA-NOTICE.md) |

模型核验借鉴了 Woodpecker 的视觉事实检查，周边颜色对照借鉴相对辐射归一化。实现和评测见模块目录。[Woodpecker](https://github.com/VITA-MLLM/Woodpecker) · [Planet Labs](https://github.com/planetlabs/radiometric_normalization)
