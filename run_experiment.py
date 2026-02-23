"""
主实验运行脚本
"""
import numpy as np
import yaml
import os
import json
from tqdm import tqdm
import argparse

from src.data_generator import FarmerDataGenerator, load_config
from src.network_builder import HyperbolicNetworkBuilder
from src.dynamics import AdoptionDynamics
from src.rl_agent import MultiAgentSystem
from src.phase_transition import PhaseTransitionAnalyzer
from src.visualization import Visualizer


class Experiment:
    """实验管理器"""
    
    def __init__(self, config_path: str = 'config.yaml'):
        self.config = load_config(config_path)
        self.setup_directories()
        
    def setup_directories(self):
        """创建输出目录"""
        for key in ['results_dir', 'figures_dir', 'models_dir', 'logs_dir']:
            path = self.config['output'][key]
            os.makedirs(path, exist_ok=True)
        os.makedirs('./data', exist_ok=True)
    
    def run_baseline_simulation(self):
        """
        运行基线仿真 (无强化学习，仅动力学演化)
        """
        print("\n" + "="*60)
        print("基线仿真：动力学演化 + TPB决策")
        print("="*60)
        
        # 1. 生成数据
        print("\n[1/5] 生成农户数据...")
        generator = FarmerDataGenerator(self.config)
        farmer_df = generator.generate_farmer_attributes()
        generator.save_data(farmer_df)
        
        # 2. 构建网络
        print("\n[2/5] 构建复杂网络...")
        builder = HyperbolicNetworkBuilder(self.config, farmer_df)
        G = builder.build_scale_free_network()
        builder.add_family_village_links(G)
        hyperedges = builder.add_hyperedges(G)
        builder.save_network(G, hyperedges)
        
        metrics = builder.compute_network_metrics(G)
        print("\n网络指标:")
        for k, v in metrics.items():
            print(f"  {k}: {v}")
        
        # 3. 动力学仿真
        print("\n[3/5] 运行动力学仿真...")
        dynamics = AdoptionDynamics(self.config, G, farmer_df, hyperedges)
        
        history = {
            'time': [],
            'adoption_rate': [],
            'global_Q': [],
            'mean_land_quality': []
        }
        
        num_steps = self.config['simulation']['max_steps']
        subsidy = self.config['policy']['subsidy_base']
        
        for t in tqdm(range(num_steps), desc="Simulating"):
            dynamics.step_decision_update(subsidy, use_threshold=False)
            dynamics.update_land_quality(dt=1.0)
            
            state = dynamics.get_system_state()
            history['time'].append(t)
            history['adoption_rate'].append(state['adoption_rate'])
            history['global_Q'].append(state['global_Q'])
            history['mean_land_quality'].append(state['mean_land_quality'])
        
        print(f"\n最终采纳率: {history['adoption_rate'][-1]:.2%}")
        print(f"最终全局质量: {history['global_Q'][-1]:.3f}")
        
        # 保存结果
        import pandas as pd
        df_history = pd.DataFrame(history)
        df_history.to_csv(f"{self.config['output']['results_dir']}/baseline_history.csv", index=False)
        
        # 4. 相变分析
        print("\n[4/5] 相变与临界阈值分析...")
        analyzer = PhaseTransitionAnalyzer(self.config)
        
        # 相变扫描分辨率：现实校准场景下，将扫描点数提高以获得更平滑的相变曲线与可拟合的 Sigmoid 参数
        subsidy_range = np.linspace(
            self.config['policy']['subsidy_range'][0],
            self.config['policy']['subsidy_range'][1],
            101
        )
        
        # 重新初始化dynamics用于相变分析
        farmer_df_phase = generator.generate_farmer_attributes()
        dynamics_phase = AdoptionDynamics(self.config, G, farmer_df_phase, hyperedges)
        
        phase_result = analyzer.analyze_percolation_threshold(dynamics_phase, subsidy_range)
        fit_result = analyzer.fit_phase_transition_curve(
            phase_result['subsidy_values'],
            phase_result['adoption_rates']
        )
        
        # 网络传播分析
        farmer_df_network = generator.generate_farmer_attributes()
        dynamics_network = AdoptionDynamics(self.config, G, farmer_df_network, hyperedges)
        network_result = analyzer.analyze_network_effect_strength(G, dynamics_network)
        
        # 修正阈值
        theta_modified = analyzer.compute_modified_threshold(dynamics, hyperedges)
        
        # 5. 可视化
        print("\n[5/5] 生成可视化图表...")
        vis = Visualizer(self.config['output']['figures_dir'])
        
        vis.plot_network(G, farmer_df, save_name='network_final_state')
        vis.plot_degree_distribution(G)
        vis.plot_phase_transition(phase_result, fit_result)
        vis.plot_betweenness_vs_response(G, farmer_df)
        vis.plot_diffusion_over_time(network_result['rates_over_time'])
        
        # 保存配置和结果摘要
        # 转换所有NumPy类型为Python原生类型
        def convert_to_json_serializable(obj):
            """递归转换NumPy类型为Python原生类型"""
            import numpy as np
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_to_json_serializable(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_json_serializable(item) for item in obj]
            else:
                return obj
        
        results_summary = {
            'config': convert_to_json_serializable(self.config),
            'network_metrics': convert_to_json_serializable(metrics),
            'final_adoption_rate': float(history['adoption_rate'][-1]),
            'final_global_Q': float(history['global_Q'][-1]),
            'critical_subsidy': float(phase_result['critical_subsidy']),
            'critical_threshold': float(phase_result['critical_threshold']),
            'theta_modified': float(theta_modified),
            # 逾渗相变结果（新增）
            'percolation_subsidy': float(phase_result.get('percolation_subsidy', phase_result['critical_subsidy'])),
            'percolation_threshold': float(phase_result.get('percolation_threshold', 0.0)),
            'giant_component_sizes': convert_to_json_serializable(phase_result.get('giant_component_sizes', [])),
            'global_qualities': convert_to_json_serializable(phase_result.get('global_qualities', []))
        }
        
        with open(f"{self.config['output']['results_dir']}/baseline_summary.json", 'w') as f:
            json.dump(results_summary, f, indent=4)
        
        print("\n[OK] 基线仿真完成！结果已保存至:", self.config['output']['results_dir'])
        
        return results_summary
    
    def run_rl_training(self):
        """
        运行强化学习训练
        """
        print("\n" + "="*60)
        print("强化学习训练：DQN多智能体优化")
        print("="*60)
        
        # 1. 准备环境
        print("\n[1/4] 准备环境...")
        generator = FarmerDataGenerator(self.config)
        farmer_df = generator.generate_farmer_attributes()
        
        builder = HyperbolicNetworkBuilder(self.config, farmer_df)
        G = builder.build_scale_free_network()
        builder.add_family_village_links(G)
        hyperedges = builder.add_hyperedges(G)
        
        dynamics = AdoptionDynamics(self.config, G, farmer_df, hyperedges)
        
        # 2. 创建多智能体系统
        print("\n[2/4] 初始化多智能体系统...")
        mas = MultiAgentSystem(self.config, dynamics, G)
        
        # 3. 训练
        print("\n[3/4] 开始强化学习训练...")
        num_episodes = self.config['simulation']['num_episodes']
        max_steps = self.config['simulation']['max_steps']
        target_update = self.config['rl']['target_update']
        
        history = {
            'episode': [],
            'adoption_rates': [],
            'avg_rewards': [],
            'global_Q': [],
            'epsilon': []
        }
        
        # 使用固定补贴（与Baseline相同），确保公平对比
        subsidy = self.config['policy']['subsidy_base']  # 固定 = 1000元
        
        for episode in tqdm(range(num_episodes), desc="Training Episodes"):
            # 重置环境
            farmer_df = generator.generate_farmer_attributes()
            dynamics = AdoptionDynamics(self.config, G, farmer_df, hyperedges)
            mas.dynamics = dynamics
            
            episode_rewards = []
            # 所有episode使用相同补贴（与Baseline一致）
            
            for step in range(max_steps):
                avg_reward = mas.step(subsidy, training=True)
                episode_rewards.append(avg_reward)
            
            # 更新目标网络
            if episode % target_update == 0:
                mas.update_all_target_networks()
            
            # 衰减探索率
            mas.decay_all_epsilon()
            
            # 记录
            state = dynamics.get_system_state()
            history['episode'].append(episode)
            history['adoption_rates'].append(state['adoption_rate'])
            history['avg_rewards'].append(np.mean(episode_rewards))
            history['global_Q'].append(state['global_Q'])
            history['epsilon'].append(mas.agents[0].epsilon)
            
            if episode % 20 == 0:
                print(f"\nEpisode {episode}: "
                      f"采纳率={state['adoption_rate']:.2%}, "
                      f"平均奖励={np.mean(episode_rewards):.3f}, "
                      f"ε={mas.agents[0].epsilon:.3f}")
        
        # 4. 保存模型和结果
        print("\n[4/4] 保存模型和结果...")
        
        # 保存一个代表性智能体的模型
        models_dir = self.config['output']['models_dir']
        mas.agents[0].save_model(f"{models_dir}/agent_0_final.pth")
        
        # 保存训练历史
        import pandas as pd
        df_history = pd.DataFrame(history)
        df_history.to_csv(f"{self.config['output']['results_dir']}/rl_training_history.csv", index=False)
        
        # 可视化训练曲线
        vis = Visualizer(self.config['output']['figures_dir'])
        vis.plot_training_curves(history)
        
        print("\n[OK] 强化学习训练完成！")
        
        return history
    
    def run_comparative_analysis(self):
        """
        对比分析：基线 vs 强化学习
        """
        print("\n" + "="*60)
        print("对比分析：基线方法 vs 强化学习优化")
        print("="*60)
        
        # 加载结果
        import pandas as pd
        
        baseline_history = pd.read_csv(f"{self.config['output']['results_dir']}/baseline_history.csv")
        rl_history = pd.read_csv(f"{self.config['output']['results_dir']}/rl_training_history.csv")
        
        # 对比可视化
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 采纳率对比
        axes[0].plot(baseline_history['time'], baseline_history['adoption_rate'], 
                     label='Baseline (TPB)', linewidth=2, color='blue')
        axes[0].plot(rl_history['episode'], rl_history['adoption_rates'], 
                     label='RL-optimized (DQN)', linewidth=2, color='red')
        axes[0].set_xlabel('Time/Episode', fontsize=12)
        axes[0].set_ylabel('Adoption Rate', fontsize=12)
        axes[0].set_title('Adoption Rate Comparison', fontsize=13)
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 质量对比
        axes[1].plot(baseline_history['time'], baseline_history['global_Q'], 
                     label='Baseline', linewidth=2, color='blue')
        axes[1].plot(rl_history['episode'], rl_history['global_Q'], 
                     label='RL-optimized', linewidth=2, color='red')
        axes[1].set_xlabel('Time/Episode', fontsize=12)
        axes[1].set_ylabel('Global Land Quality Q(t)', fontsize=12)
        axes[1].set_title('Land Quality Comparison', fontsize=13)
        axes[1].legend()
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f"{self.config['output']['figures_dir']}/comparison.png", dpi=150)
        plt.close()
        
        print(f"\n[OK] 对比分析完成！图表已保存")
        print(f"\n最终采纳率:")
        print(f"  基线方法: {baseline_history['adoption_rate'].iloc[-1]:.2%}")
        print(f"  强化学习: {rl_history['adoption_rates'].iloc[-1]:.2%}")


def main():
    parser = argparse.ArgumentParser(description='复杂网络农户采纳行为模型')
    parser.add_argument('--mode', type=str, default='all', 
                        choices=['baseline', 'rl', 'compare', 'all'],
                        help='运行模式: baseline(基线), rl(强化学习), compare(对比), all(全部)')
    parser.add_argument('--config', type=str, default='config.yaml',
                        help='配置文件路径')
    
    args = parser.parse_args()
    
    exp = Experiment(args.config)
    
    if args.mode in ['baseline', 'all']:
        exp.run_baseline_simulation()
    
    if args.mode in ['rl', 'all']:
        exp.run_rl_training()
    
    if args.mode in ['compare', 'all']:
        exp.run_comparative_analysis()
    
    print("\n" + "="*60)
    print("所有实验完成！")
    print("="*60)


if __name__ == '__main__':
    main()

