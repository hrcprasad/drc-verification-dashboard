import pandas as pd
import re
import os

def parse_drc_report(report_full_path):
    # Use os.path.abspath to ensure we are looking at the absolute location
    absolute_path = os.path.abspath(report_full_path)

    if not os.path.exists(absolute_path):
        print(f"Error: Path not found -> {absolute_path}")
        return None

    data = []
    pattern = r"RULECHECK\s+(?P<layer>\w+)\.(?P<rule>\w+)\s+\.+\s+TOTAL Result Count\s+=\s+(?P<count>\d+)"

    try:
        with open(absolute_path, 'r') as file:
            for line in file:
                match = re.search(pattern, line)
                if match:
                    data.append(match.groupdict())

        df = pd.DataFrame(data)
        if not df.empty:
            df['count'] = df['count'].astype(int)
            return df
        return None

    except Exception as e:
        print(f"Failed to read file at {absolute_path}: {e}")
        return None

# --- Main Execution ---
# You can now provide the full path to any file on your system
target_file = "/home/hrcprasad/code/datamites/VLSI/Files/drc_summary.rpt"
# For Windows, (you can give a Windows path)
# it would look like: "C:/Users/chaitanya/Documents/drc_summary.rpt"

drc_results = parse_drc_report(target_file)

if drc_results is not None:
    print(f"Successfully parsed: {os.path.basename(target_file)}")
    print(drc_results.groupby('layer')['count'].sum())
