# 配置参数参考（config.yaml）

> 说明：本文件只对 **A 版范围**（代码可见的字段）做参数释义与影响面梳理。

## 1. network

- `network.num_farmers`：农户数量（规模参数，直接影响耗时与内存）
- `network.avg_degree`：目标平均度（`build_scale_free_network` 以目标边数近似实现）
- `network.heterogeneity`：预留字段（当前代码未直接使用）
- `network.clustering`：预留字段（当前代码未直接使用；聚类来自 `add_family_village_links` 的额外连边）
- `network.hyperedge_ratio`：超边数量比例，`num_hyperedges=int(num_farmers*ratio)`
- `network.gamma`：幂律指数（在 `PhaseTransitionAnalyzer.analyze_network_effect_strength` 用于理论传播速度）

## 2. farmer

- `farmer.economic_mean/std`：经济水平分布参数
- `farmer.education_levels`：教育等级取值集合（实际概率在代码中固定为 `[0.3,0.4,0.2,0.1]`）
- `farmer.risk_tolerance_mean/std`：风险偏好分布
- `farmer.env_awareness_mean/std`：环保意识分布
- `farmer.myopia_range`：短视性 δ 的采样范围；个性化折扣因子 `γ_i = 1/(1+δ_i)`
- `farmer.education_priority_base / political_voice_base`：在 config 中存在，但当前生成逻辑主要由代码按教育/经济/随机项生成

## 3. quality_dynamics（三维土壤质量）

字段为 3 维字典：`fertility / soil_structure / biological_activity`

- `alpha`：绿色施肥对质量提升
- `beta`：传统施肥对质量退化
- `gamma`：自然退化
- `delta`：外部生态修复输入
- `diffusion`：邻居扩散项（network diffusion）

初始：
- `initial_Q`：兼容字段
- `initial_fertility / initial_soil_structure / initial_biological_activity`

合成权重：
- `quality_weights.{fertility,soil_structure,biological_activity}`：综合质量 `land_quality` 与 `global_Q` 的加权

## 4. policy

- `policy.subsidy_base`：baseline 与 RL 默认使用的固定补贴
- `policy.subsidy_range`：相变扫描范围
- `policy.cost_traditional`：传统施肥成本
- `policy.cost_green`：绿色施肥成本
- `policy.training_coverage`：培训覆盖率（影响 `training_access`，进而影响政策激励）

## 5. decision（TPB/Logit/阈值）

- `decision.theta_p0`：政策项基权重（会被 `tanh(mu*global_Q)` 耦合修正）
- `decision.theta_s0`：社会影响项权重
- `decision.theta_e`：成本项权重
- `decision.theta_q`：质量收益项权重
- `decision.mu`：政策-质量耦合强度
- `decision.tau`：Logit 温度（越大越“确定性”）
- `decision.threshold`：阈值判据临界值（相变扫描使用）

价值标定（单位：元）：
- `decision.social_value_base`：社会声誉基准价值
- `decision.quality_value_base`：质量收益基准价值

## 6. rl（DQN 超参）

- `rl.hidden_dim`：Q 网络隐藏层维度
- `rl.learning_rate`
- `rl.gamma`：此字段存在，但 **每个智能体实际使用个体折扣 `discount_factor`**
- `rl.epsilon_start/end/decay`
- `rl.batch_size`
- `rl.memory_size`
- `rl.target_update`：目标网络更新周期（episode 级）

## 7. reward（奖励权重）

- `reward.lambda1`：经济收益
- `reward.lambda2`：政策补贴
- `reward.lambda3`：社会声誉
- `reward.lambda4`：教育优先权收益
- `reward.lambda5`：话语权收益

## 8. simulation

- `simulation.num_episodes`：RL 训练轮数
- `simulation.max_steps`：baseline 时间步 / RL 每 episode 的步数
- `simulation.num_runs`：预留字段（当前入口脚本未直接使用）
- `simulation.save_interval`：预留字段（当前入口脚本未直接使用）

## 9. output

- `output.results_dir`
- `output.figures_dir`
- `output.models_dir`
- `output.logs_dir`
