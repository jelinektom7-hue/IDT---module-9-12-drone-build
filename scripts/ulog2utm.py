#!/usr/bin/env python3
import argparse, os, numpy as np, pandas as pd
from pyulog import ULog
from pyproj import Transformer

# headless plotting
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LAT_CANDS  = ["lat","latitude","lat_deg","latitude_deg","lat_rad"]
LON_CANDS  = ["lon","longitude","lon_deg","longitude_deg","lon_rad"]
ALT_CANDS  = ["alt","alt_ellipsoid","amsl","alt_msl","relative_alt"]
TIME_CANDS = ["timestamp","time_usec","time_boot_ms"]

def to_seconds(df: pd.DataFrame) -> np.ndarray:
    for c in TIME_CANDS:
        if c in df.columns:
            v = df[c].astype("float64").to_numpy()
            if c in ("timestamp","time_usec"): return v * 1e-6
            if c == "time_boot_ms":            return v * 1e-3
    return np.arange(len(df), dtype=float)

def to_degrees(series: pd.Series) -> np.ndarray:
    s = series.astype("float64").to_numpy(copy=True)
    if s.size == 0: return s
    m = np.nanmax(np.abs(s))
    if m > 1e6:   return s * 1e-7   # PX4 1e-7 deg
    if m > 1800:  return s * 1e-3   # milideg
    if m <= 3.2:  return np.degrees(s)  # rad
    return s

def find_lat_lon_alt(df: pd.DataFrame):
    lat_col = next((c for c in LAT_CANDS if c in df.columns), None)
    lon_col = next((c for c in LON_CANDS if c in df.columns), None)
    alt_col = next((c for c in ALT_CANDS if c in df.columns), None)
    if lat_col and lon_col:
        lat = to_degrees(df[lat_col])
        lon = to_degrees(df[lon_col])
        alt = df[alt_col].astype("float64").to_numpy() if alt_col else None
        return lat, lon, alt
    return None, None, None

def pick_topic(u: ULog):
    prefer = ["vehicle_gps_position","sensor_gps","vehicle_global_position"]
    for name in prefer:
        for d in u.data_list:
            if d.name == name:
                lat, lon, _ = find_lat_lon_alt(pd.DataFrame(d.data))
                if lat is not None: return d, name
    for d in u.data_list:
        df = pd.DataFrame(d.data)
        lat, lon, _ = find_lat_lon_alt(df)
        if lat is not None: return d, d.name
    raise RuntimeError("No topic with lat/lon found in .ulg")

def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1))*np.cos(np.radians(lat2))*np.sin(dlon/2)**2
    return 2*R*np.arcsin(np.sqrt(a))

def clean_track(time_s, lat, lon, alt, zero_eps=1e-6, max_abs_km=0.0, max_jump_m=0.0):
    """
    Minimal-clean:
      - usuń NaN/out-of-range i (prawie) [0,0]
      - posortuj po czasie
      - opcjonalnie: usuń punkty dalekie od centrum (> max_abs_km od mediany)
      - opcjonalnie: usuń pojedyncze teleporty na podstawie odległości do sąsiadów (> max_jump_m)
    Zwraca: posortowane i przefiltrowane: time, lat, lon, alt
    """
    # 0) baza: ważny zakres i brak (0,0)
    m = (~np.isnan(lat)) & (~np.isnan(lon)) & (np.abs(lat)<=90) & (np.abs(lon)<=180)
    m &= ~((np.abs(lat) < zero_eps) & (np.abs(lon) < zero_eps))
    time_s, lat, lon, alt = time_s[m], lat[m], lon[m], alt[m]

    # 1) sortowanie po czasie
    order = np.argsort(time_s)
    time_s, lat, lon, alt = time_s[order], lat[order], lon[order], alt[order]

    if lat.size < 2:
        return time_s, lat, lon, alt

    # 2) filtr promieniowy (odległość od mediany), jeśli włączony
    if max_abs_km and max_abs_km > 0:
        lat_med = float(np.median(lat)); lon_med = float(np.median(lon))
        dist_c = haversine_m(lat, lon, lat_med*np.ones_like(lat), lon_med*np.ones_like(lon))
        keep_c = dist_c <= (max_abs_km*1000.0)
        time_s, lat, lon, alt = time_s[keep_c], lat[keep_c], lon[keep_c], alt[keep_c]

    # 3) filtr "teleportów" po sąsiadach, jeśli włączony
    if max_jump_m and max_jump_m > 0 and lat.size >= 3:
        dist_prev = np.zeros(lat.size)
        dist_next = np.zeros(lat.size)
        dist_prev[1:]  = haversine_m(lat[1:],  lon[1:],  lat[:-1], lon[:-1])
        dist_next[:-1] = haversine_m(lat[:-1], lon[:-1], lat[1:],  lon[1:])
        keep = np.ones(lat.size, dtype=bool)
        offenders = np.where((dist_prev > max_jump_m) & (dist_next > max_jump_m))[0]
        keep[offenders] = False
        time_s, lat, lon, alt = time_s[keep], lat[keep], lon[keep], alt[keep]

    return time_s, lat, lon, alt

