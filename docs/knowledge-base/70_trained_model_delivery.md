# 70 训练后模型交付说明（DQN 多智能体）

> 目的：把“强化学习最终得到的模型”作为可交付、可复现的研究产物，明确文件位置、加载方法、推理复现与论文引用口径。

---

## 1. 交付产物清单（Artifacts）

### 1.1 训练后模型权重（核心交付物）

- **路径**：`models/agent_0_final.pth`
- **生成方式**：执行强化学习训练（见第 2 节命令）后自动保存
- **内容结构**（PyTorch `torch.save` 字典）：
  - `policy_net`：训练后策略网络参数（用于推理/决策）
  - `target_net`：目标网络参数（训练稳定性辅助）
  - `optimizer`：优化器状态（用于断点续训）
  - `epsilon`：训练结束时的探索率（用于复现实验记录）

> 说明：当前仓库默认保存 **一个代表性智能体（agent_0）** 的模型权重，用于展示训练后的策略网络。训练过程本身是多智能体系统（每个农户可有独立智能体），但为了论文复现与工程交付的简化，保存了一个可加载、可推理的模型文件。

### 1.2 训练过程日志（可复现实验曲线）

- **路径**：`results/rl_training_history.csv`
- **字段**：
  - `episode`：训练轮次
  - `adoption_rates`：该轮 episode 结束时的系统采纳率
  - `avg_rewards`：该轮 episode 内“每步平均奖励”的均值
  - `global_Q`：该轮 episode 结束时的全局耕地质量指标
  - `epsilon`：探索率

### 1.3 训练曲线图（论文可直接引用）

- **路径**：`figures/training_curves.png`
- **生成方式**：训练结束后由 `Visualizer.plot_training_curves(history)` 自动生成

### 1.4 策略可解释性评估输出（辅助交付物）

- **脚本**：`scripts/policy_explainability.py`
- **输出**：
  - `results/policy_explainability.csv`：样本级 state→action→reward 分解
  - `results/policy_explainability_summary.json`：聚合统计（均值/分组/相关性等）

---

## 2. 如何复现训练（生成模型文件）

### 2.1 强化学习训练命令

```bash
python3 run_experiment.py --mode rl --config config.yaml
```

训练完成后，将在以下位置生成/覆盖：
- `models/agent_0_final.pth`
- `results/rl_training_history.csv`
- `figures/training_curves.png`

> 注意：训练耗时与机器性能有关（当前设置 `num_episodes=200`，`max_steps=60`）。

---

## 3. 如何加载模型并进行推理（Inference）

### 3.1 最小加载示例（只验证模型可加载）

```python
import torch
ckpt = torch.load('models/agent_0_final.pth', map_location='cpu')
print(ckpt.keys())
```

应输出类似：`dict_keys(['policy_net', 'target_net', 'optimizer', 'epsilon'])`

### 3.2 用训练后策略网络对状态做动作选择（Q 最大动作）

本项目使用 DQN：给定状态向量 `s`，输出两个动作的 Q 值 `Q(s,0)` 与 `Q(s,1)`，选择 `argmax` 即为决策动作。

- 状态维度：12 维（见论文/实现说明文档）
- 动作空间：2（0=传统施肥，1=绿色施肥）

仓库中已提供可复现推理的脚本：

```bash
python3 scripts/policy_explainability.py --config config.yaml --subsidy 105 --steps 1
```

---

## 4. 如何复现实验“最终指标”（论文引用口径）

### 4.1 Baseline 指标（对照）

- 文件：`results/baseline_summary.json`、`results/baseline_history.csv`
- 典型指标：最终采纳率、最终全局质量、临界补贴（梯度最大点）、逾渗临界补贴等

### 4.2 RL 指标（训练后性能）

- 文件：`results/rl_training_history.csv`
- 推荐引用口径：
  - 以最后一轮 episode（`episode=199`）对应的 `adoption_rates / avg_rewards / global_Q / epsilon` 作为“训练后性能”
  - 同时给出训练曲线图 `figures/training_curves.png` 作为收敛性证据

---

## 5. 论文写作建议（如何表述“最终得到了模型”）

建议在论文中明确区分：

1. **学习产物**：训练得到参数化策略（DQN 的 Q 网络）
   - 形式：`Q_θ(s,a)`（神经网络）
   - 交付：`models/agent_0_final.pth`

2. **有效性证据**：训练曲线收敛 + 与 baseline 对照
   - 训练曲线：`figures/training_curves.png`
   - 量化结果：`results/rl_training_history.csv`

3. **可复现性**：提供命令与脚本复现
   - 训练：`run_experiment.py --mode rl`
   - 推理/解释：`scripts/policy_explainability.py`

---

## 6. 重要注意事项（必读）

- 当前工程为了“交付与论文复现”简化保存了 `agent_0` 的模型文件。
- 如果你需要严格意义上的“每个农户一个独立模型文件”交付（300 个 .pth），需要在训练保存阶段扩展保存逻辑（可后续再做）。
- `policy_explainability.py` 采用“共享策略评估（policy sharing evaluation）”来生成可解释性数据：即用 `agent_0` 的策略网络对所有农户状态进行动作推断。

---

## 7. 快速核验清单（你答辩前 30 秒自检）

- [ ] `models/agent_0_final.pth` 存在
- [ ] `results/rl_training_history.csv` 存在且有 200 行 episode 记录
- [ ] `figures/training_curves.png` 已生成
- [ ] `python3 scripts/policy_explainability.py ...` 可运行并生成 explainability 输出

