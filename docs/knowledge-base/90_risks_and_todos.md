# 风险清单与待办（A 版）

> 本清单只基于“代码 + 核心运行文档”的事实，不引入外部假设。

## 1. 可复现性与依赖风险

1) `requirements.txt` 过于精简：
- 代码显式 import 了 `numpy/pandas/networkx/matplotlib/seaborn/sklearn/yaml` 等，但 requirements 未声明。
- 风险：新环境安装后运行失败（ModuleNotFoundError）。

2) 随机性控制不完全一致：
- `FarmerDataGenerator.__init__` 固定 `np.random.seed(42)`，但其它模块仍会使用 `np.random`（如相变扫描重置采纳者、Logit 的 Gumbel 噪声等）。
- 风险：结果波动较大，影响对比与论文复现。

## 2. 建模一致性风险（以代码为准）

1) `farmer.education_levels` 的概率分布在代码中硬编码 `[0.3,0.4,0.2,0.1]`，不由 config 控制。

2) 网络构建：`build_scale_free_network` 通过双层 for+break 达到“目标边数”，并非严格保证无标度/幂律拟合；
- 风险：在某些参数下网络指标可能不稳定。

3) RL 训练：
- 每个农户一个 DQN（不共享参数），训练成本随 `num_farmers` 增长很快。
- `rl.gamma` 在 config 中存在，但 agent 实际使用个体 `discount_factor`。

## 3. 性能与规模风险

1) `build_scale_free_network` 的两重循环在大规模下会非常慢（近 O(n^2) 距离计算）。
2) 多智能体 DQN：
- 每个 agent 一个 replay buffer + 两个网络，规模大时内存压力显著。

## 4. 代码工程风险

1) 可视化里字体 `SimHei` 在非中文环境可能不可用，导致图表乱码或报错。
2) `pretrainedmodels/` 与 `examples/` 目录看起来是外部模型仓库残留/参考内容，与本项目核心链路无关；
- 风险：读者误解项目边界，建议在知识库中标注“非核心”。

## 5. 建议待办（按优先级）

P0（保证可运行）
- [ ] 补全 `requirements.txt` 与 `setup.py` 的 install_requires（以源码 import 为准）
- [ ] 增加统一的随机种子入口（如在 `run_experiment.py` 开始处调用 `set_random_seed`）

P1（提升可复现与科研可用性）
- [ ] 把 education 的采样概率从硬编码改为 config 字段
- [ ] 把相变扫描、RL 训练的关键随机点记录到 results/summary

P2（性能与扩展）
- [ ] 网络构建改为向量化/采样式连边（避免 O(n^2) 全对计算）
- [ ] RL：考虑参数共享或集中式 critic（如果研究目标允许）
