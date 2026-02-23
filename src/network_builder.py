"""
网络构建模块：基于双曲几何生成复杂网络
"""
import numpy as np
import networkx as nx
import pandas as pd
from typing import Dict, List, Tuple
from scipy.spatial.distance import cdist


class HyperbolicNetworkBuilder:
    """双曲几何网络构建器"""
    
    def __init__(self, config: Dict, farmer_df: pd.DataFrame):
        self.config = config
        self.farmer_df = farmer_df
        self.num_farmers = len(farmer_df)
        self.network_config = config['network']
        
    def compute_hyperbolic_distance(self, i: int, j: int) -> float:
        """
        计算双曲空间中两个节点的距离
        基于论文中的公式：d_ij = ar*cosh(1 + (2||x_i - x_j||^2) / ((1-||x_i||^2)(1-||x_j||^2)))
        
        简化版本：当 ||x_i|| 和 ||x_j|| << 1 时，近似为 P(i↔j) ∝ c·e^(-ζ·d_ij)
        """
        xi = self.farmer_df.loc[i, ['x', 'y', 'z']].values
        xj = self.farmer_df.loc[j, ['x', 'y', 'z']].values
        
        norm_i = np.linalg.norm(xi)
        norm_j = np.linalg.norm(xj)
        diff_norm = np.linalg.norm(xi - xj)
        
        # 避免除零
        denominator = (1 - norm_i**2) * (1 - norm_j**2)
        if denominator < 1e-10:
            return 1e10  # 很大的距离
        
        # 双曲余弦距离
        arg = 1 + (2 * diff_norm**2) / denominator
        arg = np.clip(arg, 1, 1e10)  # 确保在定义域内
        
        # 简化：ar 取5km左右，ζ取2.5
        ar = 5.0
        distance = ar * np.arccosh(arg)
        
        return distance
    
    def connection_probability(self, distance: float) -> float:
        """
        连边概率：P(i↔j) = exp(-ζ·d_ij)
        ζ 是空间衰减指数，论文中约为 2.5
        """
        zeta = 2.5
        prob = np.exp(-zeta * distance / 5.0)  # 归一化
        return prob
    
    def build_scale_free_network(self) -> nx.Graph:
        """
        构建无标度网络 (双曲几何模型)
        节点度分布 P(k) ~ k^(-γ)，γ ≈ 2.5
        """
        G = nx.Graph()
        
        # 添加节点及属性
        for idx, row in self.farmer_df.iterrows():
            G.add_node(
                idx,
                economic=row['economic_level'],
                education=row['education'],
                risk_tolerance=row['risk_tolerance'],
                env_awareness=row['env_awareness'],
                adoption=row['adoption_state'],
                land_quality=row['land_quality'],
                x=row['x'],
                y=row['y'],
                z=row['z']
            )
        
        # 基于双曲距离和概率连边
        target_edges = int(self.num_farmers * self.network_config['avg_degree'] / 2)
        edge_count = 0
        
        print(f"正在构建网络，目标边数: {target_edges}...")
        
        # 计算所有节点对的距离 (优化：只计算上三角)
        edges_to_add = []
        for i in range(self.num_farmers):
            for j in range(i+1, self.num_farmers):
                distance = self.compute_hyperbolic_distance(i, j)
                prob = self.connection_probability(distance)
                
                # 按概率决定是否连边
                if np.random.rand() < prob:
                    weight = 1.0 / (1.0 + distance)  # 距离越近权重越大
                    edges_to_add.append((i, j, weight))
                    edge_count += 1
                    
                    if edge_count >= target_edges:
                        break
            
            if edge_count >= target_edges:
                break
            
            if i % 50 == 0:
                print(f"  进度: {i}/{self.num_farmers}, 已添加边数: {edge_count}")
        
        # 批量添加边
        G.add_weighted_edges_from(edges_to_add)
        
        print(f"[OK] 网络构建完成: {G.number_of_nodes()} 节点, {G.number_of_edges()} 边")
        print(f"  平均度: {2*G.number_of_edges()/G.number_of_nodes():.2f}")
        
        return G
    
    def add_hyperedges(self, G: nx.Graph) -> Dict[int, List[int]]:
        """
        添加超边 (hyperedges) - 表示合作社、村子等多方协作
        超边比例 δ = 3ρ/(2+ρ)，其中 ρ 是临界阈值 ρ_c
        
        Returns:
            Dict: hyperedge_id -> [node_list]
        """
        hyperedge_ratio = self.network_config['hyperedge_ratio']
        num_hyperedges = int(self.num_farmers * hyperedge_ratio)
        
        hyperedges = {}
        
        # 策略：从高度数节点(hub)出发，形成超边
        degrees = dict(G.degree())
        sorted_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)
        
        for he_id in range(num_hyperedges):
            # 选择一个hub作为中心
            center_node = sorted_nodes[he_id % len(sorted_nodes)][0]
            
            # 获取其邻居，随机选择3-5个形成合作社
            neighbors = list(G.neighbors(center_node))
            if len(neighbors) >= 2:
                size = min(np.random.randint(3, 6), len(neighbors))
                members = np.random.choice(neighbors, size=size, replace=False).tolist()
                members.append(center_node)
                hyperedges[he_id] = members
        
        print(f"[OK] 添加了 {len(hyperedges)} 个超边 (合作社)")
        
        return hyperedges
    
    def add_family_village_links(self, G: nx.Graph):
        """
        添加家族/村子内的强连接
        论文：如果农户属于同一家族或村子，则以概率 p_k = N_k/N_g 添加超边
        
        简化实现：将空间上接近的节点视为同村，增加连边概率
        """
        # 基于3D坐标聚类，简单k-means
        from sklearn.cluster import KMeans
        
        coords = self.farmer_df[['x', 'y', 'z']].values
        num_villages = max(10, self.num_farmers // 50)  # 假设每村50人左右
        
        kmeans = KMeans(n_clusters=num_villages, random_state=42)
        self.farmer_df['village_id'] = kmeans.fit_predict(coords)
        
        # 村内增加连边
        for village_id in range(num_villages):
            village_members = self.farmer_df[
                self.farmer_df['village_id'] == village_id
            ].index.tolist()
            
            if len(village_members) < 2:
                continue
            
            # 村内任意两户有额外连边概率
            for i in range(len(village_members)):
                for j in range(i+1, len(village_members)):
                    node_i = village_members[i]
                    node_j = village_members[j]
                    
                    if not G.has_edge(node_i, node_j):
                        # 同村连边概率较高
                        if np.random.rand() < 0.3:
                            G.add_edge(node_i, node_j, weight=1.5)  # 更高权重
        
        print(f"[OK] 添加村内强连接，共 {num_villages} 个村子")
    
    def compute_network_metrics(self, G: nx.Graph) -> Dict:
        """计算网络指标"""
        metrics = {
            'num_nodes': G.number_of_nodes(),
            'num_edges': G.number_of_edges(),
            'avg_degree': 2 * G.number_of_edges() / G.number_of_nodes(),
            'density': nx.density(G),
            'num_components': nx.number_connected_components(G)
        }
        
        # 度分布
        degrees = [d for n, d in G.degree()]
        metrics['degree_mean'] = np.mean(degrees)
        metrics['degree_std'] = np.std(degrees)
        metrics['degree_max'] = np.max(degrees)
        
        # 聚类系数
        if G.number_of_edges() > 0:
            metrics['clustering'] = nx.average_clustering(G)
        else:
            metrics['clustering'] = 0
        
        return metrics
    
    def save_network(self, G: nx.Graph, hyperedges: Dict, output_path: str = './data'):
        """保存网络"""
        import os
        os.makedirs(output_path, exist_ok=True)
        
        # 保存边列表
        nx.write_edgelist(G, f'{output_path}/network_edges.txt', data=['weight'])
        
        # 保存超边
        with open(f'{output_path}/hyperedges.txt', 'w') as f:
            for he_id, members in hyperedges.items():
                f.write(f"{he_id}: {','.join(map(str, members))}\n")
        
        # 保存节点属性 (更新后的farmer_df)
        try:
            self.farmer_df.to_csv(f'{output_path}/farmer_attributes_with_network.csv', index=False)
        except PermissionError:
            # 如果文件被占用，尝试使用临时文件名
            import time
            temp_file = f'{output_path}/farmer_attributes_with_network_{int(time.time())}.csv'
            self.farmer_df.to_csv(temp_file, index=False)
            print(f"[警告] 原文件被占用，已保存到: {temp_file}")
        
        print(f"[OK] 网络已保存至 {output_path}/")


if __name__ == '__main__':
    from data_generator import load_config, FarmerDataGenerator
    
    config = load_config('../config.yaml')
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()
    
    builder = HyperbolicNetworkBuilder(config, farmer_df)
    G = builder.build_scale_free_network()
    builder.add_family_village_links(G)
    hyperedges = builder.add_hyperedges(G)
    
    metrics = builder.compute_network_metrics(G)
    print("\n=== 网络指标 ===")
    for k, v in metrics.items():
        print(f"{k}: {v}")
    
    builder.save_network(G, hyperedges)

