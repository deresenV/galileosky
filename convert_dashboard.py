import json
import re

# Пути к файлам
INPUT_DASHBOARD = "Электрика-1771182508445.json"
OUTPUT_DASHBOARD = "monitoring/grafana/dashboards/mercury_dashboard.json"

def convert_dashboard():
    with open(INPUT_DASHBOARD, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 1. Update Datasource
    def update_datasource(obj):
        if isinstance(obj, dict):
            if "datasource" in obj:
                if isinstance(obj["datasource"], dict):
                    if obj["datasource"].get("type") == "prometheus":
                        obj["datasource"] = {"type": "loki", "uid": "Loki"}
            for key, value in obj.items():
                update_datasource(value)
        elif isinstance(obj, list):
            for item in obj:
                update_datasource(item)

    update_datasource(data)

    # 2. Update Variables
    for var in data.get("templating", {}).get("list", []):
        if var["name"] == "imei":
            var["query"] = 'label_values({job="mercury_parser"}, imei)'
            var["definition"] = 'label_values({job="mercury_parser"}, imei)'
        elif var["name"] == "mercury_id":
            var["query"] = 'label_values({job="mercury_parser"}, mercury_id)'
            var["definition"] = 'label_values({job="mercury_parser"}, mercury_id)'
        
        if "current" in var:
            var["current"] = {}

    # 3. Update Targets (Queries)
    def update_targets(panels):
        for panel in panels:
            if "panels" in panel: # Row
                update_targets(panel["panels"])
                continue
            
            if "targets" not in panel:
                continue

            # Determine panel type
            panel_type = panel.get("type", "stat")
            
            for target in panel["targets"]:
                expr = target.get("expr", "")
                
                # Regex to capture metric name
                match = re.search(r'([a-zA-Z0-9_]+)\{', expr)
                if match:
                    metric_name = match.group(1)
                    
                    # Base Loki query
                    base_query = f'{{job="mercury_parser", mercury_id=~"$mercury_id", imei=~"$imei"}} | json | unwrap {metric_name} | __error__=""'
                    
                    if panel_type in ["timeseries", "graph"]:
                        # Graph: Range query with aggregation over interval
                        target["expr"] = f'max by (mercury_id, imei) (avg_over_time({base_query} [$__interval]))'
                        target["queryType"] = "range"
                        
                        # Connect null values for better visualization
                        if panel_type == "timeseries":
                            if "fieldConfig" not in panel: panel["fieldConfig"] = {}
                            if "defaults" not in panel["fieldConfig"]: panel["fieldConfig"]["defaults"] = {}
                            if "custom" not in panel["fieldConfig"]["defaults"]: panel["fieldConfig"]["defaults"]["custom"] = {}
                            panel["fieldConfig"]["defaults"]["custom"]["spanNulls"] = True
                        elif panel_type == "graph":
                            panel["nullPointMode"] = "connected"
                    else:
                        # Stat/Gauge: Instant query for "Current" value
                        # Use 5m lookback to ensure we catch the last push
                        target["expr"] = f'max by (mercury_id, imei) (last_over_time({base_query} [5m]))'
                        target["queryType"] = "instant"
                        # Remove 'range' param if present, as it conflicts or confuses
                        if "range" in target:
                            del target["range"]

                    target["editorMode"] = "code"

    update_targets(data.get("panels", []))

    # Update title and uid
    data["title"] = "Mercury 230 Dashboard (Loki)"
    data["uid"] = "mercury-230-loki"

    with open(OUTPUT_DASHBOARD, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Converted dashboard saved to {OUTPUT_DASHBOARD}")

if __name__ == "__main__":
    convert_dashboard()
