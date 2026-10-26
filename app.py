import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Alpine Herbs — Party Ledger Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Alpine Herbs Pvt. Ltd. — Client Ledger Dashboard")
st.caption("Repository B: Live Party Outstanding & Recovery Tracking System")

# Google Sheet CSV Export Link
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=10)
def load_data():
    # Reads the public Google Sheet directly without needing st.connection or secrets
    return pd.read_csv(CSV_URL)

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ Failed to connect to Google Sheet: {e}")
    st.info("💡 Tip: Ensure your Google Sheet sharing setting is set to **'Anyone with the link can view'**.")
    st.stop()

if df.empty:
    st.info("📌 The ledger spreadsheet is currently empty.")
else:
    # Clean numeric columns
    if "Outstanding Cash (NRs)" in df.columns:
        df["Outstanding Cash (NRs)"] = pd.to_numeric(df["Outstanding Cash (NRs)"], errors="coerce").fillna(0.0)

    # Sidebar Filters
    st.sidebar.header("🔍 Filters")
    
    categories = df["Category / Status"].dropna().unique().tolist() if "Category / Status" in df.columns else []
    category_filter = st.sidebar.multiselect("Category / Status", options=categories, default=categories)
    
    districts = df["District / Area"].dropna().unique().tolist() if "District / Area" in df.columns else []
    district_filter = st.sidebar.multiselect("District / Area", options=districts, default=districts)

    if categories or districts:
        filtered_df = df[
            df["Category / Status"].isin(category_filter) & 
            df["District / Area"].isin(district_filter)
        ]
    else:
        filtered_df = df

    # Client Code Selector
    client_codes = sorted(filtered_df["Client Code"].dropna().astype(str).unique().tolist()) if "Client Code" in filtered_df.columns else []
    client_list = ["ALL CLIENTS"] + client_codes
    selected_client = st.sidebar.selectbox("Select Client Code / Party", options=client_list)

    if selected_client != "ALL CLIENTS":
        display_df = filtered_df[filtered_df["Client Code"].astype(str) == selected_client]
    else:
        display_df = filtered_df

    # Summary Metrics
    total_outstanding = display_df["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in display_df.columns else 0.0
    total_parties = len(display_df)
    
    bad_debt_mask = display_df["Category / Status"] == "Bad Debt / Recovery" if "Category / Status" in display_df.columns else False
    bad_debt_total = display_df[bad_debt_mask]["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in display_df.columns else 0.0

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
