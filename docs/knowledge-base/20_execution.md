# 运行与产物（Execution & Outputs）

## 1. 入口与模式

入口脚本：`run_experiment.py`

- baseline：
  ```bash
  python run_experiment.py --mode baseline
  ```
- rl：
  ```bash
  python run_experiment.py --mode rl
  ```
- compare：
  ```bash
  python run_experiment.py --mode compare
  ```
- all：
  ```bash
  python run_experiment.py --mode all
  ```

配置切换：
```bash
python run_experiment.py --config config.yaml --mode baseline
```

## 2. baseline 模式会做什么

对应函数：`Experiment.run_baseline_simulation()`

1) 生成数据：`FarmerDataGenerator.generate_farmer_attributes()`
2) 构建网络：
   - `HyperbolicNetworkBuilder.build_scale_free_network()`
   - `HyperbolicNetworkBuilder.add_family_village_links()`
   - `HyperbolicNetworkBuilder.add_hyperedges()`
3) 动力学仿真：
   - `AdoptionDynamics.step_decision_update(..., use_threshold=False)`（Logit 决策）
   - `AdoptionDynamics.update_land_quality()`（质量演化）
4) 相变分析：
   - `PhaseTransitionAnalyzer.analyze_percolation_threshold(..., use_threshold=True)`（阈值/逾渗判据）
   - `PhaseTransitionAnalyzer.fit_phase_transition_curve()`（Sigmoid）
   - `PhaseTransitionAnalyzer.analyze_network_effect_strength()`（传播速度）
   - `PhaseTransitionAnalyzer.compute_modified_threshold()`（超边修正）
5) 可视化：`Visualizer.*`
6) 结果落盘：CSV/JSON/PNG

## 3. RL 模式会做什么

对应函数：`Experiment.run_rl_training()`

- 固定网络/超边；每个 episode 重采样农户属性与初始状态
- `MultiAgentSystem.step()` 内部流程：
  1) 所有 agent 根据状态选择动作
  2) 环境更新（质量演化 + 采纳率更新）
  3) 计算奖励并写入经验回放
  4) 每步训练
- 每隔 `rl.target_update` episode 同步更新目标网络
- 全体 agent 同步衰减 epsilon
- 保存：
  - `models/agent_0_final.pth`
  - `results/rl_training_history.csv`
  - `figures/training_curves.png`

## 4. 输出目录与关键文件

由 `config.yaml: output` 控制（默认：`./results ./figures ./models ./logs`）。

### results/
- `baseline_history.csv`：baseline 时间序列（采纳率、global_Q 等）
- `baseline_summary.json`：baseline 摘要（含临界补贴、逾渗点、网络指标等）
- `rl_training_history.csv`：RL 训练曲线数据

### figures/
- `network_final_state.png`：网络结构与节点采纳状态
- `degree_distribution.png`：度分布与幂律验证
- `phase_transition.png`：采纳率相变 + 逾渗序参量（巨型连通分量）
- `training_curves.png`：RL 训练曲线
- `diffusion_time.png`：扩散过程曲线

### models/
- `agent_0_final.pth`：代表性智能体的 DQN 参数

## 5. 复现实验的最小建议

- 先跑：`python quick_test.py`
- 再跑：`python run_experiment.py --mode baseline`
- 最后按需跑 RL（耗时显著更长）。
