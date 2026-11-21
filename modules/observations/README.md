# 双期建筑外观解释

输入 UTF-8 JSONL 清单，每栋一行。必需字段为唯一 `building_id`、灾后 RGB `image_path` 与同尺寸足迹 `mask_path`。双期时再给灾前的 `pre_image_path`、`pre_mask_path`。图片路径相对清单所在目录。掩膜前景取 255。可提供有效像素掩膜与覆盖率；检索排除同栋或邻近案例还使用 `tile`、`bbox_lonlat` 和来源 UID 或建筑 ID。

默认程序在 CPU 上对齐两期建筑占区，按三个尺度选取局部并保存两期归一化坐标。在共同有效像素内计算中位 RGB、亮度、分位数和空间反差，由固定判据形成中文观察。单期输入只描述可见外观。`changed` 表示目标窗像素外观有别，整栋灾损程度另由评级模块提供。

以下命令均从仓库根目录执行。输出使用新文件名。

```sh
python -m pip install -r modules/observations/requirements.txt
python modules/observations/run_roofs.py --cases data/xbd/confirm/cases.jsonl --output observations.jsonl
python modules/observations/compare_context.py --cases data/xbd/context-confirm/cases.jsonl --output context-check.json
```

第二条推理命令以 8 栋新增母图各生成 11 对受控数据，重新计算线性与非线性光照校正的 88 对结果。实际观测可加 `--photometric-context`。该功能需要两期共同像素格、已知配准误差至多 1 像素、覆盖率各至少 0.98，且具备原始有效像素掩膜。条件充分时返回同址选区与周边颜色映射是否一致，以及建筑中仍有残差的独立复查框。证据不足时记录具体原因。

## 可选的图像语言核验

另准备 GPU、本地 Qwen3-VL-4B-Instruct、匹配 CUDA 的 torch、torchvision、Transformers 和 accelerate，实测模型环境为 PyTorch 2.8 与 Transformers 5.18。用 `--mode verify` 运行：

```sh
python modules/observations/run_roofs.py --mode verify --cases data/xbd/confirm/cases.jsonl --output verified.jsonl --model /models/Qwen3-VL-4B-Instruct --library data/xbd/library/index.json --cards data/xbd/library/grounded_cases.json
```

视觉案例库提供“复查哪类属性”。模型观察本栋的灾前/灾后整栋与局部，从实测候选事实中选取观察。模型失败或没选中合格事实时使用测量结果。供人阅读的字段为 `explanation_zh`，`evidence_region` 给出两期的证据位置，`measurement`、`render_mode`、`selected_fact_ids`、`raw_verification` 可追溯输出来源。20 栋真实双期建筑的两位 AI 读者对照中，旧自由生成的视觉 RAG 有 1 栋通过，纯测量与加 Qwen 核验均为 20 栋通过。该终点评估外观解释的可复核性。

## 挂接整栋评级

```sh
python modules/observations/attach_observations.py --cases building-inputs/cases.jsonl --grades grades.jsonl --candidates observations.jsonl --output building-observations.jsonl
```

挂接按建筑 ID 和源图 SHA-256 验证，成功后原等级旁新增 `regional_observation`。质量记录不满足时保留原因。完整的测量、模型选择和光照校正详情留在原始观察 JSONL。准备实际输入见 [逐栋评级程序](../buildings/README.md)。公开影像及案例笔记来源于 xBD，使用与署名条款见 [xBD 数据说明](../../data/xbd/README.md)。[视觉事实核验思路](https://github.com/VITA-MLLM/Woodpecker) · [周边颜色归一化参考](https://github.com/planetlabs/radiometric_normalization)
