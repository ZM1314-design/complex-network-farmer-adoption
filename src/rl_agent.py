"""
强化学习模块：DQN智能体决策优化
"""
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
from collections import deque
import random
from typing import Dict, Tuple, List


class DQNetwork(nn.Module):
    """DQN网络"""
    
    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super(DQNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)
    
    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.fc3(x)


class ReplayBuffer:
    """经验回放池"""
    
    def __init__(self, capacity: int):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size: int):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards),
            np.array(next_states),
            np.array(dones)
        )
    
    def __len__(self):
        return len(self.buffer)


class FarmerAgent:
    """
    农户智能体
    
    Agent 多维属性向量：
    Agent_i = {e_i, s_i, p_i, r_i, δ_i}
    - e_i: 经济水平
    - s_i: 社会影响力
    - p_i: 政策感知度
    - r_i: 风险偏好
    - δ_i: 短视性 (折扣因子)
    """
    
    def __init__(self, config: Dict, farmer_id: int, farmer_attrs: Dict):
        self.config = config
        self.farmer_id = farmer_id
        self.attrs = farmer_attrs
        
        # 状态空间维度：[经济, 社会影响, 政策感知, 风险, 肥力, 颗粒结构, 生物活性, 邻居采纳率, 全局Q, 短视性, 教育优先权, 话语权]
        self.state_dim = 12
        self.action_dim = 2  # 0: 传统施肥, 1: 绿色施肥
        
        self.rl_config = config['rl']
        self.reward_config = config['reward']
        
        # DQN网络
        self.policy_net = DQNetwork(
            self.state_dim, 
            self.action_dim, 
            self.rl_config['hidden_dim']
        )
        self.target_net = DQNetwork(
            self.state_dim, 
            self.action_dim, 
            self.rl_config['hidden_dim']
        )
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        self.optimizer = optim.Adam(
            self.policy_net.parameters(),
            lr=self.rl_config['learning_rate']
        )
        
        self.memory = ReplayBuffer(self.rl_config['memory_size'])
        
        # ε-greedy探索
        self.epsilon = self.rl_config['epsilon_start']
        self.epsilon_decay = self.rl_config['epsilon_decay']
        self.epsilon_min = self.rl_config['epsilon_end']
        
        # 个性化折扣因子 (短视性)
        self.gamma = farmer_attrs['discount_factor']
    
    def get_state_vector(self, dynamics, G, global_Q: float) -> np.ndarray:
        """
        构建状态向量 S（三维质量模型 + 三个新维度）
        S = [经济水平, 社会影响力权重, 政策感知, 风险偏好, 肥力, 颗粒结构, 生物活性, 邻居采纳率, 全局Q, 短视性, 教育优先权, 话语权]
        """
        farmer_id = self.farmer_id
        
        # 社会影响力权重：基于度中心性
        degree = G.degree(farmer_id)
        max_degree = max(dict(G.degree()).values())
        social_influence = degree / max_degree if max_degree > 0 else 0
        
        # 邻居采纳率
        neighbors = list(G.neighbors(farmer_id))
        if neighbors:
            neighbor_adoption = dynamics.farmer_df.loc[neighbors, 'adoption_state'].mean()
        else:
            neighbor_adoption = 0.0
        
        # 获取三个维度的质量（如果存在）
        if ('fertility' in dynamics.farmer_df.columns and 
            'soil_structure' in dynamics.farmer_df.columns and 
            'biological_activity' in dynamics.farmer_df.columns):
            fertility = dynamics.farmer_df.loc[farmer_id, 'fertility']
            soil_structure = dynamics.farmer_df.loc[farmer_id, 'soil_structure']
            biological_activity = dynamics.farmer_df.loc[farmer_id, 'biological_activity']
        else:
            # 向后兼容：使用综合质量
            land_quality = dynamics.farmer_df.loc[farmer_id, 'land_quality']
            fertility = land_quality
            soil_structure = land_quality
            biological_activity = land_quality
        
        # 获取短视性（如果存在）
        myopia = dynamics.farmer_df.loc[farmer_id, 'myopia'] if 'myopia' in dynamics.farmer_df.columns else 0.5
        
        # 获取教育优先权（如果存在）
        education_priority = dynamics.farmer_df.loc[farmer_id, 'education_priority'] if 'education_priority' in dynamics.farmer_df.columns else 0.5
        
        # 获取话语权（如果存在）
        political_voice = dynamics.farmer_df.loc[farmer_id, 'political_voice'] if 'political_voice' in dynamics.farmer_df.columns else 0.3
        
        state = np.array([
            self.attrs['economic_level'] / 100000,  # 归一化
            social_influence,
            self.attrs['policy_perception'],
            self.attrs['risk_tolerance'],
            fertility,  # 肥力
            soil_structure,  # 颗粒结构
            biological_activity,  # 生物活性
            neighbor_adoption,
            global_Q,
            myopia,  # 短视性 δ_i
            education_priority,  # 子女教育优先权
            political_voice  # 农民话语权（参政机会）
        ], dtype=np.float32)
        
        return state
    
    def select_action(self, state: np.ndarray, training: bool = True) -> int:
        """
        选择动作 (ε-greedy)
        """
        if training and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()
    
    def compute_reward(self, action: int, dynamics, subsidy: float) -> float:
        """
        计算奖励函数 R(S, A)（三维质量模型 + 三个新维度）
        R = λ1·经济效益 + λ2·政策补贴 + λ3·社会声誉 + λ4·子女教育优先权 + λ5·农民话语权
        
        经济效益分别考虑三个维度：
        - 肥力(F)：直接影响产量
        - 颗粒结构(S)：影响水分保持和长期产量
        - 生物活性(B)：影响土壤健康和可持续性
        """
        lambda1 = self.reward_config['lambda1']
        lambda2 = self.reward_config['lambda2']
        lambda3 = self.reward_config['lambda3']
        lambda4 = self.reward_config.get('lambda4', 0.3)  # 子女教育优先权权重
        lambda5 = self.reward_config.get('lambda5', 0.2)  # 农民话语权权重
        
        farmer_id = self.farmer_id
        
        # 获取三个维度的质量（如果存在）
        if ('fertility' in dynamics.farmer_df.columns and 
            'soil_structure' in dynamics.farmer_df.columns and 
            'biological_activity' in dynamics.farmer_df.columns):
            fertility = dynamics.farmer_df.loc[farmer_id, 'fertility']
            soil_structure = dynamics.farmer_df.loc[farmer_id, 'soil_structure']
            biological_activity = dynamics.farmer_df.loc[farmer_id, 'biological_activity']
        else:
            # 向后兼容：使用综合质量
            land_quality = dynamics.farmer_df.loc[farmer_id, 'land_quality']
            fertility = land_quality
            soil_structure = land_quality
            biological_activity = land_quality
        
        # 经济效益：分别考虑三个维度的影响
        # 肥力直接影响短期产量，颗粒结构影响长期稳定性，生物活性影响可持续性
        if action == 1:  # 绿色施肥
            # 肥力对产量的影响（权重0.5，短期效应）
            yield_fertility = 1.0 + 0.5 * fertility
            # 颗粒结构对产量的影响（权重0.3，长期效应）
            yield_structure = 1.0 + 0.3 * soil_structure
            # 生物活性对产量的影响（权重0.2，可持续性）
            yield_biological = 1.0 + 0.2 * biological_activity
            # 综合产量因子
            yield_factor = yield_fertility * 0.5 + yield_structure * 0.3 + yield_biological * 0.2
            cost = self.config['policy']['cost_green'] - subsidy
            economic_benefit = yield_factor * 10000 - cost
        else:  # 传统施肥
            # 传统施肥主要依赖肥力，但长期会损害结构和生物活性
            yield_fertility = 1.0 + 0.3 * fertility  # 短期肥力效应较低
            yield_structure = 1.0 + 0.1 * soil_structure  # 结构效应很小
            yield_biological = 1.0 + 0.05 * biological_activity  # 生物活性效应很小
            yield_factor = yield_fertility * 0.6 + yield_structure * 0.2 + yield_biological * 0.2
            cost = self.config['policy']['cost_traditional']
            economic_benefit = yield_factor * 10000 - cost
        
        # 政策补贴
        policy_reward = subsidy if action == 1 else 0
        
        # 社会声誉：采纳绿色施肥在高采纳率社区获得更高声誉
        neighbors = list(dynamics.G.neighbors(farmer_id))
        if neighbors:
            neighbor_adoption = dynamics.farmer_df.loc[neighbors, 'adoption_state'].mean()
            if action == 1:
                social_reputation = neighbor_adoption * 1000  # 从众奖励
            else:
                social_reputation = (1 - neighbor_adoption) * 500
        else:
            social_reputation = 0
        
        # 子女教育优先权奖励 (如果采纳绿色施肥)
        # 采纳绿色施肥可获得子女教育优先权，价值与教育优先权水平相关
        if action == 1:
            # 获取当前教育优先权水平
            education_priority = dynamics.farmer_df.loc[farmer_id, 'education_priority'] if 'education_priority' in dynamics.farmer_df.columns else 0.5
            # 采纳绿色施肥提升教育优先权
            education_bonus = 500 * (1 + education_priority)  # 基础500 + 基于当前优先权的加成
        else:
            education_bonus = 0
        
        # 农民话语权（参政机会）奖励 (如果采纳绿色施肥)
        # 采纳绿色施肥可获得更多参政机会，价值与话语权水平相关
        if action == 1:
            # 获取当前话语权水平
            political_voice = dynamics.farmer_df.loc[farmer_id, 'political_voice'] if 'political_voice' in dynamics.farmer_df.columns else 0.3
            # 采纳绿色施肥提升话语权
            voice_bonus = 300 * (1 + political_voice)  # 基础300 + 基于当前话语权的加成
        else:
            voice_bonus = 0
        
        # 总奖励（增加直接奖励采纳行为，提供更强的学习信号）
        adoption_bonus = 50.0 if action == 1 else 0.0  # 直接奖励采纳行为
        
        reward = (
            adoption_bonus +  # 新增：直接奖励采纳
            lambda1 * economic_benefit / 10000 +  # 归一化
            lambda2 * policy_reward / 1000 +
            lambda3 * social_reputation / 1000 +
            lambda4 * education_bonus / 500 +  # 子女教育优先权
            lambda5 * voice_bonus / 300  # 农民话语权（参政机会）
        )
        
        return reward
    
    def store_transition(self, state, action, reward, next_state, done):
        """存储经验"""
        self.memory.push(state, action, reward, next_state, done)
    
    def train_step(self):
        """训练一步"""
        if len(self.memory) < self.rl_config['batch_size']:
            return None
        
        batch_size = self.rl_config['batch_size']
        states, actions, rewards, next_states, dones = self.memory.sample(batch_size)
        
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # 当前Q值
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # 目标Q值
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # 损失
        loss = F.mse_loss(current_q, target_q)
        
        # 优化
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self):
        """更新目标网络"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def decay_epsilon(self):
        """衰减探索率"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
    
    def save_model(self, path: str):
        """保存模型"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, path)
    
    def load_model(self, path: str):
        """加载模型"""
        checkpoint = torch.load(path)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']


class MultiAgentSystem:
    """多智能体系统"""
    
    def __init__(self, config: Dict, dynamics, G):
        self.config = config
        self.dynamics = dynamics
        self.G = G
        
        # 为每个农户创建智能体
        self.agents = {}
        for idx, row in dynamics.farmer_df.iterrows():
            attrs = {
                'economic_level': row['economic_level'],
                'policy_perception': row['policy_perception'],
                'risk_tolerance': row['risk_tolerance'],
                'discount_factor': row['discount_factor'],
                # 新增维度（如果存在）
                'myopia': row.get('myopia', 0.5),
                'education_priority': row.get('education_priority', 0.5),
                'political_voice': row.get('political_voice', 0.3)
            }
            self.agents[idx] = FarmerAgent(config, idx, attrs)
    
    def step(self, subsidy: float, training: bool = True):
        """
        多智能体同步决策
        
        Returns:
            平均奖励
        """
        total_reward = 0.0
        
        # 获取当前状态
        global_Q = self.dynamics.global_Q
        states = {}
        actions = {}
        
        for farmer_id, agent in self.agents.items():
            state = agent.get_state_vector(self.dynamics, self.G, global_Q)
            states[farmer_id] = state
            
            # 选择动作
            action = agent.select_action(state, training)
            actions[farmer_id] = action
            
            # 更新农户决策
            self.dynamics.farmer_df.loc[farmer_id, 'adoption_state'] = action
        
        # 更新系统动态
        self.dynamics.update_land_quality(dt=1.0)
        self.dynamics.adoption_rate = self.dynamics.farmer_df['adoption_state'].mean()
        
        # 计算奖励并存储经验
        for farmer_id, agent in self.agents.items():
            action = actions[farmer_id]
            reward = agent.compute_reward(action, self.dynamics, subsidy)
            total_reward += reward
            
            next_state = agent.get_state_vector(self.dynamics, self.G, self.dynamics.global_Q)
            done = False
            
            agent.store_transition(states[farmer_id], action, reward, next_state, done)
            
            # 训练
            if training:
                agent.train_step()
        
        return total_reward / len(self.agents)
    
    def update_all_target_networks(self):
        """更新所有智能体的目标网络"""
        for agent in self.agents.values():
            agent.update_target_network()
    
    def decay_all_epsilon(self):
        """衰减所有智能体的探索率"""
        for agent in self.agents.values():
            agent.decay_epsilon()


if __name__ == '__main__':
    from data_generator import load_config, FarmerDataGenerator
    from network_builder import HyperbolicNetworkBuilder
    from dynamics import AdoptionDynamics
    
    config = load_config('../config.yaml')
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()
    
    builder = HyperbolicNetworkBuilder(config, farmer_df)
    G = builder.build_scale_free_network()
    hyperedges = builder.add_hyperedges(G)
    
    dynamics = AdoptionDynamics(config, G, farmer_df, hyperedges)
    mas = MultiAgentSystem(config, dynamics, G)
    
    print("\n=== 多智能体系统测试 ===")
    print(f"智能体数量: {len(mas.agents)}")
    
    # 测试几步
    for t in range(5):
        subsidy = 1500
        avg_reward = mas.step(subsidy, training=True)
        state = dynamics.get_system_state()
        print(f"\nStep {t+1}:")
        print(f"  平均奖励: {avg_reward:.3f}")
        print(f"  采纳率: {state['adoption_rate']:.2%}")

