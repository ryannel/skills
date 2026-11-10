"""tidepool: tide tables from the command line."""
import argparse

COLUMNS = ["station", "high_m", "low_m", "range_m"]

def report(rows):
    print("  ".join(c.ljust(10) for c in COLUMNS))
    for r in rows:
        print("  ".join(str(r[c]).ljust(10) for c in COLUMNS))

def main():
    p = argparse.ArgumentParser(prog="tidepool")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("report", help="print the tide table")
    a = p.parse_args()
    if a.cmd == "report":
        report([{"station": "Looe", "high_m": 5.1, "low_m": 0.9, "range_m": 4.2}])

if __name__ == "__main__":
    main()
