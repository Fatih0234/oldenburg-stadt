#!/usr/bin/env python3
import json
import sys
import argparse
from datetime import datetime, timedelta

def get_reference_date(reports):
    """
    Computes reference date matching the app.js logic.
    If the latest report is more than 14 days old, uses that latest date.
    Otherwise, uses the current local time.
    """
    now = datetime.now()
    if not reports:
        return now
        
    latest_timestamp = None
    for r in reports:
        created_at_str = r.get("createdAt")
        if created_at_str:
            try:
                # Handle standard ISO timestamp (e.g. 2024-05-19T10:00:00.000Z)
                # Strip trailing 'Z' and milliseconds if present for simplicity
                clean_str = created_at_str.replace("Z", "")
                if "." in clean_str:
                    clean_str = clean_str.split(".")[0]
                dt = datetime.fromisoformat(clean_str)
                if latest_timestamp is None or dt > latest_timestamp:
                    latest_timestamp = dt
            except ValueError:
                continue
                
    if not latest_timestamp:
        return now
        
    diff = now - latest_timestamp
    if diff.days > 14:
        return latest_timestamp
    return now

def calculate_safety_index(reports):
    """
    Computes City Safety Index matching the app.js logic.
    Penalty: Confirmed * 8 + Likely * 4 + Possible * 1.5
    Score: Max(10, Min(100, 100 - Penalty))
    """
    confirmed = 0
    likely = 0
    possible = 0
    
    for r in reports:
        state = r.get("state")
        if state in ("OPEN", "IN_PROCESS"):
            impact = r.get("cyclist_impact_label")
            if impact == "Confirmed cycling issue":
                confirmed += 1
            elif impact == "Likely cycling issue":
                likely += 1
            elif impact == "Possibly affects cyclists":
                possible += 1
                
    penalty = (confirmed * 8) + (likely * 4) + (possible * 1.5)
    return max(10, min(100, round(100 - penalty)))

