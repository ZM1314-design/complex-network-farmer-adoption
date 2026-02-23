"""plot_baseline_vs_rl.py

生成 baseline 与 RL（DQN）关键结果对比图（顶刊风格）。

输出：
- figures_journal/baseline_vs_rl_comparison.png
- figures_journal/baseline_vs_rl_comparison.pdf

数据来源：
- results/baseline_summary.json
- results/baseline_history.csv
- results/rl_training_history.csv

运行：
python3 scripts/plot_baseline_vs_rl.py --out figures_journal
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# project import
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.plot_style import apply_journal_style, JOURNAL_PALETTE


def load_baseline():
    summary = json.loads(Path("results/baseline_summary.json").read_text(encoding="utf-8"))
    hist = pd.read_csv("results/baseline_history.csv")
    return summary, hist


def load_rl():
    df = pd.read_csv("results/rl_training_history.csv")
    return df


def save(fig, out_dir: Path, name: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / f"{name}.png", dpi=600, bbox_inches="tight", pad_inches=0.05, facecolor="white")
    fig.savefig(out_dir / f"{name}.pdf", bbox_inches="tight", pad_inches=0.05, facecolor="white")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="figures_journal")
    args = parser.parse_args()

    apply_journal_style()

    out_dir = Path(args.out)

    baseline_summary, baseline_hist = load_baseline()
    rl_hist = load_rl()

    # --- key scalars ---
    baseline_final_adoption = float(baseline_summary.get("final_adoption_rate", baseline_hist["adoption_rate"].iloc[-1]))
    baseline_final_q = float(baseline_summary.get("final_global_Q", baseline_hist["global_Q"].iloc[-1]))

    rl_final_adoption = float(rl_hist["adoption_rates"].iloc[-1])
    rl_final_q = float(rl_hist["global_Q"].iloc[-1])

    # threshold markers
    s_sigmoid = 483.4  # paper primary
    s_scan = float(baseline_summary.get("critical_subsidy", 500.0))
    s_perc = float(baseline_summary.get("percolation_subsidy", 485.0))
    s_base = float(baseline_summary.get("config", {}).get("policy", {}).get("subsidy_base", 105.0))

    # --- figure layout ---
    # Use manual layout to avoid suptitle/subplot title overlap across backends
    fig = plt.figure(figsize=(11.5, 7.2))
    gs = fig.add_gridspec(
        2,
        2,
        left=0.07,
        right=0.98,
        bottom=0.08,
        top=0.88,
        wspace=0.25,
        hspace=0.35,
    )

    # (A) final adoption bar
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.bar(["Baseline", "RL (DQN)"], [baseline_final_adoption, rl_final_adoption],
            color=[JOURNAL_PALETTE["gray"], JOURNAL_PALETTE["green"]])
    ax1.set_ylim(0, 1)
    ax1.set_ylabel("Final adoption rate")
    ax1.set_title("(A) Final adoption", pad=6)
    for i, v in enumerate([baseline_final_adoption, rl_final_adoption]):
        ax1.text(i, v + 0.02, f"{v*100:.1f}%", ha="center", va="bottom", fontsize=9, clip_on=False)

    # (B) final global quality bar
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.bar(["Baseline", "RL (DQN)"], [baseline_final_q, rl_final_q],
            color=[JOURNAL_PALETTE["gray"], JOURNAL_PALETTE["blue"]])
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("Final global land quality (Q)")
    ax2.set_title("(B) Final global quality", pad=6)
    for i, v in enumerate([baseline_final_q, rl_final_q]):
        ax2.text(i, v + 0.02, f"{v:.2f}", ha="center", va="bottom", fontsize=9, clip_on=False)

    # (C) adoption trajectories: baseline time vs RL training (episode)
    ax3 = fig.add_subplot(gs[1, 0])
    ax3.plot(baseline_hist["time"], baseline_hist["adoption_rate"], color=JOURNAL_PALETTE["gray"], label="Baseline (time)")
    ax3.plot(rl_hist["episode"], rl_hist["adoption_rates"], color=JOURNAL_PALETTE["green"], label="RL (training)")
    ax3.set_ylim(0, 1)
    ax3.set_xlabel("Time step / Training episode")
    ax3.set_ylabel("Adoption rate")
    ax3.set_title("(C) Dynamics vs learning", pad=6)
    ax3.legend(loc="upper left", frameon=False)

    # (D) policy threshold markers
    ax4 = fig.add_subplot(gs[1, 1])
    ax4.axvline(s_base, color=JOURNAL_PALETTE["black"], linestyle="--", linewidth=1.5, label="Baseline subsidy (105)")
    ax4.axvline(s_sigmoid, color=JOURNAL_PALETTE["purple"], linestyle="-", linewidth=2.0, label="Critical (Sigmoid) ~483.4")
    ax4.axvline(s_perc, color=JOURNAL_PALETTE["orange"], linestyle=":", linewidth=2.0, label="Percolation ~485")
    ax4.axvline(s_scan, color=JOURNAL_PALETTE["red"], linestyle="-.", linewidth=2.0, label="Scan critical 500")
    ax4.set_xlim(0, 500)
    ax4.set_xlabel("Subsidy (yuan/mu)")
    ax4.set_yticks([])
    ax4.set_title("(D) Critical region (0–500)", pad=6)
    ax4.legend(loc="upper left", frameon=False, fontsize=8)

    fig.suptitle(
        "Baseline vs RL (DQN): outcome comparison under realism-calibrated setting",
        y=0.97,
        fontsize=12,
    )

    save(fig, out_dir, "baseline_vs_rl_comparison")
    plt.close(fig)

    print("[OK] Saved: figures_journal/baseline_vs_rl_comparison.(png/pdf)")


if __name__ == "__main__":
    main()
