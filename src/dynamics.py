"""
动力学演化模块：耕地质量方程 + TPB决策过程
"""
import numpy as np
import networkx as nx
import pandas as pd
from typing import Dict, Tuple


class AdoptionDynamics:
    """农户采纳行为动力学"""
    
    def __init__(self, config: Dict, G: nx.Graph, farmer_df: pd.DataFrame, hyperedges: Dict):
        self.config = config
        self.G = G
        self.farmer_df = farmer_df
        self.hyperedges = hyperedges
        
        self.quality_config = config['quality_dynamics']
        self.policy_config = config['policy']
        self.decision_config = config['decision']
        
        # 全局序参数（综合质量：三个维度的加权平均）
        # 计算初始全局质量（如果数据中已有三个维度）
        if 'fertility' in farmer_df.columns and 'soil_structure' in farmer_df.columns and 'biological_activity' in farmer_df.columns:
            # 使用三个维度的加权平均
            weights = self.quality_config.get('quality_weights', {'fertility': 0.4, 'soil_structure': 0.3, 'biological_activity': 0.3})
            self.global_Q = (
                weights['fertility'] * farmer_df['fertility'].mean() +
                weights['soil_structure'] * farmer_df['soil_structure'].mean() +
                weights['biological_activity'] * farmer_df['biological_activity'].mean()
            )
        else:
            # 兼容旧版本：使用单一质量
            self.global_Q = config['quality_dynamics']['initial_Q']
        
        self.adoption_rate = farmer_df['adoption_state'].mean()
        
    def update_land_quality(self, dt: float = 1.0):
        """
        更新耕地质量（三个维度：肥力、颗粒结构、生物活性）
        
        每个维度的演化方程：
        dF/dt = α_F·a_i - β_F·(1-a_i) - γ_F·F + δ_F + D_F·∇²F  (肥力)
        dS/dt = α_S·a_i - β_S·(1-a_i) - γ_S·S + δ_S + D_S·∇²S  (颗粒结构)
        dB/dt = α_B·a_i - β_B·(1-a_i) - γ_B·B + δ_B + D_B·∇²B  (生物活性)
        
        其中：
        - F: Fertility (肥力)
        - S: Soil Structure (颗粒结构)
        - B: Biological Activity (生物活性)
        """
        # 获取参数（支持每个维度独立参数）
        alpha = self.quality_config.get('alpha', {})
        beta = self.quality_config.get('beta', {})
        gamma = self.quality_config.get('gamma', {})
        delta = self.quality_config.get('delta', {})
        diffusion = self.quality_config.get('diffusion', {})
        
        # 如果参数是标量，则三个维度使用相同参数
        if isinstance(alpha, (int, float)):
            alpha = {'fertility': alpha, 'soil_structure': alpha, 'biological_activity': alpha}
        if isinstance(beta, (int, float)):
            beta = {'fertility': beta, 'soil_structure': beta, 'biological_activity': beta}
        if isinstance(gamma, (int, float)):
            gamma = {'fertility': gamma, 'soil_structure': gamma, 'biological_activity': gamma}
        if isinstance(delta, (int, float)):
            delta = {'fertility': delta, 'soil_structure': delta, 'biological_activity': delta}
        if isinstance(diffusion, (int, float)):
            diffusion = {'fertility': diffusion, 'soil_structure': diffusion, 'biological_activity': diffusion}
        
        # 计算绿色和传统施肥比例
        rho_g = self.farmer_df['adoption_state'].mean()
        rho_t = 1 - rho_g
        
        # 检查是否使用三维质量模型
        use_3d_quality = ('fertility' in self.farmer_df.columns and 
                          'soil_structure' in self.farmer_df.columns and 
                          'biological_activity' in self.farmer_df.columns)
        
        if use_3d_quality:
            # 三维质量模型
            quality_dims = ['fertility', 'soil_structure', 'biological_activity']
            weights = self.quality_config.get('quality_weights', {'fertility': 0.4, 'soil_structure': 0.3, 'biological_activity': 0.3})
            
            # 更新每个维度的全局质量
            global_qualities = {}
            for dim in quality_dims:
                global_q = (
                    self.farmer_df[dim].mean() if dim in self.farmer_df.columns 
                    else self.quality_config['initial_Q']
                )
                dQ = (alpha[dim] * rho_g - beta[dim] * rho_t - 
                      gamma[dim] * global_q + delta[dim])
                global_q = np.clip(global_q + dQ * dt, 0, 1)
                global_qualities[dim] = global_q
            
            # 计算综合全局质量（加权平均）
            self.global_Q = (
                weights['fertility'] * global_qualities['fertility'] +
                weights['soil_structure'] * global_qualities['soil_structure'] +
                weights['biological_activity'] * global_qualities['biological_activity']
            )
            
            # 更新个体三个维度的质量
            for idx in self.farmer_df.index:
                adoption = self.farmer_df.loc[idx, 'adoption_state']
                neighbors = list(self.G.neighbors(idx))
                
                for dim in quality_dims:
                    current_q = self.farmer_df.loc[idx, dim]
                    
                    if adoption == 1:  # 绿色施肥
                        dq_local = alpha[dim] - gamma[dim] * current_q + delta[dim]
                    else:  # 传统施肥
                        dq_local = -beta[dim] - gamma[dim] * current_q + delta[dim]
                    
                    # 扩散项：邻居影响
                    if neighbors:
                        neighbor_quality = self.farmer_df.loc[neighbors, dim].mean()
                        dq_local += diffusion[dim] * (neighbor_quality - current_q)
                    
                    new_q = current_q + dq_local * dt
                    self.farmer_df.loc[idx, dim] = np.clip(new_q, 0, 1)
                
                # 更新综合质量（向后兼容）
                self.farmer_df.loc[idx, 'land_quality'] = (
                    weights['fertility'] * self.farmer_df.loc[idx, 'fertility'] +
                    weights['soil_structure'] * self.farmer_df.loc[idx, 'soil_structure'] +
                    weights['biological_activity'] * self.farmer_df.loc[idx, 'biological_activity']
                )
        else:
            # 兼容旧版本：单一质量模型
            alpha_val = alpha.get('fertility', self.quality_config.get('alpha', 0.05))
            beta_val = beta.get('fertility', self.quality_config.get('beta', 0.08))
            gamma_val = gamma.get('fertility', self.quality_config.get('gamma', 0.02))
            delta_val = delta.get('fertility', self.quality_config.get('delta', 0.01))
            
            # 全局耕地质量演化
            dQ = alpha_val * rho_g - beta_val * rho_t - gamma_val * self.global_Q + delta_val
            self.global_Q += dQ * dt
            self.global_Q = np.clip(self.global_Q, 0, 1)
            
            # 个体耕地质量受全局影响 + 自身决策
            for idx in self.farmer_df.index:
                adoption = self.farmer_df.loc[idx, 'adoption_state']
                current_q = self.farmer_df.loc[idx, 'land_quality']
                
                if adoption == 1:  # 绿色施肥
                    dq_local = alpha_val - gamma_val * current_q + delta_val
                else:  # 传统施肥
                    dq_local = -beta_val - gamma_val * current_q + delta_val
                
                # 加上全局影响 (邻居效应)
                neighbors = list(self.G.neighbors(idx))
                if neighbors:
                    neighbor_quality = self.farmer_df.loc[neighbors, 'land_quality'].mean()
                    dq_local += 0.1 * (neighbor_quality - current_q)  # 扩散项
                
                new_q = current_q + dq_local * dt
                self.farmer_df.loc[idx, 'land_quality'] = np.clip(new_q, 0, 1)
    
    def compute_social_influence(self, farmer_id: int) -> float:
        """
        计算社会网络影响 S_social（单位：元）
        基于邻居的采纳状态和权重，转换为经济价值
        """
        neighbors = list(self.G.neighbors(farmer_id))
        if not neighbors:
            return 0.0
        
        # 邻居影响：加权求和（得到邻居采纳率，0-1之间）
        total_influence = 0.0
        total_weight = 0.0
        
        for neighbor in neighbors:
            weight = self.G[farmer_id][neighbor].get('weight', 1.0)
            adoption = self.farmer_df.loc[neighbor, 'adoption_state']
            total_influence += weight * adoption
            total_weight += weight
        
        if total_weight > 0:
            neighbor_adoption_rate = total_influence / total_weight
        else:
            neighbor_adoption_rate = 0.0
        
        # 超边影响 (合作社效应)
        for he_id, members in self.hyperedges.items():
            if farmer_id in members:
                # 合作社内的采纳率
                cooperative_adoption = self.farmer_df.loc[members, 'adoption_state'].mean()
                neighbor_adoption_rate = 0.7 * neighbor_adoption_rate + 0.3 * cooperative_adoption  # 混合
                break
        
        # 转换为经济价值：邻居采纳率 × 社会声誉基准价值（元）
        # 基准价值：如果所有邻居都采纳，获得最大社会声誉价值
        social_value_base = self.decision_config.get('social_value_base', 1000.0)  # 默认1000元
        S_social = neighbor_adoption_rate * social_value_base
        
        return S_social
    
    def compute_policy_incentive(self, farmer_id: int, subsidy: float) -> float:
        """
        计算政策激励强度 S_policy（单位：元）
        考虑补贴、培训等
        """
        training = self.farmer_df.loc[farmer_id, 'training_access']
        perception = self.farmer_df.loc[farmer_id, 'policy_perception']
        
        # 基础政策激励：补贴金额 × 感知系数（单位：元）
        S_policy = subsidy * perception
        
        # 培训加成（培训增加20%的感知价值）
        if training:
            S_policy *= 1.2
        
        return S_policy
    
    def compute_utility_tpb(self, farmer_id: int, action: int, subsidy: float) -> float:
        """
        计算效用 (TPB理论) - 所有项单位均为"元"
        U_i = θ_p·S_policy + θ_s·S_social - θ_e·C_cost + θ_q·Q_benefit
        
        Args:
            farmer_id: 农户ID
            action: 决策 (0: 传统, 1: 绿色)
            subsidy: 当前补贴强度（元）
            
        Returns:
            效用值（元）
        """
        theta_p0 = self.decision_config['theta_p0']
        theta_s0 = self.decision_config['theta_s0']
        theta_e = self.decision_config['theta_e']
        theta_q = self.decision_config['theta_q']
        mu = self.decision_config['mu']
        
        # 政策感知项（单位：元）
        # S_policy = 补贴金额 × 感知系数 × 培训加成
        S_policy = self.compute_policy_incentive(farmer_id, subsidy)
        
        # 社会网络项（单位：元）
        # S_social = 邻居采纳率 × 社会声誉基准价值
        S_social = self.compute_social_influence(farmer_id)
        
        # 成本项（单位：元）
        cost_green = self.policy_config['cost_green']
        cost_traditional = self.policy_config['cost_traditional']
        
        if action == 1:  # 绿色施肥
            net_cost = cost_green - subsidy  # 净成本（元）
        else:  # 传统施肥
            net_cost = cost_traditional  # 成本（元）
        
        C_cost = net_cost  # 直接使用元，不再归一化
        
        # 耕地质量收益项（单位：元）
        # 如果存在三个维度，使用加权平均；否则使用单一质量
        if ('fertility' in self.farmer_df.columns and 
            'soil_structure' in self.farmer_df.columns and 
            'biological_activity' in self.farmer_df.columns):
            weights = self.quality_config.get('quality_weights', 
                                               {'fertility': 0.4, 'soil_structure': 0.3, 'biological_activity': 0.3})
            Q_normalized = (
                weights['fertility'] * self.farmer_df.loc[farmer_id, 'fertility'] +
                weights['soil_structure'] * self.farmer_df.loc[farmer_id, 'soil_structure'] +
                weights['biological_activity'] * self.farmer_df.loc[farmer_id, 'biological_activity']
            )
        else:
            Q_normalized = self.farmer_df.loc[farmer_id, 'land_quality']
        
        # 将质量值转换为经济收益（元）
        # 质量收益 = 质量值 × 基准产量价值
        quality_value_base = self.decision_config.get('quality_value_base', 5000.0)  # 默认5000元（质量=1时的收益）
        Q_benefit = Q_normalized * quality_value_base
        
        # 耦合政策感知：θ_p = θ_p0 · tanh(μQ)
        theta_p = theta_p0 * np.tanh(mu * self.global_Q)
        
        # 总效用（所有项单位均为"元"）
        # U_i = θ_p·S_policy + θ_s·S_social - θ_e·C_cost + θ_q·Q_benefit
        # 其中：
        # - S_policy: 元 - 政策激励价值
        # - S_social: 元 - 社会网络影响价值
        # - C_cost: 元 - 净成本
        # - Q_benefit: 元 - 质量收益
        utility = (
            theta_p * S_policy +
            theta_s0 * S_social -
            theta_e * C_cost +
            theta_q * Q_benefit
        )
        
        return utility
    
    def logit_adoption_probability(self, farmer_id: int, subsidy: float) -> float:
        """
        Logit函数决策：P(a_i=1) = 1 / (1 + exp(-τ·U_i + ε_i))
        其中 ε_i ~ Gumbel(0,1)
        """
        tau = self.decision_config['tau']
        
        # 计算绿色施肥的效用
        U_green = self.compute_utility_tpb(farmer_id, action=1, subsidy=subsidy)
        
        # 随机误差项 (Gumbel分布)
        epsilon = np.random.gumbel(0, 1)
        
        # Logit概率（防止数值溢出）
        # 使用 log-sum-exp 技巧：exp(x) / (exp(x) + 1) = 1 / (1 + exp(-x))
        exponent = tau * U_green + epsilon
        
        # 防止溢出：如果exponent太大，直接返回1；如果太小，直接返回0
        if exponent > 500:
            prob = 1.0
        elif exponent < -500:
            prob = 0.0
        else:
            prob = 1.0 / (1.0 + np.exp(-exponent))
        
        return np.clip(prob, 0.0, 1.0)
    
    def percolation_threshold_check(self, farmer_id: int, subsidy: float) -> bool:
        """
        临界阈值判据 (Percolation Phase Transition)
        
        农户 i 采纳绿色施肥需满足：
        (Σ w_ij·a_j) / max_k(w_ik) + P_i/P_max - C_i/C_max ≥ Θ_c
        
        Returns:
            是否超过阈值
        """
        threshold = self.decision_config['threshold']
        
        neighbors = list(self.G.neighbors(farmer_id))
        if not neighbors:
            return False
        
        # 邻居采纳影响（归一化到 0-1）：加权邻居采纳率
        total_influence = 0.0
        total_weight = 0.0
        for neighbor in neighbors:
            weight = self.G[farmer_id][neighbor].get('weight', 1.0)
            adoption = self.farmer_df.loc[neighbor, 'adoption_state']
            total_influence += weight * adoption
            total_weight += weight
        
        neighbor_adoption_rate = (total_influence / total_weight) if total_weight > 0 else 0.0
        social_term = float(np.clip(neighbor_adoption_rate, 0.0, 1.0))
        
        # 政策项（归一化到 0-1）
        P_i = float(subsidy)
        P_max = float(self.policy_config['subsidy_range'][1])
        policy_term = float(np.clip(P_i / P_max, 0.0, 1.0)) if P_max > 0 else 0.0
        
        # 成本项（归一化到 0-1）：补贴后净成本占比
        # subsidy 越大，net_cost 越小，cost_term 越小（更容易通过阈值）
        cost_green = float(self.policy_config['cost_green'])
        net_cost = max(cost_green - P_i, 0.0)
        cost_term = (net_cost / cost_green) if cost_green > 0 else 1.0
        cost_term = float(np.clip(cost_term, 0.0, 1.0))
        
        # 总得分（无量纲）
        score = social_term + policy_term - cost_term
        
        return score >= threshold
    
    def step_decision_update(self, subsidy: float, use_threshold: bool = False):
        """
        一步决策更新
        
        Args:
            subsidy: 当前补贴水平
            use_threshold: 是否使用阈值判据 (否则用Logit)
        """
        new_adoptions = self.farmer_df['adoption_state'].copy()
        
        for idx in self.farmer_df.index:
            if use_threshold:
                # 阈值判据
                should_adopt = self.percolation_threshold_check(idx, subsidy)
                new_adoptions[idx] = int(should_adopt)
            else:
                # Logit概率决策
                prob = self.logit_adoption_probability(idx, subsidy)
                new_adoptions[idx] = int(np.random.rand() < prob)
        
        # 更新状态
        self.farmer_df['adoption_state'] = new_adoptions
        self.adoption_rate = new_adoptions.mean()
        
        # 动态更新教育优先权和话语权（基于采纳状态）
        self._update_policy_incentives()
    
    def _update_policy_incentives(self):
        """
        动态更新教育优先权和话语权
        采纳绿色施肥的农户会获得更高的教育优先权和话语权
        """
        # 更新教育优先权
        if 'education_priority' in self.farmer_df.columns:
            for idx in self.farmer_df.index:
                adoption = self.farmer_df.loc[idx, 'adoption_state']
                current_priority = self.farmer_df.loc[idx, 'education_priority']
                
                if adoption == 1:  # 采纳绿色施肥
                    # 采纳后教育优先权提升（渐进式）
                    increment = 0.05 * (1 - current_priority)  # 越接近1提升越慢
                    new_priority = np.clip(current_priority + increment, 0, 1)
                else:  # 不采纳
                    # 不采纳时教育优先权缓慢下降
                    decrement = 0.01 * current_priority  # 越接近0下降越慢
                    new_priority = np.clip(current_priority - decrement, 0, 1)
                
                self.farmer_df.loc[idx, 'education_priority'] = new_priority
        
        # 更新话语权（参政机会）
        if 'political_voice' in self.farmer_df.columns:
            # 计算全局采纳率，影响话语权提升速度
            global_adoption_rate = self.adoption_rate
            
            for idx in self.farmer_df.index:
                adoption = self.farmer_df.loc[idx, 'adoption_state']
                current_voice = self.farmer_df.loc[idx, 'political_voice']
                
                if adoption == 1:  # 采纳绿色施肥
                    # 采纳后话语权提升，且全局采纳率越高提升越快（从众效应）
                    increment = 0.03 * (1 + global_adoption_rate) * (1 - current_voice)
                    new_voice = np.clip(current_voice + increment, 0, 1)
                else:  # 不采纳
                    # 不采纳时话语权缓慢下降
                    decrement = 0.01 * current_voice
                    new_voice = np.clip(current_voice - decrement, 0, 1)
                
                self.farmer_df.loc[idx, 'political_voice'] = new_voice
    
    def get_system_state(self) -> Dict:
        """获取系统当前状态"""
        state = {
            'global_Q': self.global_Q,
            'adoption_rate': self.adoption_rate,
            'mean_land_quality': self.farmer_df['land_quality'].mean(),
            'std_land_quality': self.farmer_df['land_quality'].std()
        }
        
        # 如果使用三维质量模型，添加各维度的统计信息
        if ('fertility' in self.farmer_df.columns and 
            'soil_structure' in self.farmer_df.columns and 
            'biological_activity' in self.farmer_df.columns):
            state['mean_fertility'] = self.farmer_df['fertility'].mean()
            state['mean_soil_structure'] = self.farmer_df['soil_structure'].mean()
            state['mean_biological_activity'] = self.farmer_df['biological_activity'].mean()
            state['std_fertility'] = self.farmer_df['fertility'].std()
            state['std_soil_structure'] = self.farmer_df['soil_structure'].std()
            state['std_biological_activity'] = self.farmer_df['biological_activity'].std()
        
        # 添加新维度的统计信息
        if 'education_priority' in self.farmer_df.columns:
            state['mean_education_priority'] = self.farmer_df['education_priority'].mean()
        if 'political_voice' in self.farmer_df.columns:
            state['mean_political_voice'] = self.farmer_df['political_voice'].mean()
        if 'myopia' in self.farmer_df.columns:
            state['mean_myopia'] = self.farmer_df['myopia'].mean()
        
        return state


if __name__ == '__main__':
    from data_generator import load_config, FarmerDataGenerator
    from network_builder import HyperbolicNetworkBuilder
    
    config = load_config('../config.yaml')
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()
    
    builder = HyperbolicNetworkBuilder(config, farmer_df)
    G = builder.build_scale_free_network()
    hyperedges = builder.add_hyperedges(G)
    
    dynamics = AdoptionDynamics(config, G, farmer_df, hyperedges)
    
    print("\n=== 动力学测试 ===")
    print(f"初始采纳率: {dynamics.adoption_rate:.2%}")
    print(f"初始全局质量: {dynamics.global_Q:.3f}")
    
    # 模拟10步
    for t in range(10):
        subsidy = 1500 + 100 * t  # 逐渐增加补贴
        dynamics.step_decision_update(subsidy, use_threshold=False)
        dynamics.update_land_quality(dt=1.0)
        
        state = dynamics.get_system_state()
        print(f"\nStep {t+1} (补贴={subsidy}):")
        print(f"  采纳率: {state['adoption_rate']:.2%}")
        print(f"  全局质量: {state['global_Q']:.3f}")