def main():
    parser = argparse.ArgumentParser(description="Aggregate and filter Oldenburg stadtverbesserer reports for slide generation.")
    parser.add_argument("--days", type=int, default=7, help="Number of days to filter (default: 7). Use 0 for all time.")
    parser.add_argument("--min-score", type=int, default=40, help="Minimum confidence score (default: 40).")
    parser.add_argument("--cycling-only", action="store_true", default=True, help="Only include confirmed/likely cycling issues (default: True).")
    parser.add_argument("--no-cycling-only", dest="cycling_only", action="store_false", help="Include all issues including generic ones.")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of featured critical issues (default: 5).")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted markdown summary.")
    
    args = parser.parse_args()
    
    try:
        with open("classified_reports.json", "r", encoding="utf-8") as f:
            reports = json.load(f)
    except FileNotFoundError:
        print("Error: classified_reports.json not found. Run from the oldenburg-stadt directory.", file=sys.stderr)
        sys.exit(1)
        
    ref_date = get_reference_date(reports)
    
    # 1. Date range filter
    if args.days > 0:
        cutoff = ref_date - timedelta(days=args.days)
        time_filtered = []
        for r in reports:
            created_at_str = r.get("createdAt")
            if created_at_str:
                try:
                    clean_str = created_at_str.replace("Z", "")
                    if "." in clean_str:
                        clean_str = clean_str.split(".")[0]
                    dt = datetime.fromisoformat(clean_str)
                    if dt >= cutoff:
                        time_filtered.append(r)
                except ValueError:
                    continue
    else:
        time_filtered = reports
        cutoff = None
        
    # Calculate safety index of the filtered period
    period_safety_index = calculate_safety_index(time_filtered)
    overall_safety_index = calculate_safety_index(reports)
    
    # 2. Relevancy & cycling filter for featured issues
    featured_pool = []
    for r in time_filtered:
        score = r.get("confidence_score", 0)
        impact = r.get("cyclist_impact_label", "")
        
        if score < args.min_score:
            continue
            
        if args.cycling_only:
            if impact not in ("Confirmed cycling issue", "Likely cycling issue"):
                continue
                
        featured_pool.append(r)
        
    # Sort by confidence score descending, then distance to bike path ascending
    featured_pool.sort(key=lambda x: (-x.get("confidence_score", 0), x.get("distance_to_bike_path_meters", 999)))
    featured_issues = featured_pool[:args.limit]
    
    # Calculate stats for the period
    state_counts = {"OPEN": 0, "IN_PROCESS": 0, "CLOSED": 0}
    impact_counts = {
        "Confirmed cycling issue": 0,
        "Likely cycling issue": 0,
        "Possibly affects cyclists": 0,
        "Not cycling-specific": 0
    }
    
    for r in time_filtered:
        state = r.get("state", "OPEN")
        if state in state_counts:
            state_counts[state] += 1
        impact = r.get("cyclist_impact_label")
        if impact in impact_counts:
            impact_counts[impact] += 1
            
    # Hotspot analysis (group by nearest street segment)
    segment_counts = {}
    for r in time_filtered:
        segment = r.get("nearest_segment_name")
        if segment and segment != "":
            segment_counts[segment] = segment_counts.get(segment, 0) + 1
            
    sorted_hotspots = sorted(segment_counts.items(), key=lambda x: -x[1])[:3]
    
    # Output presentation data
    output_data = {
        "metadata": {
            "reference_date": ref_date.isoformat(),
            "timeframe_days": args.days,
            "cutoff_date": cutoff.isoformat() if cutoff else "All Time",
            "total_reports_in_period": len(time_filtered),
            "period_safety_index": period_safety_index,
            "overall_safety_index": overall_safety_index,
            "safety_index_delta": period_safety_index - overall_safety_index
        },
        "stats": {
            "states": state_counts,
            "impact_levels": impact_counts
        },
        "hotspots": [{"segment": k, "count": v} for k, v in sorted_hotspots],
        "featured_issues": [
            {
                "id": r.get("id"),
                "category": r.get("categoryName"),
                "description": r.get("replacingText"),
                "impact": r.get("cyclist_impact_label"),
                "score": r.get("confidence_score"),
                "street": r.get("nearest_segment_name") or "Unknown Street",
                "distance_to_path_m": r.get("distance_to_bike_path_meters"),
                "explanation": r.get("explanation_de"),
                "state": r.get("state"),
                "coords": [r.get("latitude"), r.get("longitude")]
            }
            for r in featured_issues
        ]
    }
    
    if args.json:
        print(json.dumps(output_data, indent=2, ensure_ascii=False))
    else:
        # Markdown report optimized for Antigravity's slide generation prompt
        meta = output_data["metadata"]
        stats = output_data["stats"]
        
        delta_str = f"{meta['safety_index_delta']:+d}" if meta['safety_index_delta'] != 0 else "No Change"
        
        print(f"# ANTIGRAVITY PRESENTATION DATA REPORT")
        print(f"**Generated on**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"**Timeframe**: Last {meta['timeframe_days']} days (Cutoff: {meta['cutoff_date'].split('T')[0]})")
        print(f"**Reference Date**: {meta['reference_date'].split('T')[0]}")
        print(f"**Total Reports in Period**: {meta['total_reports_in_period']}")
        print(f"**Period Safety Index**: {meta['period_safety_index']}/100 (Overall: {meta['overall_safety_index']}/100, Delta: {delta_str})")
        print()
        print(f"## 📊 PERIOD METRICS")
        print(f"* **States**: {stats['states']['OPEN']} Open, {stats['states']['IN_PROCESS']} In Progress, {stats['states']['CLOSED']} Closed")
        print(f"* **Cyclist Impact Breakdown**:")
        print(f"  * 🚨 Confirmed: {stats['impact_levels']['Confirmed cycling issue']}")
        print(f"  * 🚧 Likely: {stats['impact_levels']['Likely cycling issue']}")
        print(f"  * 🧸 Possible: {stats['impact_levels']['Possibly affects cyclists']}")
        print(f"  * 📍 Other: {stats['impact_levels']['Not cycling-specific']}")
        print()
        print(f"## 🔥 TOP HOTSPOTS")
        if output_data["hotspots"]:
            for hs in output_data["hotspots"]:
                print(f"* **{hs['segment']}**: {hs['count']} issues reported")
        else:
            print("No street hotspots found in this period.")
        print()
        print(f"## 🚨 FEATURED CRITICAL ISSUES (Limit: {args.limit})")
        for idx, issue in enumerate(output_data["featured_issues"]):
            print(f"### {idx+1}. {issue['category']} at {issue['street']} (ID: #{issue['id']})")
            print(f"* **Description**: \"{issue['description']}\"")
            print(f"* **Impact Level**: {issue['impact']} (Score: {issue['score']} pts)")
            print(f"* **Distance to Bike Path**: {issue['distance_to_path_m']} meters")
            print(f"* **State**: {issue['state']}")
            print(f"* **Coordinates**: {issue['coords']}")
            print(f"* **AI Context (DE)**: {issue['explanation']}")
            print()

if __name__ == "__main__":
    main()
