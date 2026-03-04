# 复杂网络-农户绿色施肥采纳仿真（Hyperbolic Network + TPB + Phase Transition + Multi-Agent DQN）

本仓库提供一个**可复现的端到端仿真框架**，用于研究绿色施肥技术在农户社交网络中的扩散机制，并支持：

- **双曲几何无标度网络**生成（含村内强连边、超边/合作社机制）
- **TPB（计划行为理论）+ Logit** 的微观采纳决策
- **三维耕地质量动力学**（肥力/结构/生物活性）与网络扩散耦合
- **逾渗相变分析**（采纳者子图的巨大连通分量 GCC 作为序参量）与临界补贴识别
- **多智能体 DQN** 学习型策略（在财政约束下跨越“低采纳—低质量锁定”）

> 说明：本仓库为 **轻量代码仓库（A+1）**，不提交 `data/ results/ figures/ models/ logs` 等运行产物。
> 你可以在本地一键生成论文所需图表与结果。

---

## 1. 环境要求

- Python **3.9+**（建议 3.9/3.10）
- macOS / Linux / Windows 均可

---

## 2. 快速开始（推荐）

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate

pip install -r requirements.txt

# 运行基线仿真（现实补贴 config.yaml: policy.subsidy_base）
python3 run_experiment.py --mode baseline
```

运行后会在本地生成（默认）：
- `data/`：农户属性与网络文件
- `results/`：过程数据与摘要
- `figures/`：基础图表
- `models/`：RL 权重（如运行 rl/compare）
- `logs/`：日志

这些目录已在 `.gitignore` 中忽略，不会污染 GitHub 仓库。

---

## 3. 运行模式

统一入口脚本：`run_experiment.py`

### 3.1 基线仿真（baseline）

```bash
python3 run_experiment.py --mode baseline
```

### 3.2 强化学习训练（rl）

```bash
python3 run_experiment.py --mode rl
```

### 3.3 对比分析（compare）

```bash
python3 run_experiment.py --mode compare
```

> 提示：`compare` 依赖 baseline 与 rl 的产物文件；如未生成，请先分别运行。

---

## 4. 生成顶刊风格图表（可选）

```bash
python3 scripts/export_journal_figures.py
```

---

## 5. 参数配置

所有参数统一在 `config.yaml` 中管理，关键字段：
- `network.*`：网络规模、平均度、超边比例等
- `farmer.*`：异质性分布参数
- `quality_dynamics.*`：三维质量动力学
- `policy.*`：补贴与成本（现实量纲）
- `decision.*`：TPB/Logit 权重与温度
- `rl.*`：DQN 超参
- `simulation.*`：训练轮数/步数
- `output.*`：输出目录（默认会生成在项目根目录下）

更详细释义见：`docs/knowledge-base/30_config_reference.md`。

---

## 6. 仓库结构

```
.
├── config.yaml
├── requirements.txt
├── run_experiment.py
├── src/                  # 核心实现
├── scripts/              # 出图/可解释性/数据导出等脚本
├── docs/                 # 知识库与实现说明
```

---

## 7. 可复现性说明

- 仓库已统一入口：`run_experiment.py`
- 随机种子：数据生成模块默认 `np.random.seed(42)`（见 `src/data_generator.py`）
- 运行产物默认被 `.gitignore` 忽略，可在本地复现生成

