import streamlit as st
import pandas as pd
import re
import io

# --- Core Logic: Parsing and Categorization ---
def parse_drc_content(content, filename):
    data = []
    pattern = r"RULECHECK\s+(?P<layer>\w+)\.(?P<rule>\w+)\s+\.+\s+TOTAL Result Count\s+=\s+(?P<count>\d+)"

    for line in content.splitlines():
        match = re.search(pattern, line)
        if match:
            entry = match.groupdict()
            entry['filename'] = filename

            # Categorization Logic
            rule_upper = entry['rule'].upper()
            layer_upper = entry['layer'].upper()

            if 'DENSITY' in rule_upper or 'DENSITY' in layer_upper:
                entry['Category'] = 'Density'
            elif 'ANTENNA' in rule_upper or 'ANTENNA' in layer_upper:
                entry['Category'] = 'Antenna'
            elif 'WIDTH' in rule_upper:
                entry['Category'] = 'Width'
            elif 'SPACE' in rule_upper or 'SEP' in rule_upper:
                entry['Category'] = 'Spacing'
            elif 'ENCL' in rule_upper:
                entry['Category'] = 'Enclosure'
            else:
                entry['Category'] = 'General'
            data.append(entry)
    return data

# --- Streamlit UI ---
st.set_page_config(page_title="VLSI Tape-out Dashboard", layout="wide")

st.title("🚀 Physical Verification Dashboard")
st.markdown("Upload your Calibre `.rpt` or `.summary` files to assess tape-out readiness.")

uploaded_files = st.file_uploader("Drag and drop DRC reports here", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        # Read file content as string
        stringio = io.StringIO(uploaded_file.getvalue().decode("utf-8"))
        content = stringio.read()
        all_data.extend(parse_drc_content(content, uploaded_file.name))

    if all_data:
        master_df = pd.DataFrame(all_data)
        master_df['count'] = master_df['count'].astype(int)

        # 1. High-Level Metrics
        total_errors = master_df['count'].sum()
        num_files = len(uploaded_files)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Blocks", num_files)
        col2.metric("Total Violations", total_errors)
        col3.metric("Status", "READY" if total_errors == 0 else "ACTION REQUIRED")

        # 2. Block-Level Status Table
        st.subheader("Block Status Summary")
        block_totals = master_df.groupby('filename')['count'].sum().reset_index()

        def get_status(x):
            if x == 0: return '✅ CLEAN'
            if x < 5: return '⚠️ WARNING'
            return '❌ FAIL'

        block_totals['Status'] = block_totals['count'].apply(get_status)
        st.table(block_totals)

        # 3. Categorized Breakdown
        st.subheader("Violations by Category")
        category_pivot = master_df.pivot_table(
            index='filename', columns='Category', values='count',
            aggfunc='sum', fill_value=0
        )
        st.bar_chart(category_pivot)

        # 4. Detailed View and Export
        with st.expander("View Raw Data"):
            st.dataframe(master_df)
            csv = master_df.to_csv(index=False).encode('utf-8')
            st.download_button("Download Full CSV", data=csv, file_name="drc_full_report.csv", mime="text/csv")
    else:
        st.warning("No DRC violations found in the uploaded files.")
