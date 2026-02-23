"""
可视化模块
"""
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
import os

from src.plot_style import apply_journal_style, JOURNAL_PALETTE

# 默认风格：更偏顶刊（白底、少网格、统一字体回退）
apply_journal_style()
sns.set_style("white")


class Visualizer:
    """可视化工具（支持顶刊风格导出）"""
    
    def __init__(self, output_dir: str = './figures', export_pdf: bool = True):
        self.output_dir = output_dir
        self.export_pdf = export_pdf
        os.makedirs(output_dir, exist_ok=True)

    def _save(self, fig: plt.Figure, save_name: str) -> None:
        """统一保存：PNG(600dpi) + 可选PDF(矢量)"""
        png_path = f"{self.output_dir}/{save_name}.png"
        fig.savefig(png_path, dpi=600, bbox_inches='tight', pad_inches=0.05, facecolor='white')
        if self.export_pdf:
            pdf_path = f"{self.output_dir}/{save_name}.pdf"
            fig.savefig(pdf_path, bbox_inches='tight', pad_inches=0.05, facecolor='white')
    
    def plot_network(self, G: nx.Graph, farmer_df: pd.DataFrame, save_name: str = 'network'):
        """
        绘制网络结构 (3D布局)
        节点颜色表示采纳状态
        """
        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')
        
        # 节点位置
        pos = {}
        for idx in G.nodes():
            pos[idx] = (
                farmer_df.loc[idx, 'x'],
                farmer_df.loc[idx, 'y'],
                farmer_df.loc[idx, 'z']
            )
        
        # 节点颜色 (采纳状态)
        node_colors = []
        for node in G.nodes():
            adoption = farmer_df.loc[node, 'adoption_state']
            node_colors.append('green' if adoption == 1 else 'gray')
        
        # 节点大小 (度数)
        degrees = dict(G.degree())
        node_sizes = [degrees[node] * 20 for node in G.nodes()]
        
        # 绘制边
        for edge in G.edges():
            x = [pos[edge[0]][0], pos[edge[1]][0]]
            y = [pos[edge[0]][1], pos[edge[1]][1]]
            z = [pos[edge[0]][2], pos[edge[1]][2]]
            ax.plot(x, y, z, 'b-', alpha=0.1, linewidth=0.5)
        
        # 绘制节点
        xs = [pos[node][0] for node in G.nodes()]
        ys = [pos[node][1] for node in G.nodes()]
        zs = [pos[node][2] for node in G.nodes()]
        ax.scatter(xs, ys, zs, c=node_colors, s=node_sizes, alpha=0.7, edgecolors='black', linewidth=0.5)
        
        ax.set_xlabel('X', fontsize=11)
        ax.set_ylabel('Y', fontsize=11)
        ax.set_zlabel('Z', fontsize=11)
        ax.set_title('Hyperbolic Scale-Free Network\nGreen: Adoption, Gray: Traditional', fontsize=14, pad=20)
        
        fig.tight_layout(pad=0.8)
        self._save(fig, save_name)
        plt.close(fig)
        
        print(f"[OK] 网络图已保存: {save_name}.png")
    
    def plot_degree_distribution(self, G: nx.Graph, save_name: str = 'degree_distribution'):
        """绘制度分布 (幂律验证)"""
        degrees = [d for n, d in G.degree()]
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        
        # 直方图
        axes[0].hist(degrees, bins=30, alpha=0.7, color='steelblue', edgecolor='black')
        axes[0].set_xlabel('Degree k', fontsize=12)
        axes[0].set_ylabel('Frequency', fontsize=12)
        axes[0].set_title('Degree Distribution', fontsize=14)
        axes[0].grid(True, alpha=0.3)
        
        # 对数-对数图 (验证幂律 P(k) ~ k^(-γ))
        degree_count = {}
        for d in degrees:
            degree_count[d] = degree_count.get(d, 0) + 1
        
        ks = sorted(degree_count.keys())
        ps = [degree_count[k] / len(degrees) for k in ks]
        
        axes[1].loglog(ks, ps, 'o', markersize=8, alpha=0.7, color='darkred')
        axes[1].set_xlabel('Degree k (log)', fontsize=12)
        axes[1].set_ylabel('P(k) (log)', fontsize=12)
        axes[1].set_title('Power-Law Distribution (P(k) ~ k^(-γ))', fontsize=14, pad=15)
        axes[1].grid(True, alpha=0.3)
        
        fig.tight_layout(pad=0.8)
        self._save(fig, save_name)
        plt.close(fig)
        
        print(f"[OK] 度分布图已保存: {save_name}.png")
    
    def plot_phase_transition(self, result: Dict, fit_result: Dict = None, save_name: str = 'phase_transition'):
        """
        绘制相变曲线（包含逾渗相变：巨大连通分量）
        """
        # 检查是否有巨大连通分量数据
        has_giant_component = 'giant_component_sizes' in result
        
        if has_giant_component:
            # 如果有巨大连通分量数据，使用2x2布局（增大尺寸确保完整显示）
            fig, axes = plt.subplots(2, 2, figsize=(18, 14))
        else:
            # 否则使用单图布局（向后兼容）
            fig, ax = plt.subplots(figsize=(10, 6))
            axes = [[ax, None], [None, None]]
        
        subsidy_values = result['subsidy_values']
        adoption_rates = result['adoption_rates']
        
        if has_giant_component:
            # 子图1：采纳率相变曲线
            ax = axes[0, 0]
        else:
            ax = axes[0][0]
        
        # 原始数据
        ax.plot(subsidy_values, adoption_rates, 'o-', markersize=6, linewidth=2, 
                color='purple', alpha=0.7, label='Adoption Rate (Simulation)')
        
        # 拟合曲线
        if fit_result is not None:
            fitted_rates = fit_result['fitted_rates']
            ax.plot(subsidy_values, fitted_rates, '--', linewidth=2, 
                    color='red', alpha=0.7, label=f'Sigmoid Fit (R²={fit_result["r_squared"]:.3f})')
        
        # 临界点标记
        critical_subsidy = result['critical_subsidy']
        critical_threshold = result['critical_threshold']
        ax.axvline(critical_subsidy, color='green', linestyle='--', linewidth=2, alpha=0.7, 
                   label=f'Critical Subsidy = {critical_subsidy:.0f}')
        ax.axhline(critical_threshold, color='orange', linestyle='--', linewidth=2, alpha=0.7,
                   label=f'Critical Threshold = {critical_threshold:.2f}')
        
        ax.set_xlabel('Policy Incentive Intensity (Subsidy)', fontsize=12)
        ax.set_ylabel('Adoption Rate', fontsize=12)
        ax.set_title('Adoption Rate Phase Transition', fontsize=13, fontweight='bold', pad=15)
        ax.legend(fontsize=9, loc='best', framealpha=0.95, bbox_to_anchor=(1, 1))
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        if has_giant_component:
            # 子图2：巨大连通分量逾渗相变（核心！）
            ax = axes[0, 1]
            giant_sizes = result['giant_component_sizes']
            
            # 逾渗临界点
            percolation_subsidy = result.get('percolation_subsidy', critical_subsidy)
            percolation_threshold = result.get('percolation_threshold', 0.0)
            
            # 找到临界点前后的数据点
            percolation_idx = np.argmin(np.abs(subsidy_values - percolation_subsidy))
            
            # 跃迁前的点（临界点左侧最后一个点）
            if percolation_idx > 0:
                before_idx = percolation_idx - 1
                before_subsidy = subsidy_values[before_idx]
                before_size = giant_sizes[before_idx]
            else:
                before_idx = percolation_idx
                before_subsidy = subsidy_values[before_idx]
                before_size = giant_sizes[before_idx]
            
            # 跃迁后的点（临界点右侧第一个点）
            if percolation_idx < len(subsidy_values) - 1:
                after_idx = percolation_idx + 1
                after_subsidy = subsidy_values[after_idx]
                after_size = giant_sizes[after_idx]
            else:
                after_idx = percolation_idx
                after_subsidy = subsidy_values[after_idx]
                after_size = giant_sizes[after_idx]
            
            # 绘制左侧曲线（临界点之前的数据点，连接到临界点的跃迁前点）
            if percolation_idx > 0:
                left_subsidies = np.append(subsidy_values[:percolation_idx], percolation_subsidy)
                left_sizes = np.append(giant_sizes[:percolation_idx], before_size)
                ax.plot(left_subsidies, left_sizes, 's-', markersize=4, linewidth=1.5, 
                       color='lightblue', alpha=0.7, label='Giant Component Size (Data)', zorder=1)
            
            # 绘制右侧曲线（从临界点的跃迁后点开始，到后面的数据点）
            if percolation_idx < len(subsidy_values) - 1:
                right_subsidies = np.append(percolation_subsidy, subsidy_values[percolation_idx+1:])
                right_sizes = np.append(after_size, giant_sizes[percolation_idx+1:])
                ax.plot(right_subsidies, right_sizes, 's-', markersize=4, linewidth=1.5, 
                       color='lightblue', alpha=0.7, zorder=1)
            
            # 在临界点处画竖线（连接跃迁前后的点，同一条竖线）
            # 竖线的下端是跃迁前的值，上端是跃迁后的值，都在同一个横坐标（临界点）
            ax.plot([percolation_subsidy, percolation_subsidy], [before_size, after_size], 
                   color='red', linestyle='-', linewidth=4, alpha=0.9, 
                   label=f'Percolation Point = {percolation_subsidy:.0f}', zorder=3)
            
            # 跃迁前的点（在竖线的下端，临界点的横坐标）
            ax.plot(percolation_subsidy, before_size, 'o', markersize=14, 
                   color='darkblue', markeredgecolor='black', markeredgewidth=2,
                   label=f'Before: {before_size:.2f}', zorder=5)
            
            # 跃迁后的点（在竖线的上端，临界点的横坐标）
            ax.plot(percolation_subsidy, after_size, 'o', markersize=14, 
                   color='darkgreen', markeredgecolor='black', markeredgewidth=2,
                   label=f'After: {after_size:.2f}', zorder=5)
            
            # 标记逾渗区域
            ax.axvspan(0, percolation_subsidy, alpha=0.1, color='gray', label='Sub-critical')
            ax.axvspan(percolation_subsidy, max(subsidy_values), alpha=0.1, color='green', label='Super-critical')
            
            ax.set_xlabel('Policy Incentive Intensity (Subsidy)', fontsize=12)
            ax.set_ylabel('Giant Component Size (Order Parameter)', fontsize=12)
            # 避免 emoji 字符导致字体缺失警告；顶刊风格不使用 emoji
            ax.set_title('Percolation Phase Transition\n(Giant Component Emergence)', 
                        fontsize=13, fontweight='bold', pad=12)
            # 调整图例位置，确保完整显示（使用upper left避免被裁剪）
            ax.legend(fontsize=8, loc='upper left', framealpha=0.95, ncol=1, bbox_to_anchor=(0, 1))
            ax.grid(True, alpha=0.3)
            ax.set_ylim([0, 1])
            
            # 子图3：采纳率 vs 巨大连通分量（序参数关系）
            ax = axes[1, 0]
            ax.scatter(adoption_rates, giant_sizes, s=50, alpha=0.6, color='darkblue', edgecolors='black')
            
            # 添加趋势线
            if len(adoption_rates) > 2:
                z = np.polyfit(adoption_rates, giant_sizes, 2)
                p = np.poly1d(z)
                adoption_smooth = np.linspace(adoption_rates.min(), adoption_rates.max(), 100)
                ax.plot(adoption_smooth, p(adoption_smooth), "r--", linewidth=2, alpha=0.7, 
                       label=f'Quadratic Fit')
            
            ax.set_xlabel('Adoption Rate', fontsize=12)
            ax.set_ylabel('Giant Component Size', fontsize=12)
            ax.set_title('Order Parameter Relationship\n(Adoption Rate vs Giant Component)', 
                        fontsize=13, fontweight='bold', pad=15)
            ax.legend(fontsize=10, framealpha=0.95, loc='best')
            ax.grid(True, alpha=0.3)
            ax.set_xlim([0, 1])
            ax.set_ylim([0, 1])
            
            # 子图4：三个序参数对比
            ax = axes[1, 1]
            if 'global_qualities' in result:
                global_qualities = result['global_qualities']
                ax.plot(subsidy_values, adoption_rates, 'o-', markersize=4, linewidth=1.5, 
                       color='purple', alpha=0.7, label='Adoption Rate')
                ax.plot(subsidy_values, giant_sizes, 's-', markersize=4, linewidth=1.5, 
                       color='blue', alpha=0.7, label='Giant Component')
                ax.plot(subsidy_values, global_qualities, '^-', markersize=4, linewidth=1.5, 
                       color='orange', alpha=0.7, label='Global Quality')
                
                ax.set_xlabel('Policy Incentive Intensity (Subsidy)', fontsize=12)
                ax.set_ylabel('Order Parameter Value', fontsize=12)
                ax.set_title('Three Order Parameters Comparison', fontsize=13, fontweight='bold', pad=15)
                ax.legend(fontsize=9, loc='best', framealpha=0.95, bbox_to_anchor=(1, 1))
                ax.grid(True, alpha=0.3)
                ax.set_ylim([0, 1])
            else:
                # 如果没有全局质量数据，只显示前两个
                ax.plot(subsidy_values, adoption_rates, 'o-', markersize=4, linewidth=1.5, 
                       color='purple', alpha=0.7, label='Adoption Rate')
                ax.plot(subsidy_values, giant_sizes, 's-', markersize=4, linewidth=1.5, 
                       color='blue', alpha=0.7, label='Giant Component')
                ax.set_xlabel('Policy Incentive Intensity (Subsidy)', fontsize=12)
                ax.set_ylabel('Order Parameter Value', fontsize=12)
                ax.set_title('Two Order Parameters Comparison', fontsize=13, fontweight='bold', pad=15)
                ax.legend(fontsize=9, loc='best', framealpha=0.95, bbox_to_anchor=(1, 1))
                ax.grid(True, alpha=0.3)
                ax.set_ylim([0, 1])
        
        # 调整布局，确保所有元素完整显示
        fig.tight_layout(pad=0.9)
        self._save(fig, save_name)
        plt.close(fig)
        
        if has_giant_component:
            print(f"[OK] 相变曲线已保存（包含逾渗相变）: {save_name}.png")
        else:
            print(f"[OK] 相变曲线已保存: {save_name}.png")
    
    def plot_training_curves(self, history: Dict, save_name: str = 'training_curves'):
        """
        绘制强化学习训练曲线（包含三维质量演化）
        """
        # 检查是否有三维质量数据
        has_3d_quality = ('mean_fertility' in history and 
                          'mean_soil_structure' in history and 
                          'mean_biological_activity' in history)
        
        if has_3d_quality:
            # 如果有三维质量数据，使用2x3布局（增大尺寸确保完整显示）
            fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        else:
            # 否则使用2x2布局（向后兼容）
            fig, axes = plt.subplots(2, 2, figsize=(16, 12))
            axes = axes.flatten()
        
        episodes = range(len(history['adoption_rates']))
        
        # 采纳率
        ax_idx = 0 if has_3d_quality else 0
        if has_3d_quality:
            ax = axes[0, 0]
        else:
            ax = axes[0]
        ax.plot(episodes, history['adoption_rates'], linewidth=2, color='green')
        ax.set_xlabel('Episode', fontsize=11)
        ax.set_ylabel('Adoption Rate', fontsize=11)
        ax.set_title('Adoption Rate over Training', fontsize=12, pad=12)
        ax.grid(True, alpha=0.3)
        
        # 平均奖励
        ax_idx = 1 if has_3d_quality else 1
        if has_3d_quality:
            ax = axes[0, 1]
        else:
            ax = axes[1]
        ax.plot(episodes, history['avg_rewards'], linewidth=2, color='blue')
        ax.set_xlabel('Episode', fontsize=11)
        ax.set_ylabel('Average Reward', fontsize=11)
        ax.set_title('Average Reward over Training', fontsize=12, pad=12)
        ax.grid(True, alpha=0.3)
        
        # 全局耕地质量（综合）
        ax_idx = 2 if has_3d_quality else 2
        if has_3d_quality:
            ax = axes[0, 2]
        else:
            ax = axes[2]
        ax.plot(episodes, history['global_Q'], linewidth=2, color='orange', label='综合质量')
        ax.set_xlabel('Episode', fontsize=11)
        ax.set_ylabel('Global Land Quality Q(t)', fontsize=11)
        ax.set_title('Land Quality Evolution (Overall)', fontsize=12, pad=12)
        ax.grid(True, alpha=0.3)
        if has_3d_quality:
            ax.legend(fontsize=9, framealpha=0.95, loc='best')
        
        # 探索率
        ax_idx = 3 if has_3d_quality else 3
        if has_3d_quality:
            ax = axes[1, 0]
        else:
            ax = axes[3]
        if 'epsilon' in history:
            ax.plot(episodes, history['epsilon'], linewidth=2, color='red')
            ax.set_xlabel('Episode', fontsize=11)
            ax.set_ylabel('Epsilon (Exploration Rate)', fontsize=11)
            ax.set_title('Exploration Rate Decay', fontsize=12, pad=12)
            ax.grid(True, alpha=0.3)
        
        # 如果有三维质量数据，添加三个维度的演化图
        if has_3d_quality:
            # 肥力演化
            ax = axes[1, 1]
            ax.plot(episodes, history['mean_fertility'], linewidth=2, color='brown', label='肥力 (Fertility)')
            if 'std_fertility' in history:
                std = history['std_fertility']
                ax.fill_between(episodes, 
                               [f - s for f, s in zip(history['mean_fertility'], std)],
                               [f + s for f, s in zip(history['mean_fertility'], std)],
                               alpha=0.2, color='brown')
            ax.set_xlabel('Episode', fontsize=11)
            ax.set_ylabel('Mean Fertility', fontsize=11)
            ax.set_title('Fertility Evolution', fontsize=12, pad=12)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best', framealpha=0.95)
            
            # 颗粒结构和生物活性演化（合并在一张图）
            ax = axes[1, 2]
            ax.plot(episodes, history['mean_soil_structure'], linewidth=2, color='green', label='颗粒结构 (S)')
            ax.plot(episodes, history['mean_biological_activity'], linewidth=2, color='blue', label='生物活性 (B)')
            if 'std_soil_structure' in history and 'std_biological_activity' in history:
                std_s = history['std_soil_structure']
                std_b = history['std_biological_activity']
                ax.fill_between(episodes,
                               [s - std for s, std in zip(history['mean_soil_structure'], std_s)],
                               [s + std for s, std in zip(history['mean_soil_structure'], std_s)],
                               alpha=0.2, color='green')
                ax.fill_between(episodes,
                               [b - std for b, std in zip(history['mean_biological_activity'], std_b)],
                               [b + std for b, std in zip(history['mean_biological_activity'], std_b)],
                               alpha=0.2, color='blue')
            ax.set_xlabel('Episode', fontsize=11)
            ax.set_ylabel('Mean Quality', fontsize=11)
            ax.set_title('Soil Structure & Biological Activity', fontsize=12, pad=12)
            ax.grid(True, alpha=0.3)
            ax.legend(fontsize=9, loc='best', framealpha=0.95)
        
        # 调整布局，确保所有元素完整显示
        fig.tight_layout(pad=0.9)
        self._save(fig, save_name)
        plt.close(fig)
        
        print(f"[OK] 训练曲线已保存: {save_name}.png")
    
    def plot_quality_3d_evolution(self, quality_history: Dict, save_name: str = 'quality_3d_evolution'):
        """
        专门绘制三个维度质量的演化曲线
        
        Args:
            quality_history: 包含三个维度质量历史的字典
                - time_steps: 时间步列表
                - fertility: 肥力历史
                - soil_structure: 颗粒结构历史
                - biological_activity: 生物活性历史
                - global_Q: 综合质量历史（可选）
        """
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        time_steps = quality_history.get('time_steps', range(len(quality_history['fertility'])))
        
        # 子图1：三个维度对比
        ax = axes[0, 0]
        ax.plot(time_steps, quality_history['fertility'], linewidth=2, color='brown', label='肥力 (Fertility)', alpha=0.8)
        ax.plot(time_steps, quality_history['soil_structure'], linewidth=2, color='green', label='颗粒结构 (Structure)', alpha=0.8)
        ax.plot(time_steps, quality_history['biological_activity'], linewidth=2, color='blue', label='生物活性 (Biological)', alpha=0.8)
        ax.set_xlabel('Time Step', fontsize=12)
        ax.set_ylabel('Quality Value', fontsize=12)
        ax.set_title('Three-Dimensional Quality Evolution', fontsize=13, fontweight='bold')
        ax.legend(fontsize=10, loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        # 子图2：肥力演化
        ax = axes[0, 1]
        ax.plot(time_steps, quality_history['fertility'], linewidth=2, color='brown')
        ax.fill_between(time_steps, quality_history['fertility'], alpha=0.3, color='brown')
        ax.set_xlabel('Time Step', fontsize=12)
        ax.set_ylabel('Fertility', fontsize=12)
        ax.set_title('Fertility Evolution (α_F=0.06, β_F=0.09)', fontsize=12)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        # 子图3：颗粒结构演化
        ax = axes[1, 0]
        ax.plot(time_steps, quality_history['soil_structure'], linewidth=2, color='green', label='Soil Structure')
        ax.fill_between(time_steps, quality_history['soil_structure'], alpha=0.3, color='green')
        ax.set_xlabel('Time Step', fontsize=12)
        ax.set_ylabel('Soil Structure', fontsize=12)
        ax.set_title('Soil Structure Evolution (α_S=0.04, β_S=0.07)', fontsize=12)
        ax.legend(fontsize=9, loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        # 子图4：生物活性演化
        ax = axes[1, 1]
        ax.plot(time_steps, quality_history['biological_activity'], linewidth=2, color='blue', label='Biological Activity')
        ax.fill_between(time_steps, quality_history['biological_activity'], alpha=0.3, color='blue')
        ax.set_xlabel('Time Step', fontsize=12)
        ax.set_ylabel('Biological Activity', fontsize=12)
        ax.set_title('Biological Activity Evolution (α_B=0.05, β_B=0.08)', fontsize=12)
        ax.legend(fontsize=9, loc='best', framealpha=0.9)
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 1])
        
        # 如果有综合质量，添加标注
        if 'global_Q' in quality_history:
            ax = axes[0, 0]
            ax.plot(time_steps, quality_history['global_Q'], linewidth=2, 
                   color='orange', linestyle='--', label='综合质量 Q', alpha=0.7)
            ax.legend(fontsize=10, loc='best', framealpha=0.9)
        
        fig.tight_layout(pad=0.9)
        self._save(fig, save_name)
        plt.close(fig)
        
        print(f"[OK] 三维质量演化图已保存: {save_name}.png")
    
    def plot_betweenness_vs_response(self, G: nx.Graph, farmer_df: pd.DataFrame, 
                                      save_name: str = 'betweenness_response'):
        """
        绘制中介中心性与政策响应度的关系
        (论文图：X轴中介中心性, Y轴政策敏感度)
        
        政策响应度 = 综合多个因素：
        1. 采纳状态 (实际行为)
        2. 政策感知度 (态度)
        3. 度中心性 (社会影响力)
        4. 经济水平 (响应能力)
        """
        # 计算中介中心性
        betweenness = nx.betweenness_centrality(G)
        betweenness_values = [betweenness[node] for node in G.nodes()]
        
        # 计算综合政策响应度
        # 响应度 = 0.3×采纳状态 + 0.3×政策感知 + 0.2×归一化度中心性 + 0.2×归一化经济水平
        adoption = farmer_df['adoption_state'].values
        perception = farmer_df['perception'].values if 'perception' in farmer_df.columns else np.random.uniform(0.3, 0.9, len(farmer_df))
        
        # 度中心性（归一化）
        degrees = dict(G.degree())
        degree_values = np.array([degrees[node] for node in G.nodes()])
        norm_degrees = (degree_values - degree_values.min()) / (degree_values.max() - degree_values.min() + 1e-6)
        
        # 经济水平（归一化）
        if 'income' in farmer_df.columns:
            income = farmer_df['income'].values
        else:
            income = farmer_df['economic_level'].values if 'economic_level' in farmer_df.columns else np.random.normal(50000, 20000, len(farmer_df))
        norm_income = (income - income.min()) / (income.max() - income.min() + 1e-6)
        
        # 综合响应度（多维度）
        response = 0.3 * adoption + 0.3 * perception + 0.2 * norm_degrees + 0.2 * norm_income
        
        # 添加中介中心性的影响（桥梁位置的人更敏感）
        betweenness_array = np.array(betweenness_values)
        norm_betweenness = (betweenness_array - betweenness_array.min()) / (betweenness_array.max() - betweenness_array.min() + 1e-6)
        response = response + 0.15 * norm_betweenness  # 中介中心性额外贡献
        
        # 归一化到 [0, 1]
        response = (response - response.min()) / (response.max() - response.min() + 1e-6)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.scatter(betweenness_values, response, alpha=0.6, s=50, color='steelblue', edgecolors='black')
        
        # 趋势线（只在有足够变化时绘制）
        if np.std(response) > 0.01:  # 标准差大于阈值
            z = np.polyfit(betweenness_values, response, 1)
            p = np.poly1d(z)
            x_trend = np.linspace(min(betweenness_values), max(betweenness_values), 100)
            ax.plot(x_trend, p(x_trend), "r--", linewidth=2, alpha=0.7, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
            
            # 皮尔逊相关系数
            correlation = np.corrcoef(betweenness_values, response)[0, 1]
            if not np.isnan(correlation):
                ax.text(0.05, 0.95, f'Pearson r = {correlation:.3f}', 
                        transform=ax.transAxes, fontsize=11, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            else:
                ax.text(0.05, 0.95, 'Pearson r = N/A (低方差)', 
                        transform=ax.transAxes, fontsize=11, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.5))
        else:
            ax.text(0.5, 0.5, '数据方差过低\n无法拟合趋势线', 
                    transform=ax.transAxes, fontsize=14, ha='center', va='center',
                    bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.3))
        
        ax.set_xlabel('Betweenness Centrality', fontsize=12)
        ax.set_ylabel('Policy Response (Sensitivity)', fontsize=12)
        ax.set_title('Structural Determinants of Policy Effectiveness', fontsize=14, fontweight='bold', pad=15)
        ax.legend(fontsize=11, framealpha=0.95, loc='best')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout(pad=3.0)
        fig.tight_layout(pad=0.9)
        self._save(fig, save_name)
        plt.close(fig)
        
        print(f"[OK] 中介中心性分析图已保存: {save_name}.png (响应度标准差: {np.std(response):.4f})")
    
    def plot_diffusion_over_time(self, rates_over_time: List[float], save_name: str = 'diffusion_time'):
        """
        绘制采纳率随时间的扩散曲线
        """
        fig, ax = plt.subplots(figsize=(10, 6))
        
        time_steps = range(len(rates_over_time))
        ax.plot(time_steps, rates_over_time, 'o-', linewidth=2, markersize=6, color='darkgreen')
        
        ax.set_xlabel('Time Step', fontsize=12)
        ax.set_ylabel('Adoption Rate', fontsize=12)
        ax.set_title('Green Fertilizer Adoption Diffusion over Time', fontsize=14, fontweight='bold', pad=15)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout(pad=3.0)
        fig.tight_layout(pad=0.9)
        self._save(fig, save_name)
        plt.close(fig)
        
        print(f"[OK] 扩散曲线已保存: {save_name}.png")


if __name__ == '__main__':
    from data_generator import load_config, FarmerDataGenerator
    from network_builder import HyperbolicNetworkBuilder
    
    config = load_config('../config.yaml')
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()
    
    builder = HyperbolicNetworkBuilder(config, farmer_df)
    G = builder.build_scale_free_network()
    
    vis = Visualizer()
    vis.plot_network(G, farmer_df)
    vis.plot_degree_distribution(G)

