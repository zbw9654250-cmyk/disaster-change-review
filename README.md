# 灾变影像变化定位与建筑损伤复核

[English](README.en.md)

项目接收同一地点的灾前和灾后 RGB 影像，并把变化位置画成轮廓。网页把灾前影像、基线结果和复核结果放在一起，便于检查变化位置是否完整。

[打开在线演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh)

## 基线是什么

网页提供三种基线。三种方法都接收同一对对齐的灾前和灾后影像。

| 基线 | 方法 | 输出 |
| --- | --- | --- |
| RGB-rule-v1 | 计算颜色、纹理和亮度差异，再筛选连通区域 | 橙色候选圈 |
| FC-Siam-Diff | 共享权重的双时相 Siamese 网络，用特征差异定位变化 | 二值变化掩膜和绿色轮廓 |
| BIT | 双时相 CNN 加语义 token 和 Transformer，建模全局变化 | 二值变化掩膜和绿色轮廓 |

RGB-rule-v1 是 CPU 基线。FC-Siam-Diff 和 BIT 使用 [Open-CD Lite](https://github.com/taktpixel/opencd-lite) 的推理接口，以及 [Open-CD Model Zoo](https://huggingface.co/likyoo/Open-CD_Model_Zoo) 提供的 LEVIR-CD checkpoint。网页中的 FC-Siam-Diff 和 BIT 结果是在 RTX 5090 上对五组演示影像运行后生成的，网页只保存轮廓和指标，不保存模型权重。

两个深度模型的 checkpoint 训练于 LEVIR-CD 建筑变化数据。网页中的地质灾害和 xBD 影像属于跨数据集输入，所以结果是零样本变化定位示例，不能直接当作灾损精度。xBD footprint 表示建筑范围，也不是逐像素灾损掩膜，项目不会据此虚构像素 IoU。

## 网页中的结果

打开网页后，先选择案例，再在“三条基线”中选择 RGB-rule-v1、FC-Siam-Diff 或 BIT。当前案例没有深度模型正类区域时，网页会显示空轮廓，并保留该模型的推理时间和掩膜比例。空轮廓也是模型实际输出的一部分。

默认精选三个案例。

| 案例 | 输入 | 网页内容 |
| --- | --- | --- |
| 拉帕尔马火山 | Landsat 8 灾前灾后影像 | 熔岩覆盖区域的变化轮廓 |
| 迈克尔飓风 | xBD 厂房灾前灾后影像 | 受灾厂房的建筑轮廓 |
| 圣罗莎山火 | xBD 住宅灾前灾后影像 | 受灾住宅的建筑轮廓 |

网页还保留奥索滑坡和大苏尔滑坡，可通过顶部案例按钮查看。网页链接如下。

[查看在线演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh)

## 输出内容

三个基线共用 `scripts/run_change_baselines.py`。每次运行都会写出以下文件。

- `mask.png` 是二值变化掩膜。
- `overlay.png` 是把轮廓画回灾后影像的结果。
- `regions.geojson` 是百分比坐标的轮廓。
- `metrics.json` 记录模型、输入图像哈希、掩膜比例、轮廓数量和推理时间。

RGB 基线可以直接运行。

```sh
python scripts/run_change_baselines.py \
  --model rgb \
  --before docs/assets/geology/volcano/la-palma-before.png \
  --after docs/assets/geology/volcano/la-palma-after.png \
  --output artifacts/baselines/la-palma/rgb
```

FC-Siam-Diff 需要对应的配置文件和 checkpoint。

```sh
python -m pip install "opencd-lite[torch]"
python scripts/run_change_baselines.py --model fc_siam_diff \
  --config opencd-lite/configs/fcsn/fc_siam_diff_256x256_40k_levircd.py \
  --before BEFORE.png --after AFTER.png \
  --checkpoint fc_siam_diff_256x256_40k_levircd.pth \
  --output artifacts/baselines/example/fc_siam_diff --device cuda
```

BIT 使用相同命令，把 `--model` 换成 `bit`，并把配置换成 `opencd-lite/configs/bit/bit_r18_256x256_40k_levircd.py`。权重从 Open-CD Model Zoo 下载，不能提交到本仓库。

## 本地运行网页

网页是静态文件，不需要后端服务。运行下面的命令后，用浏览器打开 `http://127.0.0.1:8000/?lang=zh`。

```sh
git clone https://github.com/zbw9654250-cmyk/disaster-change-review.git
cd disaster-change-review
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m http.server 8000 --directory docs
```

如果重新生成了案例轮廓，可以运行下面的脚本更新网页数据。

```sh
python scripts/generate_gallery_regions.py --output docs/assets/change_regions.js
```

`docs/assets/baseline_outputs.js` 保存已在 RTX 5090 上运行的 FC-Siam-Diff 和 BIT 轮廓与指标。重新运行深度模型后，可以用相同字段更新这个文件，模型权重仍放在本地或服务器。

## 部署

GitHub Pages 发布 `docs` 目录。仓库已经配置 `.github/workflows/pages.yml`。提交到 `main` 分支后，GitHub Actions 会运行测试并发布网页。

```sh
git add .
git commit -m "update change detection demo"
git push origin main
```

其他静态托管服务也可以直接发布 `docs` 目录。深度模型推理需要 GPU 和 checkpoint，网页本身只展示已经生成的轮廓与指标。

## 数据集构成

| 路径 | 内容 | 用途 |
| --- | --- | --- |
| `docs/assets/geology` | 奥索滑坡、大苏尔滑坡和拉帕尔马火山三组灾前灾后影像 | 地质灾害变化定位和网页案例 |
| `docs/assets/buildings` | 迈克尔飓风厂房和圣罗莎山火住宅两组 xBD 影像 | 整栋建筑轮廓案例 |
| `data/xbd/confirm` | 8 个建筑样本，包含灾前灾后裁剪图、掩膜和损伤等级 | CPU 复核和回归检查 |
| `data/xbd/context-confirm` | 洪水、山火、海啸、飓风和地震场景 | 上下文复核 |
| `data/xbd/stress` | 错位、模糊和外部变化压力样本 | 鲁棒性测试 |
| `data/xbd/library/windows` | 建筑小窗口和检索索引 | 检索和评估 |
| `data/ebenezer` | 航拍屋顶、建筑 footprint、损伤 GeoJSON 和正射图 | 屋顶损伤轮廓模块 |
| `data/roof_candidates` | `strong`、`same` 和 `dual` 三组 GeoJSON 候选层 | 屋顶候选融合模块 |

地质灾害影像来自 NASA Earth Observatory 和 USGS。建筑影像和标注来自 xBD。来源、裁切范围和许可见 [数据说明](docs/DATA-NOTICE.md)、[NOTICE.md](NOTICE.md) 以及各数据目录中的 README。

## 代码模块

| 模块 | 作用 |
| --- | --- |
| [变化区域生成](scripts/generate_gallery_regions.py) | 生成网页使用的 RGB 候选和复核轮廓 |
| [三基线运行器](scripts/run_change_baselines.py) | 统一运行 RGB-rule-v1、FC-Siam-Diff 和 BIT |
| [屋顶损伤定位](modules/roof_candidates/README.md) | 合并分割预测并导出屋顶损伤 GeoJSON |
| [建筑损伤评估](modules/buildings/README.md) | 统计建筑 footprint 内的损伤面积 |
| [局部变化说明](modules/observations/README.md) | 比较两期屋顶影像并输出证据位置和文字说明 |

项目代码采用 [MIT 许可](LICENSE)。公开影像、标注和模型按照各自许可使用。

