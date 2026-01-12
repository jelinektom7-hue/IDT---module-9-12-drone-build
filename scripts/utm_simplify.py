#!/usr/bin/env python3
import argparse, numpy as np, pandas as pd
from simplification.cutil import simplify_coords

# headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def plot_track(x, y, path_png, title):
    plt.figure(figsize=(6,6))
    plt.plot(x, y, marker="o", markersize=2, linewidth=1)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x [m]"); plt.ylabel("y [m]")
    plt.title(title); plt.grid(True, linewidth=0.3)
    plt.tight_layout(); plt.savefig(path_png, dpi=180); plt.close()

def main():
    ap = argparse.ArgumentParser(description="Simplify UTM track using RDP (+ plots).")
    ap.add_argument("--in", dest="inp", required=True, help="..._utm_denoised.csv")
    ap.add_argument("--out", dest="out", default=None, help="output CSV (default *_utm_simple.csv)")
    ap.add_argument("--tol", type=float, default=1.0, help="RDP tolerance [m] (default 1.0)")
    ap.add_argument("--plot", action="store_true", help="zapisz PNG przed/po")
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    if args.out is None:
        args.out = args.inp.replace("_utm_denoised.csv", "_utm_simple.csv")

    x = df["x"].values; y = df["y"].values

    # plot przed
    if args.plot:
        plot_track(x, y, args.inp.replace(".csv", "_before_simplify.png"),
                   "UTM before simplify")

    simp = simplify_coords(np.c_[x, y], args.tol)
    dfs = pd.DataFrame(simp, columns=["x","y"])

    # interp alt
    s_idx = np.linspace(0, len(df)-1, len(dfs))
    dfs["alt"] = np.interp(s_idx, np.arange(len(df)), df["alt"].values)
    if "utm_epsg" in df.columns:
        dfs["utm_epsg"] = df["utm_epsg"].iloc[0]

    dfs.to_csv(args.out, index=False)

    # plot po
    if args.plot:
        plot_track(dfs["x"].values, dfs["y"].values,
                   args.out.replace(".csv", f"_simplified_tol{args.tol}.png"),
                   f"UTM simplified (tol={args.tol} m)")

    print(f"[OK] saved {args.out}  ({len(df)} -> {len(dfs)} pts)")

if __name__ == "__main__":
    main()

