#!/usr/bin/env python3
import argparse, json, pandas as pd

def write_plan(df, out_path, vehicle=2, cruise=5.0, hover=3.0, firmware=12):
    items=[]
    for i,(la,lo,al) in enumerate(zip(df["lat"], df["lon"], df["alt"])):
        items.append({
            "AMSLAltAboveTerrain": None,
            "Altitude": float(al),
            "AltitudeMode": 1,
            "autoContinue": True,
            "command": 16,
            "doJumpId": i+1,
            "frame": 3,
            "params": [0,0,0,0,float(la),float(lo),float(al)],
            "type": "SimpleItem"
        })
    plan = {
      "fileType": "Plan",
      "groundStation": "QGroundControl",
      "version": 1,
      "geoFence": {"circles": [], "polygons": [], "version": 2},
      "rallyPoints": {"points": [], "version": 2},
      "mission": {
        "cruiseSpeed": float(cruise),
        "hoverSpeed": float(hover),
        "firmwareType": int(firmware),
        "vehicleType": int(vehicle),
        "plannedHomePosition": [float(df['lat'].iloc[0]), float(df['lon'].iloc[0]), float(df['alt'].iloc[0])],
        "items": items,
        "version": 2
      }
    }
    open(out_path,"w").write(json.dumps(plan, indent=2))
    return out_path

def main():
    ap = argparse.ArgumentParser(description="WGS84 CSV -> QGC .plan")
    ap.add_argument("--in", dest="inp", required=True, help="..._wgs84_simple.csv")
    ap.add_argument("--out", dest="out", default="route.plan", help="output .plan (default route.plan)")
    ap.add_argument("--vehicle", type=int, default=2, help="1=FixedWing, 2=MultiRotor (default 2)")
    ap.add_argument("--cruise", type=float, default=5.0)
    ap.add_argument("--hover", type=float, default=3.0)
    args = ap.parse_args()

    df = pd.read_csv(args.inp)
    path = write_plan(df, args.out, vehicle=args.vehicle, cruise=args.cruise, hover=args.hover)
    print(f"[OK] saved {path}  (waypoints: {len(df)})")

if __name__ == "__main__":
    main()

