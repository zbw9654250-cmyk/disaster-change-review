# xBD 建筑数据

该目录使用 Ritwik Gupta 等发布的 xBD / xView2 真实卫星 RGB 与建筑多边形。影像来自 Maxar / DigitalGlobe Open Data Program。裁图、掩膜、可视化与受控编辑是本项目的派生处理。本仓库随数据保留 CC BY-NC-SA 4.0 署名，底层影像保留原始权利与适用的非商业使用条件。[原研究](https://arxiv.org/abs/1911.09296) · [xView2 项目](https://www.sei.cmu.edu/projects/xview-2-challenge/) · [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/)

| 目录 | 独立来源 | 构造和用途 |
| --- | --- | --- |
| `library/` | 正式训练集 36 栋、23 个图块、10 个事件，四档各 9 栋 | 36 条双期、12 条单期、12 条完全同图、12 条 JPEG 重编码，共 72 条案例和 132 张局部参考窗。来源笔记属 AI 读图弱监督。 |
| `panel/`、`confirm/` | 正式测试集 20 栋、20 个图块 | 从 1024×1024 原图裁取并缩放为 336×336；足迹按各期官方多边形独立生成。首批 12 栋、5 个事件；确认批 8 栋、另外 4 个事件。每栋 3 个说明版本，由两名 AI 读者独立匿名审核。 |
| `stress/` | 复用首批中的 8 栋 | 每栋构造同图、仅建筑外变化、平移加模糊、仅足迹内编辑，共 32 对。有编辑位置掩膜和质心。 |
| `context-confirm/` | 独立新增 8 栋、8 图块、8 事件 | 各取真实灾后单图。实验脚本从中生成 11 种有真值的光照或局部干预，合计 88 对。 |

所有运行清单都以清单所在目录为相对路径基准。真实测试照片与训练库、历史测试数据按栋、原图块和空间邻近关系排除。官方四档标签用于分层取样与整栋评级评分。匿名读图结果衡量中文观察的可核实程度。案例库、测试分区中的原始照片和标注均可按固定提交追溯。[训练镜像](https://huggingface.co/datasets/aryananand/xBD/tree/b98724026e844e1fccd879c95e9f09f03c56e6f8) · [测试镜像](https://huggingface.co/datasets/ziruihan/xbd_test/tree/361e53f86506e1f221f42a0c0d9619c213220ae5/test) · [分组核查](prepare/cohort-verification.json) · [额外 8 栋的源文件哈希](context-confirm/source-hashes.json)
