#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd

# headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def robust_dt(t):
    t = np.asarray(t, dtype="float64")
    dt = np.diff(t)
    dt = np.where(dt <= 0, np.nan, dt)
    med = np.nanmedian(dt) if np.any(~np.isnan(dt)) else 0.1
    dt = np.where(np.isnan(dt), med, dt)
    return dt

def plot_track(x, y, path_png, title):
    plt.figure(figsize=(6,6))
    plt.plot(x, y, marker="o", markersize=2, linewidth=1)
    plt.gca().set_aspect("equal", adjustable="box")
    plt.xlabel("x [m]"); plt.ylabel("y [m]")
    plt.title(title); plt.grid(True, linewidth=0.3)
    plt.tight_layout(); plt.savefig(path_png, dpi=180); plt.close()

def main():
    ap = argparse.ArgumentParser(description="Remove outliers from UTM track via speed/jump thresholds + plots.")
    ap.add_argument("--in", dest="inp", required=True, help="wejściowy CSV: ..._utm.csv")
    ap.add_argument("--out", dest="out", default=None, help="wyjściowy CSV (domyślnie *_utm_denoised.csv)")
    ap.add_argument("--vmax", type=float, default=15.0, help="maks. prędkość [m/s] (domyślnie 15)")
    ap.add_argument("--jump", type=float, default=20.0, help="maks. skok jednorazowy [m] (domyślnie 20)")
    ap.add_argument("--plot", action="store_true", help="zapisz PNG przed/po")
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    if args.out is None:
        args.out = args.inp.replace("_utm.csv", "_utm_denoised.csv")

    # plot raw (przed)
    if args.plot:
        plot_track(df["x"].values, df["y"].values,
                   args.inp.replace(".csv", "_raw.png"),
                   "UTM raw (before denoise)")

    # czas
    if "time" in df.columns:
        dt = robust_dt(df["time"].values)
    else:
        dt = np.full(len(df)-1, 0.5, dtype="float64")

    # metry między sąsiadami
    dx = np.diff(df["x"].values)
    dy = np.diff(df["y"].values)
    dist = np.hypot(dx, dy)
    speed = dist / dt

    # reguły odrzucania
    keep_speed = speed < args.vmax
    keep_jump  = dist  < args.jump
    keep = keep_speed & keep_jump
    keep = np.insert(keep, 0, True)  # pierwszy punkt zostaw

    dfo = df[keep].reset_index(drop=True)
    dfo.to_csv(args.out, index=False)

    # plot denoised (po)
    if args.plot:
        plot_track(dfo["x"].values, dfo["y"].values,
                   args.out.replace(".csv", "_denoised.png"),
                   f"UTM denoised (vmax={args.vmax} m/s, jump<{args.jump} m)")

    kept = len(dfo); total = len(df)
    print(f"[OK] zapisano: {args.out}  (kept {kept}/{total} points)")
    if "utm_epsg" in df.columns:
        print(f"EPSG: {df['utm_epsg'].iloc[0]}")

if __name__ == "__main__":
    main()

