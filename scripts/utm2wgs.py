#!/usr/bin/env python3
import argparse, pandas as pd
from pyproj import Transformer

def main():
    ap = argparse.ArgumentParser(description="UTM CSV -> WGS84 (lat,lon,alt).")
    ap.add_argument("--in", dest="inp", required=True, help="..._utm_simple.csv")
    ap.add_argument("--out", dest="out", default=None, help="output CSV (default *_wgs84_simple.csv)")
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    if args.out is None:
        args.out = args.inp.replace("_utm_simple.csv", "_wgs84_simple.csv")

    epsg = str(df["utm_epsg"].iloc[0]) if "utm_epsg" in df.columns else None
    if not epsg:
        raise SystemExit("Brak kolumny utm_epsg – potrzebne do transformacji.")

    tr = Transformer.from_crs(f"EPSG:{epsg}", "EPSG:4326", always_xy=True)
    lon, lat = tr.transform(df["x"].values, df["y"].values)
    out = pd.DataFrame({"lat": lat, "lon": lon, "alt": df["alt"].values})
    out.to_csv(args.out, index=False)
    print(f"[OK] saved {args.out}")
if __name__ == "__main__":
    main()

