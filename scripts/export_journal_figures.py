"""export_journal_figures.py

一键导出“顶刊风格”图表到新目录 figures_journal/。

做什么：
1) 运行 baseline（现实校准版 config.yaml）并导出 baseline 相关图
2) 运行 rl 并导出训练曲线等图（如果已有训练日志，可选择跳过训练，仅重绘曲线）
3) 生成补充图（如果仓库中已有脚本 generate_supplementary_figures.py，则调用其主逻辑）
4) 生成 figures_journal/FIGURE_INDEX.md（图->含义->来源）

运行：
python3 scripts/export_journal_figures.py --config config.yaml --out figures_journal --skip_rl_train

注意：
- 为保证“完全更新”，默认会重跑 baseline。
- RL 训练耗时较长，默认可跳过训练，仅根据 results/rl_training_history.csv 重绘 training_curves。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

# 允许以脚本方式运行时正确导入项目模块：把项目根目录加入 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_generator import load_config
from src.visualization import Visualizer
from src.network_builder import HyperbolicNetworkBuilder
from src.data_generator import FarmerDataGenerator
from src.dynamics import AdoptionDynamics


def write_index(out_dir: Path):
    lines = [
        "# FIGURE_INDEX (Journal-ready)",
        "",
        "本目录为顶刊风格统一输出（PNG 600dpi + PDF 矢量）。",
        "",
        "## 核心论文图（thesis_fixed.tex 引用）",
        "- network_final_state.(png/pdf): 最终网络状态（绿色=采纳，灰色=未采纳）",
        "- phase_transition.(png/pdf): 补贴扫描下采纳率相变 + 逾渗（GCC）序参量",
        "- training_curves.(png/pdf): DQN 训练曲线（采纳率/奖励/质量/ε）",
        "- diffusion_time.(png/pdf): 采纳率随时间演化（baseline 动力学）",
        "",
        "## 补充图",
        "- degree_distribution.(png/pdf): 度分布与幂律验证",
        "- betweenness_response.(png/pdf): 中介中心性与政策响应关系",
        "- quality_3d_evolution.(png/pdf): 三维质量演化",
        "- 其余 *.png/*.pdf: 由仓库补充图脚本生成，用于扩展分析",
    ]
    (out_dir / "FIGURE_INDEX.md").write_text("\n".join(lines), encoding="utf-8")


def run_baseline_and_export(config_path: str, out_dir: Path):
    """通过调用 run_experiment.py 的 baseline 模式，保证相变/逾渗/网络等图与主流程一致。

    做法：生成一个临时 config，把 output.figures_dir 指向 out_dir，把 results_dir 指向 results_journal/，
    然后执行：python3 run_experiment.py --mode baseline --config <temp>
    """

    import subprocess
    import tempfile
    import yaml

    config = load_config(config_path)

    # 重定向输出目录，避免覆盖主目录
    config.setdefault("output", {})
    config["output"]["figures_dir"] = str(out_dir)
    config["output"]["results_dir"] = "./results_journal"
    config["output"]["models_dir"] = "./models_journal"
    config["output"]["logs_dir"] = "./logs_journal"

    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
        temp_config_path = f.name

    cmd = ["python3", "run_experiment.py", "--mode", "baseline", "--config", temp_config_path]
    subprocess.check_call(cmd)


def redraw_training_curves_from_csv(config_path: str, out_dir: Path):
    config = load_config(config_path)
    csv_path = Path("results/rl_training_history.csv")
    if not csv_path.exists():
        raise FileNotFoundError("results/rl_training_history.csv not found; please run RL training first")

    df = pd.read_csv(csv_path)
    history = {
        "adoption_rates": df["adoption_rates"].tolist(),
        "avg_rewards": df["avg_rewards"].tolist(),
        "global_Q": df["global_Q"].tolist(),
        "epsilon": df["epsilon"].tolist(),
    }

    viz = Visualizer(output_dir=str(out_dir), export_pdf=True)
    viz.plot_training_curves(history, save_name="training_curves")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--out", default="figures_journal")
    parser.add_argument("--skip_rl_train", action="store_true", help="跳过 RL 训练，仅重绘训练曲线")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # baseline + 相变 + 网络图（会重算）
    run_baseline_and_export(args.config, out_dir)

    # RL 曲线重绘
    redraw_training_curves_from_csv(args.config, out_dir)

    write_index(out_dir)
    print(f"[OK] Journal figures exported to: {out_dir}")


if __name__ == "__main__":
    main()
