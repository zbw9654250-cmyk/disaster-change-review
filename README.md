# 灾变影像变化定位与建筑损伤复核

[English](README.en.md)

项目接收同一地点的灾前和灾后 RGB 影像，输出变化候选、受灾区域轮廓和建筑损伤复核结果。网页示例把灾前影像、灾后基线和灾后改进结果放在同一行，方便检查覆盖范围和轮廓位置。

[打开在线演示](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh)

## 三条基线

项目固定比较三种变化定位方法。三种方法都接收同一地点、同一尺寸的灾前和灾后 RGB 影像，输出变化区域。当前网页实际绘制的是第一条基线，另外两条通过可选脚本运行。

| 基线 | 方法 | 输出 | 用途 |
| --- | --- | --- | --- |
| RGB-rule-v1 | 颜色、局部纹理和亮度差异，配合连通区域筛选 | 椭圆候选区域 | CPU 可运行、可解释的现有基线 |
| FC-Siam-Diff | 共享权重的双时相 Siamese 编码器和差分解码器 | 二值变化掩膜 | 正式深度学习基线 |
| BIT | 双时相 CNN、语义 token 和 Transformer | 二值变化掩膜 | 全局变化建模基线 |

网页中的橙色虚线表示 RGB-rule-v1。FC-Siam-Diff 和 BIT 使用 [Open-CD](https://github.com/likyoo/open-cd) / [Open-CD Lite](https://github.com/taktpixel/opencd-lite) 的公开实现和 LEVIR-CD 权重入口。权重属于上游项目，不能直接当作本项目灾损精度结果。当前数据中的 xBD footprint 是建筑范围标注，不是像素级受灾掩膜，因此项目不会用它们虚构 FC-Siam-Diff 或 BIT 的像素 IoU。

运行统一输出脚本：

```sh
python scripts/run_change_baselines.py \
  --model rgb \
  --before docs/assets/geology/volcano/la-palma-before.png \
  --after docs/assets/geology/volcano/la-palma-after.png \
  --output artifacts/baselines/la-palma/rgb
```

脚本会写出 `mask.png`、`overlay.png`、`regions.geojson` 和 `metrics.json`。FC-Siam-Diff 或 BIT 需要先安装可选依赖并提供对应 checkpoint：

```sh
python -m pip install "opencd-lite[torch]"
python scripts/run_change_baselines.py --model fc_siam_diff \
  --before BEFORE.png --after AFTER.png --checkpoint fc_siam_diff.pth \
  --output artifacts/baselines/example/fc_siam_diff --device cuda
```

三条基线的统一评测应报告变化区域 IoU、Precision、Recall、F1、建筑 footprint 覆盖率、漏检率、p50/p95 推理时间和显存占用。四档建筑损伤等级需要单独使用 xView2 两阶段定位与分类基线，不能由二值变化模型直接代替。

## 改进结果是什么

改进结果增加了像素变化掩膜和轮廓矢量化步骤，并针对建筑案例加入完整建筑范围约束。

- 地质灾害影像使用亮度、色度和灾前后差异生成连续变化掩膜，再用形态学处理和 `find_contours` 沿变化边缘生成绿色闭合轮廓。
- 建筑影像使用公开 xBD `destroyed` 建筑 footprint 约束受灾建筑范围，绿色轮廓覆盖完整厂房或住宅，便于检查基线候选是否漏掉屋顶区域。

改进结果和基线使用同一张灾后影像。网页中绿色轮廓表示改进结果，轮廓来源和数据许可写在 [数据说明](docs/DATA-NOTICE.md) 中。

## 展示实例

默认展示三个案例。

| 案例 | 影像类型 | 网页中的输出 |
| --- | --- | --- |
| 拉帕尔马火山 | Landsat 8 灾前灾后影像 | 主要熔岩变化区的像素轮廓 |
| 迈克尔飓风 | xBD 厂房灾前灾后影像 | 完整受灾建筑 footprint 轮廓 |
| 圣罗莎山火 | xBD 住宅灾前灾后影像 | 完整受灾建筑 footprint 轮廓 |

[查看三个实例的对比结果](https://zbw9654250-cmyk.github.io/disaster-change-review/?lang=zh)

## 本地运行网页

项目网页是静态文件，不需要后端服务或 GPU。下面的命令适用于 Windows PowerShell，也适用于安装了 Python 3.12 的其他系统。

```sh
git clone https://github.com/zbw9654250-cmyk/disaster-change-review.git
cd disaster-change-review
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_gallery_regions.py --output docs/assets/change_regions.js
python -m http.server 8000 --directory docs
```

打开 `http://127.0.0.1:8000/?lang=zh` 查看网页。`generate_gallery_regions.py` 会从仓库中的灾前灾后影像重新生成候选和轮廓文件。

## 本地运行建筑影像示例

下面的命令在 CPU 上处理 8 个建筑样本，并输出每栋建筑的变化说明和对应位置。

```sh
python -m pip install -r modules/observations/requirements.txt
python modules/observations/run_roofs.py --cases data/xbd/confirm/cases.jsonl --output observations.jsonl
```

结果写入 `observations.jsonl`。示例输出见 [confirm-measure.jsonl](results/observations/out/confirm-measure.jsonl)。

## 实际部署

项目使用 GitHub Pages 发布 `docs` 目录。仓库已经配置 `.github/workflows/pages.yml`，将代码推送到 `main` 分支后会自动运行测试并发布网页。

```sh
git add .
git commit -m "update demo"
git push origin main
```

首次在其他仓库使用时，在 GitHub 的 `Settings`、`Pages`、`Build and deployment` 中把来源设为 `GitHub Actions`。部署完成后，Pages 页面会显示访问地址。项目也可以直接把 `docs` 目录上传到其他静态网站托管服务。

## 数据集构成

| 数据 | 内容 | 用途 |
| --- | --- | --- |
| `docs/assets/geology` | 3 组地质灾害灾前灾后图像，包括奥索滑坡、大苏尔滑坡和拉帕尔马火山 | 变化检测和网页展示 |
| `docs/assets/buildings` | 2 组 xBD 建筑灾前灾后图像，包括迈克尔飓风厂房和圣罗莎山火住宅 | 整栋建筑轮廓展示 |
| `data/xbd/confirm` | 8 个建筑样本，共 8 对灾前灾后裁剪图和 16 张掩膜，配套损伤等级，覆盖飓风、山火和不同损伤等级 | CPU 复核示例和回归检查 |
| `data/xbd/context-confirm` | 8 个跨灾种场景，包含洪水、山火、海啸、飓风和地震图像及掩膜 | 上下文复核 |
| `data/xbd/stress` | 32 个压力样本，包含 64 张成对图像、掩膜和参考变化图 | 错位、模糊和外部变化测试 |
| `data/xbd/library/windows` | 132 个建筑小窗口及检索索引 | 检索和评估 |
| `data/ebenezer` | 8 张航拍屋面图、建筑 footprint、损伤 GeoJSON 和正射图 | 屋面损伤轮廓模块 |
| `data/roof_candidates` | `strong`、`same`、`dual` 三组 GeoJSON 候选层 | 屋面候选融合模块 |

网页展示使用的地质灾害影像来自 NASA Earth Observatory 和 USGS，建筑影像及标注来自 xBD。各数据集的来源、裁切范围和许可见 [数据说明](docs/DATA-NOTICE.md)、[NOTICE.md](NOTICE.md) 和各数据目录中的 README。

## 代码模块

| 模块 | 作用 |
| --- | --- |
| [变化区域生成](scripts/generate_gallery_regions.py) | 生成网页使用的基线候选和改进轮廓 |
| [三基线运行器](scripts/run_change_baselines.py) | 统一运行 RGB-rule-v1、FC-Siam-Diff 和 BIT，并导出掩膜与指标 |
| [屋面损伤定位](modules/roof_candidates/README.md) | 合并多组分割预测并导出屋面损伤 GeoJSON |
| [逐栋损伤评估](modules/buildings/README.md) | 在建筑 footprint 内统计损伤面积 |
| [局部变化说明](modules/observations/README.md) | 比较两期屋面影像并输出证据位置和文字说明 |

项目代码采用 [MIT 许可](LICENSE)。公开影像、标注和模型按照各自许可使用。

