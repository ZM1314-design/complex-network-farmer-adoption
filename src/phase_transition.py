"""
相变与临界阈值分析模块
"""
import numpy as np
import networkx as nx
from typing import Dict, List, Tuple
from scipy.optimize import curve_fit


class PhaseTransitionAnalyzer:
    """相变分析器"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def compute_giant_component_size(self, G: nx.Graph, adoption_states: np.ndarray) -> float:
        """
        计算采纳者子图中的巨大连通分量大小（序参数）
        
        Args:
            G: 完整网络
            adoption_states: 农户采纳状态数组
            
        Returns:
            巨大连通分量相对大小（0-1之间）
        """
        # 构建采纳者子图（只包含采纳绿色施肥的农户）
        adopters = np.where(adoption_states == 1)[0]
        
        if len(adopters) == 0:
            return 0.0
        
        # 创建采纳者子图
        G_adopters = G.subgraph(adopters).copy()
        
        if G_adopters.number_of_nodes() == 0:
            return 0.0
        
        # 计算所有连通分量
        connected_components = list(nx.connected_components(G_adopters))
        
        if len(connected_components) == 0:
            return 0.0
        
        # 找到最大连通分量（巨大连通分量）
        giant_component = max(connected_components, key=len)
        giant_size = len(giant_component)
        
        # 相对大小（相对于总农户数）
        total_farmers = len(adoption_states)
        giant_component_ratio = giant_size / total_farmers
        
        return giant_component_ratio
    
    def analyze_percolation_threshold(
        self, 
        dynamics,
        subsidy_range: np.ndarray
    ) -> Dict:
        """
        分析临界阈值 Θ_c（包含逾渗相变分析）
        
        通过扫描补贴强度，找到采纳率突变点和巨大连通分量出现点
        
        Returns:
            Dict: {
                'subsidy_values': 补贴值数组,
                'adoption_rates': 对应的采纳率,
                'giant_component_sizes': 巨大连通分量大小（序参数）,
                'critical_threshold': 临界阈值,
                'critical_subsidy': 临界补贴强度,
                'percolation_subsidy': 逾渗临界补贴（巨大连通分量出现点）
            }
        """
        adoption_rates = []
        giant_component_sizes = []
        global_qualities = []
        
        print("\n=== 相变分析：扫描补贴强度（包含逾渗相变） ===")
        
        for subsidy in subsidy_range:
            # 重置系统到初始状态
            dynamics.farmer_df['adoption_state'] = 0
            initial_adopters = np.random.choice(
                len(dynamics.farmer_df),
                size=int(len(dynamics.farmer_df) * 0.05),
                replace=False
            )
            dynamics.farmer_df.loc[initial_adopters, 'adoption_state'] = 1
            
            # 运行到收敛
            for _ in range(50):
                dynamics.step_decision_update(subsidy, use_threshold=True)
                dynamics.update_land_quality(dt=1.0)
            
            final_rate = dynamics.adoption_rate
            adoption_rates.append(final_rate)
            
            # 计算巨大连通分量大小（序参数）
            adoption_states = dynamics.farmer_df['adoption_state'].values
            giant_size = self.compute_giant_component_size(dynamics.G, adoption_states)
            giant_component_sizes.append(giant_size)
            
            # 记录全局质量
            global_qualities.append(dynamics.global_Q)
            
            print(f"  补贴={subsidy:.0f}, 采纳率={final_rate:.2%}, 巨大连通分量={giant_size:.2%}, 全局质量={dynamics.global_Q:.3f}")
        
        adoption_rates = np.array(adoption_rates)
        giant_component_sizes = np.array(giant_component_sizes)
        global_qualities = np.array(global_qualities)
        
        # 寻找采纳率临界点：梯度最大处
        gradient_adoption = np.gradient(adoption_rates)
        critical_idx = np.argmax(gradient_adoption)
        critical_subsidy = subsidy_range[critical_idx]
        critical_threshold = adoption_rates[critical_idx]
        
        # 寻找逾渗临界点：巨大连通分量突然出现的地方
        # 定义为巨大连通分量大小从接近0突然跳到显著值的位置
        gradient_giant = np.gradient(giant_component_sizes)
        percolation_idx = np.argmax(gradient_giant)
        percolation_subsidy = subsidy_range[percolation_idx]
        percolation_threshold = giant_component_sizes[percolation_idx]
        
        print(f"\n[OK] 采纳率临界补贴强度: {critical_subsidy:.0f}")
        print(f"[OK] 采纳率临界阈值: {critical_threshold:.2%}")
        print(f"[OK] 逾渗临界补贴强度: {percolation_subsidy:.0f}")
        print(f"[OK] 逾渗临界巨大连通分量: {percolation_threshold:.2%}")
        
        return {
            'subsidy_values': subsidy_range,
            'adoption_rates': adoption_rates,
            'giant_component_sizes': giant_component_sizes,  # 新增：巨大连通分量大小
            'global_qualities': global_qualities,  # 新增：全局质量
            'critical_threshold': critical_threshold,
            'critical_subsidy': critical_subsidy,
            'percolation_subsidy': percolation_subsidy,  # 新增：逾渗临界补贴
            'percolation_threshold': percolation_threshold,  # 新增：逾渗临界巨大连通分量
            'gradient': gradient_adoption,
            'gradient_giant': gradient_giant  # 新增：巨大连通分量梯度
        }
    
    def analyze_network_effect_strength(self, G: nx.Graph, dynamics) -> Dict:
        """
        分析网络传播效应强度
        
        在无标度网络中，Hub节点的绿色行为可触发扩散
        扩散速度 v ∝ sqrt(γ·k_max)
        """
        degrees = dict(G.degree())
        max_degree = max(degrees.values())
        gamma = self.config['network'].get('gamma', 2.5)
        
        # 理论扩散速度
        diffusion_speed = np.sqrt(gamma * max_degree)
        
        # Hub节点识别（前10%度数最高的节点）
        degree_threshold = np.percentile(list(degrees.values()), 90)
        hub_nodes = [node for node, deg in degrees.items() if deg >= degree_threshold]
        
        # 重置所有农户为未采纳状态
        dynamics.farmer_df['adoption_state'] = 0
        
        # 让Hub节点采纳，模拟种子节点效应
        for hub in hub_nodes:
            dynamics.farmer_df.loc[hub, 'adoption_state'] = 1
        
        initial_rate = dynamics.adoption_rate
        
        # 运行60步，观察扩散过程
        rates_over_time = [initial_rate]
        num_steps = 60
        
        # 使用适中的补贴强度，让扩散过程可以发生
        subsidy = self.config['policy'].get('subsidy_base', 1000)
        
        for t in range(num_steps):
            # 每一步更新决策
            dynamics.step_decision_update(subsidy, use_threshold=False)
            rates_over_time.append(dynamics.adoption_rate)
        
        # 计算实际扩散速度 (采纳人数增长速率，户/步)
        initial_adopters = initial_rate * len(dynamics.farmer_df)
        final_adopters = rates_over_time[-1] * len(dynamics.farmer_df)
        actual_speed = (final_adopters - initial_adopters) / num_steps
        
        print(f"\n=== 网络传播效应分析 ===")
        print(f"最大度数 k_max: {max_degree}")
        print(f"Hub节点数: {len(hub_nodes)} (前10%)")
        print(f"初始采纳率: {initial_rate:.1%}")
        print(f"最终采纳率: {rates_over_time[-1]:.1%}")
        print(f"理论扩散速度系数: {diffusion_speed:.3f}")
        print(f"实际扩散速度: {actual_speed:.3f} 户/步")
        
        return {
            'max_degree': max_degree,
            'hub_count': len(hub_nodes),
            'hub_nodes': hub_nodes,
            'diffusion_speed_theory': diffusion_speed,
            'diffusion_speed_actual': actual_speed,
            'rates_over_time': rates_over_time,  # 这是采纳率随时间的列表
            'initial_rate': initial_rate,
            'final_rate': rates_over_time[-1]
        }
    
    def compute_modified_threshold(self, dynamics, hyperedges: Dict) -> float:
        """
        计算修正后的临界阈值
        结合超边渗流：Θ_c* = Θ_c · (1 - p_h)^(-κ)
        
        κ = ln(连通性增强倍数) / ln(1 + 超边比例)
        """
        # 原始阈值
        theta_c = self.config['decision']['threshold']
        
        # 超边比例
        num_hyperedges = len(hyperedges)
        num_farmers = len(dynamics.farmer_df)
        p_h = num_hyperedges / num_farmers
        
        # 计算平均度的提升
        avg_degree_original = 2 * dynamics.G.number_of_edges() / num_farmers
        
        # 超边带来的额外连接
        hyperedge_connections = sum(len(members) for members in hyperedges.values())
        avg_degree_enhanced = (
            2 * dynamics.G.number_of_edges() + hyperedge_connections
        ) / num_farmers
        
        # κ 指数
        if p_h > 0 and avg_degree_enhanced > avg_degree_original:
            kappa = np.log(avg_degree_enhanced / avg_degree_original) / np.log(1 + p_h)
        else:
            kappa = 1.0
        
        # 修正阈值
        theta_c_modified = theta_c * (1 - p_h) ** (-kappa)
        
        print(f"\n=== 超边临界阈值修正 ===")
        print(f"原始阈值 Θ_c: {theta_c:.3f}")
        print(f"超边比例 p_h: {p_h:.3f}")
        print(f"指数 κ: {kappa:.3f}")
        print(f"修正阈值 Θ_c*: {theta_c_modified:.3f}")
        
        return theta_c_modified
    
    def fit_phase_transition_curve(self, subsidy_values: np.ndarray, adoption_rates: np.ndarray) -> Dict:
        """
        拟合相变曲线 (S型或指数型)
        
        采用Sigmoid函数: f(x) = L / (1 + exp(-k(x - x0)))
        """
        def sigmoid(x, L, k, x0):
            return L / (1 + np.exp(-k * (x - x0)))
        
        try:
            # 初始猜测
            L_init = np.max(adoption_rates)
            x0_init = subsidy_values[len(subsidy_values) // 2]
            k_init = 0.01
            
            popt, pcov = curve_fit(
                sigmoid,
                subsidy_values,
                adoption_rates,
                p0=[L_init, k_init, x0_init],
                maxfev=5000
            )
            
            L_fit, k_fit, x0_fit = popt
            
            # 拟合值
            fitted_rates = sigmoid(subsidy_values, L_fit, k_fit, x0_fit)
            
            # R² 评估
            ss_res = np.sum((adoption_rates - fitted_rates) ** 2)
            ss_tot = np.sum((adoption_rates - np.mean(adoption_rates)) ** 2)
            r_squared = 1 - (ss_res / ss_tot)
            
            print(f"\n=== 相变曲线拟合 ===")
            print(f"Sigmoid参数: L={L_fit:.3f}, k={k_fit:.5f}, x0={x0_fit:.1f}")
            print(f"R²: {r_squared:.4f}")
            
            return {
                'L': L_fit,
                'k': k_fit,
                'x0': x0_fit,
                'r_squared': r_squared,
                'fitted_rates': fitted_rates
            }
        
        except Exception as e:
            print(f"拟合失败: {e}")
            return None


if __name__ == '__main__':
    from data_generator import load_config, FarmerDataGenerator
    from network_builder import HyperbolicNetworkBuilder
    from dynamics import AdoptionDynamics
    
    config = load_config('../config.yaml')
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()
    
    builder = HyperbolicNetworkBuilder(config, farmer_df)
    G = builder.build_scale_free_network()
    builder.add_family_village_links(G)
    hyperedges = builder.add_hyperedges(G)
    
    dynamics = AdoptionDynamics(config, G, farmer_df, hyperedges)
    
    analyzer = PhaseTransitionAnalyzer(config)
    
    # 临界阈值分析
    subsidy_range = np.linspace(500, 3000, 20)
    result = analyzer.analyze_percolation_threshold(dynamics, subsidy_range)
    
    # 拟合
    fit_result = analyzer.fit_phase_transition_curve(
        result['subsidy_values'],
        result['adoption_rates']
    )
    
    # 网络效应分析
    network_result = analyzer.analyze_network_effect_strength(G, dynamics)
    
    # 修正阈值
    theta_modified = analyzer.compute_modified_threshold(dynamics, hyperedges)