def save_plot_xy(x, y, out_png, xlabel, ylabel, title):
    plt.figure(figsize=(6,6))
    plt.plot(x, y, marker='o', markersize=2, linewidth=1)
    plt.xlabel(xlabel); plt.ylabel(ylabel)
    plt.title(title)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.grid(True, linewidth=0.3)
    plt.tight_layout()
    plt.savefig(out_png, dpi=180)
    plt.close()

def main():
    ap = argparse.ArgumentParser(description="PX4 .ulg -> UTM CSV (+ WGS84 CSV + wykresy). Filtry: (0,0), max-abs-km, max-jump.")
    ap.add_argument("ulog", help="ścieżka do .ulg")
    ap.add_argument("--id", default="00", help="unikalny numer do nazw plików")
    ap.add_argument("--alt", type=float, default=50.0, help="wysokość gdy brak w logu [m]")
    ap.add_argument("--max-abs-km", type=float, default=0.0, help="odetnij punkty dalej niż X km od mediany (0=off)")
    ap.add_argument("--max-jump", type=float, default=0.0, help="usuń samotne skoki > X m do obu sąsiadów (0=off)")
    ap.add_argument("--plot", action="store_true", help="zapisz podglądy PNG (WGS84 i UTM)")
    ap.add_argument("--outdir", default=".", help="katalog wyjściowy")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # 1) wczytaj ULog i wybierz topic
    u = ULog(args.ulog)
    d, topic_name = pick_topic(u)
    df = pd.DataFrame(d.data)

    # 2) wyciągnij i nałóż podstawy
    time_s = to_seconds(df)
    lat, lon, alt = find_lat_lon_alt(df)
    if alt is None: alt = np.full_like(lat, float(args.alt), dtype=float)

    # konwersja do numpy
    time_s = np.asarray(time_s, dtype=float)
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    alt = np.asarray(alt, dtype=float)

    # 3) czyszczenie (zawsze: (0,0) + sort po czasie; opcjonalnie: max-abs-km, max-jump)
    time_s, lat, lon, alt = clean_track(
        time_s, lat, lon, alt,
        zero_eps=1e-6,
        max_abs_km=args.max_abs_km,
        max_jump_m=args.max_jump
    )

    if lat.size == 0:
        raise RuntimeError(f"Topic '{topic_name}': brak prawidłowych punktów po czyszczeniu.")

    # 4) WGS84 CSV
    wgs_csv = os.path.join(args.outdir, f"track_{args.id}_wgs84.csv")
    pd.DataFrame({"time": time_s, "lat": lat, "lon": lon, "alt": alt}).to_csv(wgs_csv, index=False)

    # 5) WGS84 -> UTM (strefa po czyszczeniu – mediany)
    lon_med = float(np.median(lon)); lat_med = float(np.median(lat))
    zone = int((lon_med + 180)//6) + 1
    hemisphere = "north" if lat_med >= 0 else "south"
    epsg = f"326{zone:02d}" if hemisphere == "north" else f"327{zone:02d}"
    tr = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    x, y = tr.transform(lon, lat)

    utm_csv = os.path.join(args.outdir, f"track_{args.id}_utm.csv")
    pd.DataFrame({"time": time_s, "x": x, "y": y, "alt": alt, "utm_epsg": epsg}).to_csv(utm_csv, index=False)

    # 6) wykresy (WGS84 + UTM)
    if args.plot:
        wgs_png = os.path.join(args.outdir, f"track_{args.id}_wgs84_preview.png")
        utm_png = os.path.join(args.outdir, f"track_{args.id}_utm_preview.png")
        save_plot_xy(lon, lat, wgs_png, "Longitude [deg]", "Latitude [deg]", f"Track WGS84 (topic: {topic_name})")
        save_plot_xy(x, y, utm_png, "x [m]", "y [m]", f"Track UTM EPSG:{epsg}")
        print(f"[OK] PNG: {wgs_png}")
        print(f"[OK] PNG: {utm_png}")

    print(f"[OK] topic='{topic_name}', EPSG:{epsg}, zapisano: {utm_csv} ({len(x)} pkt)")
    print(f"[OK] zapisano: {wgs_csv}")

if __name__ == "__main__":
    main()

