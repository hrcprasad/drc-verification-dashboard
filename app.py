import streamlit as st
import pandas as pd
import re
import io
import plotly.express as px
import numpy as np

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

        # ── 4. ECO Convergence Trend (multi-file only) ─────────────────────
        if len(uploaded_files) > 1:
            st.subheader("📉 ECO Convergence Trend")
            st.caption("Upload multiple ECO run reports to track closure progress.")

            # Total violations per run
            trend_df = (
                master_df.groupby('filename')['count']
                .sum().reset_index()
                .rename(columns={'filename': 'run', 'count': 'total_violations'})
            )

            # Critical violations per run
            critical_trend = (
                master_df[master_df['severity'] == 'CRITICAL']
                .groupby('filename')['count']
                .sum().reset_index()
                .rename(columns={'filename': 'run', 'count': 'critical_violations'})
            )

            trend_df = trend_df.merge(critical_trend, on='run', how='left').fillna(0)
            trend_df['critical_violations'] = trend_df['critical_violations'].astype(int)

            # ── Linear regression prediction ───────────────────────────────
            x = np.arange(len(trend_df))
            y = trend_df['critical_violations'].values
            slope, intercept = np.polyfit(x, y, 1)

            if slope < 0:
                runs_to_zero = -intercept / slope
                remaining = max(0, runs_to_zero - len(x))
                st.info(
                    f"📊 **Convergence Prediction:** At current rate, "
                    f"approximately **{remaining:.1f} more ECO run(s)** needed "
                    f"to reach 0 critical violations."
                )
            elif slope == 0:
                st.warning("⚠️ No improvement detected across runs — violations are flat.")
            else:
                st.error("🚨 Violations are increasing across runs — regression detected!")

            # ── Trend line chart ───────────────────────────────────────────
            fig3 = px.line(
                trend_df,
                x='run',
                y=['total_violations', 'critical_violations'],
                markers=True,
                labels={'value': 'Violation Count', 'run': 'ECO Run', 'variable': 'Type'},
                title='Violation Convergence Across ECO Runs',
                color_discrete_map={
                    'total_violations':    '#f97316',
                    'critical_violations': '#ef4444'
                }
            )
            fig3.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                legend_title='Violation Type'
            )
            st.plotly_chart(fig3, use_container_width=True)

            # ── Run delta table ────────────────────────────────────────────
            st.subheader("Run-over-Run Delta")
            trend_df['delta'] = trend_df['critical_violations'].diff().fillna(0).astype(int)
            trend_df['trend'] = trend_df['delta'].apply(
                lambda d: '🟢 IMPROVING' if d < 0 else ('🔴 REGRESSING' if d > 0 else '🟡 FLAT')
            )
            st.dataframe(
                trend_df[['run', 'total_violations', 'critical_violations', 'delta', 'trend']],
                use_container_width=True
            )

        else:
            st.info("💡 Upload multiple ECO run reports to unlock convergence trend analysis.")

        # 4. Detailed View and Export
        with st.expander("View Raw Data"):
            st.dataframe(master_df)

        # Download button OUTSIDE the expander
        csv = master_df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇️ Download Full CSV", data=csv,
                   file_name="drc_full_report.csv", mime="text/csv")
    else:
        st.warning("No DRC violations found in the uploaded files.")
