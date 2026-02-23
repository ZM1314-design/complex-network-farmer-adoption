"""policy_explainability.py

目标：把“RL 为什么有效”落成可复现的证据文件。

输出：
- results/policy_explainability.csv
  每行是一名农户在评估时刻的一个决策样本（state -> action -> reward分解）。
- results/policy_explainability_summary.json
  汇总统计：不同状态分组下的采纳率、奖励分解均值、相关性矩阵等。

说明：
- 不修改核心训练逻辑；通过加载训练后的模型参数并在同一环境中做一次前向评估。
- 当前仓库仅保存了 agent_0 的模型（models/agent_0_final.pth）。
  为了可解释性，我们使用该模型对所有农户做“共享策略评估”（policy sharing evaluation）。
  这不等价于真实训练时“每户一模型”，但可以回答：
  1) 模型更偏好在什么状态下选择绿色施肥；
  2) 奖励函数各分量如何驱动学习。

运行：
python3 scripts/policy_explainability.py --config config.yaml --subsidy 105 --steps 1

"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch

# 允许以脚本方式运行时正确导入项目模块：把项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generator import FarmerDataGenerator, load_config
from src.dynamics import AdoptionDynamics
from src.network_builder import HyperbolicNetworkBuilder
from src.rl_agent import DQNetwork


@dataclass
class RewardDecomposition:
    adoption_bonus: float
    economic_term: float
    policy_term: float
    social_term: float
    education_term: float
    voice_term: float
    total: float


def compute_reward_decomposition(
    *,
    config: Dict,
    farmer_id: int,
    action: int,
    dynamics: AdoptionDynamics,
    subsidy: float,
) -> RewardDecomposition:
    """复刻 FarmerAgent.compute_reward 的计算，但把每一项分开输出。

    注意：此处采用与源码一致的归一化口径（/10000,/1000,/500,/300）。
    """

    reward_cfg = config["reward"]
    lambda1 = float(reward_cfg["lambda1"])
    lambda2 = float(reward_cfg["lambda2"])
    lambda3 = float(reward_cfg["lambda3"])
    lambda4 = float(reward_cfg.get("lambda4", 0.3))
    lambda5 = float(reward_cfg.get("lambda5", 0.2))

    # 三维质量
    if {
        "fertility",
        "soil_structure",
        "biological_activity",
    }.issubset(dynamics.farmer_df.columns):
        fertility = float(dynamics.farmer_df.loc[farmer_id, "fertility"])
        soil_structure = float(dynamics.farmer_df.loc[farmer_id, "soil_structure"])
        biological_activity = float(dynamics.farmer_df.loc[farmer_id, "biological_activity"])
    else:
        land_quality = float(dynamics.farmer_df.loc[farmer_id, "land_quality"])
        fertility = soil_structure = biological_activity = land_quality

    policy_cfg = config["policy"]

    # 经济效益（元）
    if action == 1:
        yield_fertility = 1.0 + 0.5 * fertility
        yield_structure = 1.0 + 0.3 * soil_structure
        yield_biological = 1.0 + 0.2 * biological_activity
        yield_factor = yield_fertility * 0.5 + yield_structure * 0.3 + yield_biological * 0.2
        cost = float(policy_cfg["cost_green"]) - float(subsidy)
        economic_benefit = yield_factor * 10000.0 - cost
    else:
        yield_fertility = 1.0 + 0.3 * fertility
        yield_structure = 1.0 + 0.1 * soil_structure
        yield_biological = 1.0 + 0.05 * biological_activity
        yield_factor = yield_fertility * 0.6 + yield_structure * 0.2 + yield_biological * 0.2
        cost = float(policy_cfg["cost_traditional"])
        economic_benefit = yield_factor * 10000.0 - cost

    # 政策补贴（元）
    policy_reward = float(subsidy) if action == 1 else 0.0

    # 社会声誉（元）
    neighbors = list(dynamics.G.neighbors(farmer_id))
    if neighbors:
        neighbor_adoption = float(dynamics.farmer_df.loc[neighbors, "adoption_state"].mean())
        if action == 1:
            social_reputation = neighbor_adoption * 1000.0
        else:
            social_reputation = (1.0 - neighbor_adoption) * 500.0
    else:
        social_reputation = 0.0

    # 教育优先权（元）
    if action == 1:
        education_priority = (
            float(dynamics.farmer_df.loc[farmer_id, "education_priority"])
            if "education_priority" in dynamics.farmer_df.columns
            else 0.5
        )
        education_bonus = 500.0 * (1.0 + education_priority)
    else:
        education_bonus = 0.0

    # 话语权（元）
    if action == 1:
        political_voice = (
            float(dynamics.farmer_df.loc[farmer_id, "political_voice"])
            if "political_voice" in dynamics.farmer_df.columns
            else 0.3
        )
        voice_bonus = 300.0 * (1.0 + political_voice)
    else:
        voice_bonus = 0.0

    adoption_bonus = 50.0 if action == 1 else 0.0

    economic_term = lambda1 * (economic_benefit / 10000.0)
    policy_term = lambda2 * (policy_reward / 1000.0)
    social_term = lambda3 * (social_reputation / 1000.0)
    education_term = lambda4 * (education_bonus / 500.0)
    voice_term = lambda5 * (voice_bonus / 300.0)

    total = adoption_bonus + economic_term + policy_term + social_term + education_term + voice_term

    return RewardDecomposition(
        adoption_bonus=adoption_bonus,
        economic_term=float(economic_term),
        policy_term=float(policy_term),
        social_term=float(social_term),
        education_term=float(education_term),
        voice_term=float(voice_term),
        total=float(total),
    )


def load_shared_policy_net(model_path: str, state_dim: int = 12, action_dim: int = 2, hidden_dim: int = 64) -> DQNetwork:
    ckpt = torch.load(model_path, map_location="cpu")
    net = DQNetwork(state_dim=state_dim, action_dim=action_dim, hidden_dim=hidden_dim)
    net.load_state_dict(ckpt["policy_net"])
    net.eval()
    return net


def build_environment(config: Dict):
    generator = FarmerDataGenerator(config)
    farmer_df = generator.generate_farmer_attributes()

    builder = HyperbolicNetworkBuilder(config, farmer_df)
    G = builder.build_scale_free_network()
    builder.add_family_village_links(G)
    hyperedges = builder.add_hyperedges(G)

    dynamics = AdoptionDynamics(config, G, farmer_df, hyperedges)
    return farmer_df, G, hyperedges, dynamics


def get_state_vector_for_eval(dynamics: AdoptionDynamics, G, farmer_id: int) -> np.ndarray:
    """复刻 FarmerAgent.get_state_vector 的状态构造（不依赖 FarmerAgent 实例）。"""

    attrs = dynamics.farmer_df.loc[farmer_id]

    degree = float(G.degree[farmer_id])
    max_degree = max(dict(G.degree()).values()) if len(G) > 0 else 1
    social_influence = degree / max_degree if max_degree > 0 else 0.0

    neighbors = list(G.neighbors(farmer_id))
    neighbor_adoption = float(dynamics.farmer_df.loc[neighbors, "adoption_state"].mean()) if neighbors else 0.0

    fertility = float(attrs.get("fertility", attrs.get("land_quality", 0.5)))
    soil_structure = float(attrs.get("soil_structure", attrs.get("land_quality", 0.5)))
    biological_activity = float(attrs.get("biological_activity", attrs.get("land_quality", 0.5)))

    myopia = float(attrs.get("myopia", 0.5))
    education_priority = float(attrs.get("education_priority", 0.5))
    political_voice = float(attrs.get("political_voice", 0.3))

    state = np.array(
        [
            float(attrs["economic_level"]) / 100000.0,
            social_influence,
            float(attrs["policy_perception"]),
            float(attrs["risk_tolerance"]),
            fertility,
            soil_structure,
            biological_activity,
            neighbor_adoption,
            float(dynamics.global_Q),
            myopia,
            education_priority,
            political_voice,
        ],
        dtype=np.float32,
    )

    return state


def evaluate_policy(
    *,
    config: Dict,
    model_path: str,
    subsidy: float,
    steps: int,
    output_csv: str,
    output_summary_json: str,
):
    farmer_df, G, hyperedges, dynamics = build_environment(config)

    net = load_shared_policy_net(
        model_path,
        state_dim=12,
        action_dim=2,
        hidden_dim=int(config["rl"]["hidden_dim"]),
    )

    rows: List[Dict] = []

    for t in range(steps):
        # 对每个农户做一次决策评估（共享策略）
        for farmer_id in range(config["network"]["num_farmers"]):
            s = get_state_vector_for_eval(dynamics, G, farmer_id)
            with torch.no_grad():
                q = net(torch.from_numpy(s).unsqueeze(0))
                action = int(torch.argmax(q, dim=1).item())

            # reward分解（用当前环境状态计算）
            dec = compute_reward_decomposition(
                config=config,
                farmer_id=farmer_id,
                action=action,
                dynamics=dynamics,
                subsidy=subsidy,
            )

            rows.append(
                {
                    "t": t,
                    "farmer_id": farmer_id,
                    "action": action,
                    "q0": float(q[0, 0].item()),
                    "q1": float(q[0, 1].item()),
                    "economic_norm": float(s[0]),
                    "degree_centrality": float(s[1]),
                    "policy_perception": float(s[2]),
                    "risk_tolerance": float(s[3]),
                    "fertility": float(s[4]),
                    "soil_structure": float(s[5]),
                    "biological_activity": float(s[6]),
                    "neighbor_adoption": float(s[7]),
                    "global_Q": float(s[8]),
                    "myopia": float(s[9]),
                    "education_priority": float(s[10]),
                    "political_voice": float(s[11]),
                    **{f"reward_{k}": v for k, v in asdict(dec).items()},
                }
            )

        # 用该策略驱动系统前进一步（便于观察策略在动态过程中的一致性）
        # 简化：直接写入动作并更新质量
        dynamics.farmer_df.loc[:, "adoption_state"] = [
            r["action"] for r in rows[-config["network"]["num_farmers"] :]
        ]
        dynamics.update_land_quality(dt=1.0)

    df = pd.DataFrame(rows)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv, index=False)

    # 汇总统计
    summary: Dict = {}
    summary["meta"] = {
        "model_path": model_path,
        "subsidy": subsidy,
        "steps": steps,
        "num_farmers": int(config["network"]["num_farmers"]),
    }

    summary["overall"] = {
        "adoption_rate": float(df["action"].mean()),
        "avg_reward_total": float(df["reward_total"].mean()),
        "avg_reward_economic_term": float(df["reward_economic_term"].mean()),
        "avg_reward_policy_term": float(df["reward_policy_term"].mean()),
        "avg_reward_social_term": float(df["reward_social_term"].mean()),
        "avg_reward_education_term": float(df["reward_education_term"].mean()),
        "avg_reward_voice_term": float(df["reward_voice_term"].mean()),
        "avg_reward_adoption_bonus": float(df["reward_adoption_bonus"].mean()),
    }

    # 动作分组
    grp = df.groupby("action")
    summary["by_action"] = {
        int(a): {
            "count": int(len(sub)),
            "share": float(len(sub) / len(df)),
            "avg_reward_total": float(sub["reward_total"].mean()),
            "avg_neighbor_adoption": float(sub["neighbor_adoption"].mean()),
            "avg_global_Q": float(sub["global_Q"].mean()),
            "avg_degree_centrality": float(sub["degree_centrality"].mean()),
            "avg_policy_perception": float(sub["policy_perception"].mean()),
            "avg_myopia": float(sub["myopia"].mean()),
        }
        for a, sub in grp
    }

    # 相关性：动作与各特征/奖励项
    corr_cols = [
        "action",
        "economic_norm",
        "degree_centrality",
        "policy_perception",
        "risk_tolerance",
        "fertility",
        "soil_structure",
        "biological_activity",
        "neighbor_adoption",
        "global_Q",
        "myopia",
        "education_priority",
        "political_voice",
        "reward_total",
        "reward_economic_term",
        "reward_policy_term",
        "reward_social_term",
        "reward_education_term",
        "reward_voice_term",
    ]
    corr = df[corr_cols].corr(numeric_only=True).round(4)
    summary["correlation"] = corr.to_dict()

    Path(output_summary_json).parent.mkdir(parents=True, exist_ok=True)
    with open(output_summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("[OK] wrote", output_csv)
    print("[OK] wrote", output_summary_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--subsidy", type=float, default=105.0)
    parser.add_argument("--steps", type=int, default=1)
    parser.add_argument("--model", default="models/agent_0_final.pth")
    parser.add_argument("--out_csv", default="results/policy_explainability.csv")
    parser.add_argument("--out_json", default="results/policy_explainability_summary.json")
    args = parser.parse_args()

    config = load_config(args.config)

    evaluate_policy(
        config=config,
        model_path=args.model,
        subsidy=args.subsidy,
        steps=args.steps,
        output_csv=args.out_csv,
        output_summary_json=args.out_json,
    )


if __name__ == "__main__":
    main()
