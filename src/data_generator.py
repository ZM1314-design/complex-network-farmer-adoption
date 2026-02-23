"""
数据生成模块：生成农户属性和初始网络结构
"""
import numpy as np
import pandas as pd
from typing import Dict, Tuple
import yaml


class FarmerDataGenerator:
    """农户数据生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.num_farmers = config['network']['num_farmers']
        np.random.seed(42)
    
    def generate_farmer_attributes(self) -> pd.DataFrame:
        """
        生成农户的多维属性
        
        Returns:
            DataFrame: 包含所有农户属性的数据框
        """
        farmer_config = self.config['farmer']
        
        # 经济水平 (正态分布，确保非负)
        economic = np.maximum(
            np.random.normal(
                farmer_config['economic_mean'],
                farmer_config['economic_std'],
                self.num_farmers
            ),
            0
        )
        
        # 教育程度 (离散等级 0-3)
        education = np.random.choice(
            farmer_config['education_levels'],
            size=self.num_farmers,
            p=[0.3, 0.4, 0.2, 0.1]  # 概率分布
        )
        
        # 风险偏好 [0, 1]
        risk_tolerance = np.clip(
            np.random.normal(
                farmer_config['risk_tolerance_mean'],
                farmer_config['risk_tolerance_std'],
                self.num_farmers
            ),
            0, 1
        )
        
        # 环境意识 [0, 1]
        env_awareness = np.clip(
            np.random.normal(
                farmer_config['env_awareness_mean'],
                farmer_config['env_awareness_std'],
                self.num_farmers
            ),
            0, 1
        )
        
        # 短视性 - 用于强化学习折扣因子
        # δ_i ~ U(0.1, 0.9)，通过 γ = 1/(1+δ_i) 转化
        myopia = np.random.uniform(
            farmer_config['myopia_range'][0],
            farmer_config['myopia_range'][1],
            self.num_farmers
        )
        discount_factor = 1.0 / (1.0 + myopia)
        
        # 子女教育优先权 [0, 1] - 采纳绿色施肥可获得子女教育优先权
        # 初始值：基于教育水平和经济水平
        education_priority_base = (
            0.3 * (education / 3.0) +  # 教育水平越高，越重视教育
            0.2 * np.clip(economic / 100000, 0, 1) +  # 经济水平影响
            0.5 * np.random.uniform(0, 1, self.num_farmers)  # 随机因素
        )
        education_priority = np.clip(education_priority_base, 0, 1)
        
        # 农民话语权（参政机会）[0, 1] - 采纳绿色施肥可获得更多参政机会
        # 初始值：基于社会影响力（度中心性会在网络构建后更新）
        # 这里先基于教育水平和经济水平估算
        political_voice_base = (
            0.4 * (education / 3.0) +  # 教育水平影响话语权
            0.3 * np.clip(economic / 100000, 0, 1) +  # 经济水平影响
            0.3 * np.random.uniform(0, 1, self.num_farmers)  # 随机因素
        )
        political_voice = np.clip(political_voice_base, 0, 1)
        
        # 初始采纳状态 (0: 传统, 1: 绿色)
        initial_adoption = np.zeros(self.num_farmers, dtype=int)
        # 随机让少部分农户初始采纳绿色施肥
        initial_green_ratio = 0.05
        initial_adopters = np.random.choice(
            self.num_farmers,
            size=int(self.num_farmers * initial_green_ratio),
            replace=False
        )
        initial_adoption[initial_adopters] = 1
        
        # 位置坐标 (用于双曲几何网络)
        # 在单位球内均匀分布
        theta = np.random.uniform(0, 2*np.pi, self.num_farmers)
        phi = np.arccos(2*np.random.uniform(0, 1, self.num_farmers) - 1)
        r = np.random.uniform(0, 1, self.num_farmers) ** (1/3)  # 体积均匀分布
        
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        
        # 耕地质量初始值（三个维度：肥力、颗粒结构、生物活性）
        initial_Q = self.config['quality_dynamics']['initial_Q']
        
        # 如果配置中指定了三个维度的初始值，使用它们；否则使用统一初始值
        initial_fertility = self.config['quality_dynamics'].get('initial_fertility', initial_Q)
        initial_structure = self.config['quality_dynamics'].get('initial_soil_structure', initial_Q)
        initial_biological = self.config['quality_dynamics'].get('initial_biological_activity', initial_Q)
        
        # 生成三个维度的质量（正态分布，带随机性）
        fertility = np.random.normal(initial_fertility, 0.1, self.num_farmers)
        fertility = np.clip(fertility, 0, 1)
        
        soil_structure = np.random.normal(initial_structure, 0.1, self.num_farmers)
        soil_structure = np.clip(soil_structure, 0, 1)
        
        biological_activity = np.random.normal(initial_biological, 0.1, self.num_farmers)
        biological_activity = np.clip(biological_activity, 0, 1)
        
        # 计算综合质量（加权平均，向后兼容）
        quality_weights = self.config['quality_dynamics'].get('quality_weights', 
                                                               {'fertility': 0.4, 'soil_structure': 0.3, 'biological_activity': 0.3})
        land_quality = (
            quality_weights['fertility'] * fertility +
            quality_weights['soil_structure'] * soil_structure +
            quality_weights['biological_activity'] * biological_activity
        )
        
        # 构建DataFrame
        df = pd.DataFrame({
            'farmer_id': range(self.num_farmers),
            'economic_level': economic,
            'education': education,
            'risk_tolerance': risk_tolerance,
            'env_awareness': env_awareness,
            'myopia': myopia,  # 短视性参数 δ_i
            'discount_factor': discount_factor,  # RL折扣因子 γ_i = 1/(1+δ_i)
            'adoption_state': initial_adoption,
            # 三个维度的质量
            'fertility': fertility,
            'soil_structure': soil_structure,
            'biological_activity': biological_activity,
            # 综合质量（向后兼容）
            'land_quality': land_quality,
            # 新增维度：政策激励相关
            'education_priority': education_priority,  # 子女教育优先权 [0, 1]
            'political_voice': political_voice,  # 农民话语权（参政机会）[0, 1]
            'x': x,
            'y': y,
            'z': z,
            'policy_perception': np.random.uniform(0.3, 0.7, self.num_farmers),
            'training_access': np.random.binomial(
                1, 
                self.config['policy']['training_coverage'],
                self.num_farmers
            )
        })
        
        return df
    
    def generate_social_network_data(self, farmer_df: pd.DataFrame) -> pd.DataFrame:
        """
        生成社交网络的边数据 (用于后续NetworkX构建)
        这里先生成基础的邻居关系数据
        
        Args:
            farmer_df: 农户属性数据框
            
        Returns:
            DataFrame: 边列表 (source, target, weight)
        """
        # 这部分会在 network_builder.py 中基于双曲几何规则实现
        # 这里只是预留接口
        return pd.DataFrame(columns=['source', 'target', 'weight'])
    
    def save_data(self, farmer_df: pd.DataFrame, output_path: str = './data'):
        """保存生成的数据"""
        import os
        os.makedirs(output_path, exist_ok=True)
        farmer_df.to_csv(f'{output_path}/farmer_attributes.csv', index=False)
        print(f"[OK] 农户数据已保存至 {output_path}/farmer_attributes.csv")
        print(f"  共生成 {len(farmer_df)} 个农户")
        print(f"  初始绿色施肥采纳率: {farmer_df['adoption_state'].mean():.2%}")


def load_config(config_path: str = 'config.yaml') -> Dict:
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


if __name__ == '__main__':
    # 测试数据生成
    config = load_config('../config.yaml')
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()
    
    print("\n=== 农户属性统计 ===")
    print(farmer_df.describe())
    print("\n=== 前5个农户样本 ===")
    print(farmer_df.head())
    
    generator.save_data(farmer_df)

