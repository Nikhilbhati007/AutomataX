"""Generate publication-quality benchmark figures for Automata Detective."""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from experiments import (
    run_active_vs_random_study,
    run_diversity_study,
    run_learning_curve,
    run_noise_study,
)

OUT_DIR = Path(__file__).parent / "figures"
OUT_DIR.mkdir(exist_ok=True)

# Styling: modern dark/slate publication theme
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "figure.titlesize": 14,
})

def plot_learning_curves():
    print("Generating learning curves...")
    report = run_learning_curve(
        "ends_with_ab",
        train_sizes=[10, 25, 50, 80, 120],
        learners=["edsm", "rpni"],
        seeds=[0, 1, 2, 3],
        test_size=150,
    )
    edsm_pts = [p for p in report.points if p.learner == "edsm"]
    rpni_pts = [p for p in report.points if p.learner == "rpni"]

    sizes = [p.train_size for p in edsm_pts]
    edsm_acc = [p.mean_accuracy * 100 for p in edsm_pts]
    edsm_std = [p.std_accuracy * 100 for p in edsm_pts]
    rpni_acc = [p.mean_accuracy * 100 for p in rpni_pts]
    rpni_std = [p.std_accuracy * 100 for p in rpni_pts]

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    ax.errorbar(sizes, edsm_acc, yerr=edsm_std, fmt="-o", color="#0891b2", label="EDSM (Blue-Fringe)", lw=2.2, capsize=4)
    ax.errorbar(sizes, rpni_acc, yerr=rpni_std, fmt="-s", color="#e11d48", label="RPNI (Canonical)", lw=2.2, capsize=4)

    ax.set_title("Learning Curves on 'Ends with ab' (Test Generalization)")
    ax.set_xlabel("Training Set Size (Number of Labeled Strings)")
    ax.set_ylabel("Generalization Accuracy on Unseen Test Strings (%)")
    ax.set_ylim(45, 105)
    ax.legend(frameon=True, loc="lower right")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "learning_curves.png")
    plt.close(fig)
    print("Saved learning_curves.png")

def plot_noise_study():
    print("Generating noise study...")
    report = run_noise_study(
        "even_ones",
        noise_rates=[0.0, 0.05, 0.10, 0.20],
        learners=["edsm", "rpni"],
        train_size=70,
        seeds=[0, 1, 2],
    )
    edsm_pts = [p for p in report.points if p.learner == "edsm"]
    rpni_pts = [p for p in report.points if p.learner == "rpni"]

    noise_labels = ["0%", "5%", "10%", "20%"]
    edsm_acc = [p.mean_accuracy * 100 for p in edsm_pts]
    rpni_acc = [p.mean_accuracy * 100 for p in rpni_pts]

    x = np.arange(len(noise_labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    ax.bar(x - width/2, edsm_acc, width, label="EDSM (Graceful Degradation)", color="#0891b2", edgecolor="#0e7490")
    ax.bar(x + width/2, rpni_acc, width, label="RPNI (Noise Collapse)", color="#e11d48", edgecolor="#be123c")

    ax.set_title("Label Noise Tolerance on 'Even Number of 1s'")
    ax.set_xlabel("Injected Label Noise Rate (% of Flipped Labels)")
    ax.set_ylabel("Test Accuracy (%)")
    ax.set_xticks(x)
    ax.set_xticklabels(noise_labels)
    ax.set_ylim(40, 105)
    ax.legend(frameon=True, loc="upper right")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "noise_study.png")
    plt.close(fig)
    print("Saved noise_study.png")

def plot_active_vs_random():
    print("Generating active learning study...")
    comp = run_active_vs_random_study(
        "ends_with_ab",
        initial_size=6,
        batch_size=6,
        rounds=5,
        pool_size=120,
        test_size=100,
        seed=42,
    )
    budgets = comp.query_budgets
    active_acc = [a * 100 for a in comp.active_accuracies]
    random_acc = [r * 100 for r in comp.random_accuracies]

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    ax.plot(budgets, active_acc, "-o", color="#d97706", label="Active Learning (Uncertainty Queries)", lw=2.4)
    ax.plot(budgets, random_acc, "--s", color="#64748b", label="Passive Random Sampling", lw=2.0)

    ax.set_title("Active Learning vs. Random Sampling Convergence")
    ax.set_xlabel("Oracle Query Budget (Labeled Examples Used)")
    ax.set_ylabel("Test Accuracy (%)")
    ax.set_ylim(45, 105)
    ax.legend(frameon=True, loc="lower right")
    plt.tight_layout()
    fig.savefig(OUT_DIR / "active_vs_random.png")
    plt.close(fig)
    print("Saved active_vs_random.png")

def plot_diversity_study():
    print("Generating diversity study...")
    report = run_diversity_study(
        "third_from_end_a",
        learner="edsm",
        random_multipliers=[1, 2, 4],
        seeds=[0, 1, 2],
        test_size=120,
    )
    categories = ["Characteristic\nSample (1x)", "Random 1x", "Random 2x", "Random 4x"]
    accs = [
        report.characteristic_accuracy * 100,
        report.random_samples[0]["mean_accuracy"] * 100,
        report.random_samples[1]["mean_accuracy"] * 100,
        report.random_samples[2]["mean_accuracy"] * 100,
    ]
    colors = ["#10b981", "#94a3b8", "#64748b", "#475569"]

    fig, ax = plt.subplots(figsize=(7, 4.2), dpi=200)
    bars = ax.bar(categories, accs, color=colors, edgecolor="#334155", width=0.55)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 1.5, f"{yval:.1f}%", ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_title("Diversity vs. Raw Quantity ('3rd Symbol from End is a')")
    ax.set_ylabel("Test Accuracy (%)")
    ax.set_ylim(40, 110)
    plt.tight_layout()
    fig.savefig(OUT_DIR / "diversity_study.png")
    plt.close(fig)
    print("Saved diversity_study.png")

if __name__ == "__main__":
    plot_learning_curves()
    plot_noise_study()
    plot_active_vs_random()
    plot_diversity_study()
    print("All benchmark figures successfully generated in figures/")
