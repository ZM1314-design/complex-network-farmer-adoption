# 核心符号表（类/函数索引）

> 目标：把“该看什么”变成可索引清单，并把符号定位到具体文件。

## 1. 入口

- `run_experiment.py`
  - `Experiment`
    - `__init__(config_path)`
    - `setup_directories()`
    - `run_baseline_simulation()`
    - `run_rl_training()`
    - `run_comparative_analysis()`
  - `main()`

## 2. 数据生成

- `src/data_generator.py`
  - `FarmerDataGenerator`
    - `generate_farmer_attributes()`
    - `generate_social_network_data()`（预留）
    - `save_data(farmer_df, output_path='./data')`
  - `load_config(config_path='config.yaml')`

## 3. 网络构建

- `src/network_builder.py`
  - `HyperbolicNetworkBuilder`
    - `compute_hyperbolic_distance(i, j)`
    - `connection_probability(distance)`
    - `build_scale_free_network()`
    - `add_hyperedges(G)`
    - `add_family_village_links(G)`
    - `compute_network_metrics(G)`
    - `save_network(G, hyperedges, output_path='./data')`

## 4. 动力学与决策

- `src/dynamics.py`
  - `AdoptionDynamics`
    - `update_land_quality(dt=1.0)`
    - `compute_social_influence(farmer_id)`
    - `compute_policy_incentive(farmer_id, subsidy)`
    - `compute_utility_tpb(farmer_id, action, subsidy)`
    - `logit_adoption_probability(farmer_id, subsidy)`
    - `percolation_threshold_check(farmer_id, subsidy)`
    - `step_decision_update(subsidy, use_threshold=False)`
    - `_update_policy_incentives()`
    - `get_system_state()`

## 5. 强化学习

- `src/rl_agent.py`
  - `DQNetwork(nn.Module)`
  - `ReplayBuffer`
  - `FarmerAgent`
    - `get_state_vector(dynamics, G, global_Q)`
    - `select_action(state, training=True)`
    - `compute_reward(action, dynamics, subsidy)`
    - `store_transition(...)`
    - `train_step()`
    - `update_target_network()`
    - `decay_epsilon()`
    - `save_model(path)` / `load_model(path)`
  - `MultiAgentSystem`
    - `step(subsidy, training=True)`
    - `update_all_target_networks()`
    - `decay_all_epsilon()`

## 6. 相变与网络传播

- `src/phase_transition.py`
  - `PhaseTransitionAnalyzer`
    - `compute_giant_component_size(G, adoption_states)`
    - `analyze_percolation_threshold(dynamics, subsidy_range)`
    - `analyze_network_effect_strength(G, dynamics)`
    - `compute_modified_threshold(dynamics, hyperedges)`
    - `fit_phase_transition_curve(subsidy_values, adoption_rates)`

## 7. 可视化

- `src/visualization.py`
  - `Visualizer`
    - `plot_network(G, farmer_df, save_name='network')`
    - `plot_degree_distribution(G, save_name='degree_distribution')`
    - `plot_phase_transition(result, fit_result=None, save_name='phase_transition')`
    - `plot_training_curves(history, save_name='training_curves')`
    - `plot_quality_3d_evolution(quality_history, save_name='quality_3d_evolution')`
    - `plot_betweenness_vs_response(G, farmer_df, save_name='betweenness_response')`
    - `plot_diffusion_over_time(rates_over_time, save_name='diffusion_time')`

## 8. 工具

- `src/utils.py`
  - I/O：`save_json/load_json/save_pickle/load_pickle/load_yaml/save_yaml`
  - `set_random_seed(seed=42)`
  - `compute_statistics(data)`
  - `moving_average(data, window=10)`
  - `normalize_data(data, method='minmax')`
  - `create_experiment_summary(config, results, output_path)`
  - `compare_experiments(exp_paths, output_path)`
  - `plot_comparison(df, metrics, output_path)`
