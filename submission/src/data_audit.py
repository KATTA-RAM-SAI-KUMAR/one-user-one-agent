"""Read-only structural audit for the STAGE One User, One Agent data pack."""
from __future__ import annotations
import argparse, collections, csv, json
from pathlib import Path


def jsonl_audit(path: Path) -> dict:
    count = 0
    ids: set[str] = set()
    duplicate_occurrences = 0
    users: set[str] = set()
    types = collections.Counter()
    malformed = 0
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            count += 1
            if row.get("user_id"):
                users.add(row["user_id"])
            event_id = row.get("event_id")
            if event_id:
                if event_id in ids:
                    duplicate_occurrences += 1
                ids.add(event_id)
            types[row.get("event", row.get("type", "unknown"))] += 1
    return {"file": str(path), "rows": count, "unique_users": len(users),
            "duplicate_event_id_occurrences": duplicate_occurrences,
            "malformed_json_lines": malformed, "event_types": dict(types)}


def csv_audit(path: Path, key: str | None = None) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    result = {"file": str(path), "rows": len(rows), "columns": list(rows[0]) if rows else []}
    if key and rows:
        counts = collections.Counter(row.get(key, "") for row in rows)
        result["duplicate_key_values"] = sum(n > 1 for n in counts.values())
        result["max_rows_per_key"] = max(counts.values())
    if path.name == "arms.csv":
        result["arm_counts"] = dict(collections.Counter(r.get("arm", "") for r in rows))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, default=Path("one_user_one_agent_pack"),
                        help="Path to extracted one_user_one_agent_pack directory")
    parser.add_argument("--out", type=Path, default=Path("sample_run/data_audit.json"))
    args = parser.parse_args()
    p = args.pack
    if not p.is_dir():
        raise SystemExit(f"Data pack directory not found: {p.resolve()}\nExtract the supplied ZIP first.")
    report = {"pack_root": str(p), "jsonl": [], "csv": []}
    for rel in ["data/events.jsonl", "replay/triggers.jsonl", "replay/live_events.jsonl",
                "replay/control_events.jsonl", "replay/model_faults.jsonl"]:
        report["jsonl"].append(jsonl_audit(p / rel))
    for rel, key in [("data/profiles_snapshot.csv", "user_id"), ("data/catalogue.csv", "title_id"),
                     ("data/episodes.csv", "episode_id"), ("replay/arms.csv", "user_id"),
                     ("pilot/pilot_assignment.csv", "user_id"), ("pilot/pilot_outcomes.csv", "user_id")]:
        report["csv"].append(csv_audit(p / rel, key))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nAudit saved to: {args.out}")

if __name__ == "__main__":
    main()
