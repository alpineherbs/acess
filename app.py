import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Alpine Herbs — Party Ledger Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Alpine Herbs Pvt. Ltd. — Client Ledger Dashboard")
st.caption("Repository B: Live Party Outstanding & Recovery Tracking System")

# Connect to Central Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def load_data():
    return conn.read(ttl="10s")

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ Failed to connect to Google Sheet: {e}")
    st.stop()

if df.empty:
    st.info("📌 The ledger spreadsheet is currently empty.")
else:
    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    category_filter = st.sidebar.multiselect(
        "Category / Status", 
        options=df["Category / Status"].dropna().unique().tolist(),
        default=df["Category / Status"].dropna().unique().tolist()
    )
    
    district_filter = st.sidebar.multiselect(
        "District / Area",
        options=df["District / Area"].dropna().unique().tolist(),
        default=df["District / Area"].dropna().unique().tolist()
    )

    filtered_df = df[
        df["Category / Status"].isin(category_filter) & 
        df["District / Area"].isin(district_filter)
    ]

    # Client Code Selector
    client_list = ["ALL CLIENTS"] + sorted(filtered_df["Client Code"].dropna().astype(str).unique().tolist())
    selected_client = st.sidebar.selectbox("Select Client Code / Party", options=client_list)

    if selected_client != "ALL CLIENTS":
        display_df = filtered_df[filtered_df["Client Code"].astype(str) == selected_client]
    else:
        display_df = filtered_df

    # Summary Metrics
    total_outstanding = display_df["Outstanding Cash (NRs)"].sum()
    total_parties = len(display_df)
    bad_debt_total = display_df[display_df["Category / Status"] == "Bad Debt / Recovery"]["Outstanding Cash (NRs)"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Parties Filtered", f"{total_parties}")
    col2.metric("Total Outstanding Cash", f"NRs {total_outstanding:,.2f}")
    col3.metric("Bad Debt / Recovery Amount", f"NRs {bad_debt_total:,.2f}")

    st.markdown("---")

    # Display Table
    cols_to_show = ["Date", "Client Code", "District / Area", "Category / Status", "Party Name", "Address", "Mobile No.", "Outstanding Cash (NRs)", "Notes / Status"]
    avail_cols = [c for c in cols_to_show if c in display_df.columns]

    st.dataframe(display_df[avail_cols], use_container_width=True, hide_index=True)

    # Export Button
    csv = display_df[avail_cols].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Current Selection (CSV)",
        data=csv,
        file_name="alpine_herbs_filtered_ledger.csv",
        mime="text/csv"
    )
