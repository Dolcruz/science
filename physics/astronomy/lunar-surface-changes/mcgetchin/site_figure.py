"""Display the high-Sun brightness change and the July lighting reversal."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
from matplotlib import pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent


def main():
    fig, axs = plt.subplots(2, 2, figsize=(7.6, 7.3), layout="constrained")
    frames = [("pre_albedo","9 Apr 2022 · 13° incidence"), ("postA","28 Nov 2025 · 8° incidence"),
              ("post_east","17 Jul 2026 · Sun from east"), ("post_west","30 Jul 2026 · Sun from west")]
    with np.load(ROOT / "candidate-chips.npz") as chips:
        for i, ((key, title), ax) in enumerate(zip(frames, axs.flat)):
            a = chips["NW_" + key][12:53, 12:53]
            ax.imshow(a, cmap="gray", interpolation="nearest", extent=[-20.5,20.5,20.5,-20.5],
                      vmin=np.percentile(a, 1), vmax=np.percentile(a, 99))
            ax.plot([-7,-4.5],[0,0], color="#41cdb4")
            ax.plot([0,0],[-7,-4.5], color="#41cdb4")
            ax.set_title(title, fontsize=11)
            if i % 2 == 0:
                ax.set_ylabel("South offset (m)")
            if i >= 2:
                ax.set_xlabel("East offset (m)")
    fig.suptitle("Northwestern site under high and opposing low Sun", fontsize=14)
    fig.savefig(ROOT / "albedo-and-reversal.png", dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    main()
