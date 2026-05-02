import streamlit as st
import pandas as pd
import re
import io
import plotly.express as px

# Severity classification

CRITICAL_RULES = ['SPACE', 'ENCL', 'WIDTH', 'ANTENNA', 'PITCH']

def get_severity(rule: str, count: int) -> str:
    rule_upper = rule.upper()
    if any(p in rule_upper for p in CRITICAL_RULES) and count > 10:
        return 'CRITICAL'
    elif count > 0:
        return 'WARNING'
    return 'INFO'

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
            entry['severity'] = get_severity(entry['rule'], int(entry['count']))
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
        #col3.metric("Status", "READY" if total_errors == 0 else "ACTION REQUIRED")
        critical_count = master_df[master_df['severity'] == 'CRITICAL']['count'].sum()
        col3.metric("Status", "✅ READY" if critical_count == 0 else f"🚨 {critical_count} CRITICAL")

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
        st.subheader("Violations by Category and Severity")

        category_df = (
            master_df.groupby(['Category', 'severity'])['count']
            .sum().reset_index()
)

        fig1 = px.bar(
            category_df,
            x='Category', y='count', color='severity',
            color_discrete_map={
            'CRITICAL': '#ef4444',
            'WARNING':  '#f97316',
            'INFO':     '#22c55e'
            },
            labels={'count': 'Violation Count', 'Category': 'Rule Category'},
            title='DRC Violations by Category and Severity'
        )
        fig1.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            legend_title='Severity'
        )
        st.plotly_chart(fig1, use_container_width=True)
        # Layer-level breakdown
        st.subheader("Violations by Layer")
        layer_df = (
            master_df.groupby(['layer', 'severity'])['count']
            .sum().reset_index()
            .sort_values('count', ascending=False)
        )
        fig2 = px.bar(
            layer_df,
            x='layer', y='count', color='severity',
            color_discrete_map={
                'CRITICAL': '#ef4444',
                'WARNING':  '#f97316',
                'INFO':     '#22c55e'
            },
            labels={'count': 'Violation Count', 'layer': 'Layer'},
            title='DRC Violations by Layer'
        )
        fig2.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig2, use_container_width=True)


        # 4. Detailed View and Export
        with st.expander("View Raw Data"):
            st.dataframe(master_df)

        # Download button OUTSIDE the expander
        csv = master_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Full CSV", data=csv,
                   file_name="drc_full_report.csv", mime="text/csv")
    else:
        st.warning("No DRC violations found in the uploaded files.")
