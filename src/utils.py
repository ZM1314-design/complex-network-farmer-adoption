"""
工具函数模块
"""
import os
import json
import pickle
import numpy as np
import pandas as pd
from typing import Dict, Any
import yaml


def ensure_dir(directory: str):
    """确保目录存在"""
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_json(data: Dict, filepath: str):
    """保存JSON文件"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_json(filepath: str) -> Dict:
    """加载JSON文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_pickle(obj: Any, filepath: str):
    """保存pickle文件"""
    with open(filepath, 'wb') as f:
        pickle.dump(obj, f)


def load_pickle(filepath: str) -> Any:
    """加载pickle文件"""
    with open(filepath, 'rb') as f:
        return pickle.load(f)


def load_yaml(filepath: str) -> Dict:
    """加载YAML配置"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def save_yaml(data: Dict, filepath: str):
    """保存YAML配置"""
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True)


def set_random_seed(seed: int = 42):
    """设置随机种子"""
    np.random.seed(seed)
    import random
    random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def compute_statistics(data: np.ndarray) -> Dict:
    """计算统计量"""
    return {
        'mean': float(np.mean(data)),
        'std': float(np.std(data)),
        'min': float(np.min(data)),
        'max': float(np.max(data)),
        'median': float(np.median(data)),
        'q25': float(np.percentile(data, 25)),
        'q75': float(np.percentile(data, 75))
    }


def moving_average(data: np.ndarray, window: int = 10) -> np.ndarray:
    """移动平均平滑"""
    return np.convolve(data, np.ones(window)/window, mode='valid')


def normalize_data(data: np.ndarray, method: str = 'minmax') -> np.ndarray:
    """
    数据归一化
    
    Args:
        data: 输入数据
        method: 'minmax' 或 'zscore'
    """
    if method == 'minmax':
        min_val = np.min(data)
        max_val = np.max(data)
        if max_val - min_val == 0:
            return np.zeros_like(data)
        return (data - min_val) / (max_val - min_val)
    elif method == 'zscore':
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return np.zeros_like(data)
        return (data - mean) / std
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def create_experiment_summary(config: Dict, results: Dict, output_path: str):
    """
    创建实验摘要报告
    """
    summary = {
        'experiment_name': config.get('experiment_name', 'unnamed'),
        'timestamp': pd.Timestamp.now().isoformat(),
        'config': config,
        'results': results
    }
    
    save_json(summary, output_path)
    
    # 同时生成文本报告
    txt_path = output_path.replace('.json', '.txt')
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("=" * 70 + "\n")
        f.write("实验摘要报告\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("实验配置:\n")
        f.write(f"  农户数量: {config['network']['num_farmers']}\n")
        f.write(f"  训练轮数: {config['simulation']['num_episodes']}\n")
        f.write(f"  每轮步数: {config['simulation']['max_steps']}\n\n")
        
        f.write("关键结果:\n")
        for key, value in results.items():
            if isinstance(value, float):
                f.write(f"  {key}: {value:.4f}\n")
            else:
                f.write(f"  {key}: {value}\n")
        
        f.write("\n" + "=" * 70 + "\n")


def compare_experiments(exp_paths: list, output_path: str):
    """
    对比多个实验结果
    
    Args:
        exp_paths: 实验摘要JSON文件路径列表
        output_path: 输出对比表格路径
    """
    comparison = []
    
    for path in exp_paths:
        summary = load_json(path)
        exp_name = os.path.basename(path).replace('.json', '')
        
        results = summary.get('results', {})
        row = {'experiment': exp_name}
        row.update(results)
        comparison.append(row)
    
    df = pd.DataFrame(comparison)
    df.to_csv(output_path, index=False)
    
    print(f"✓ 对比结果已保存至: {output_path}")
    print(df)
    
    return df


def plot_comparison(df: pd.DataFrame, metrics: list, output_path: str):
    """
    绘制对比图表
    
    Args:
        df: 对比数据框
        metrics: 要对比的指标列表
        output_path: 输出图表路径
    """
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, len(metrics), figsize=(5*len(metrics), 5))
    
    if len(metrics) == 1:
        axes = [axes]
    
    for idx, metric in enumerate(metrics):
        if metric in df.columns:
            axes[idx].bar(df['experiment'], df[metric], alpha=0.7, color='steelblue')
            axes[idx].set_ylabel(metric, fontsize=12)
            axes[idx].set_title(f'{metric} Comparison', fontsize=13)
            axes[idx].tick_params(axis='x', rotation=45)
            axes[idx].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"✓ 对比图表已保存至: {output_path}")


if __name__ == '__main__':
    # 测试工具函数
    print("工具函数测试:")
    
    # 测试统计
    data = np.random.randn(100)
    stats = compute_statistics(data)
    print("\n统计量:")
    for k, v in stats.items():
        print(f"  {k}: {v:.4f}")
    
    # 测试归一化
    normalized = normalize_data(data, method='minmax')
    print(f"\n归一化后范围: [{normalized.min():.4f}, {normalized.max():.4f}]")

