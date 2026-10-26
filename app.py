import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Page Layout Configuration
st.set_page_config(
    page_title="Client Ledger Statement (Repo B)",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Client Ledger & Statement System")
st.caption("Repository B: Live Client Statement & Ledger Viewer")

# Connect to Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Load data with caching (refreshes every 10 seconds)
@st.cache_data(ttl=10)
def load_ledger_data():
    return conn.read(ttl="10s")

try:
    df = load_ledger_data()
except Exception as e:
    st.error(f"⚠️ Failed to connect to Google Sheets. Please verify your secrets configuration. Details: {e}")
    st.stop()

if df.empty:
    st.info("📌 The ledger spreadsheet is currently empty. Entries from Repository A will appear here automatically.")
elif "Client Code" not in df.columns:
    st.error("❌ The column 'Client Code' was not found in your spreadsheet. Please check your sheet headers.")
else:
    # Clean data types
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Units"] = pd.to_numeric(df["Units"], errors="coerce").fillna(0)
    df["Transaction Amount"] = pd.to_numeric(df["Transaction Amount"], errors="coerce").fillna(0.0)

    # Sidebar Selection for Clients
    client_list = sorted(df["Client Code"].dropna().astype(str).unique().tolist())
    
    st.sidebar.header("🔍 Client Filter")
    selected_client = st.sidebar.selectbox("Select Client Code", options=client_list)

    # Filter records for selected client code
    client_df = df[df["Client Code"].astype(str) == selected_client].copy()
    client_df = client_df.sort_values(by="Date", ascending=True)

    # Compute Running Balance
    client_df["Running Balance"] = client_df["Transaction Amount"].cumsum()

    # Main Dashboard Header
    st.subheader(f"📋 Ledger Statement for Client Code: `{selected_client}`")

    # Metrics Summary Row
    total_units = int(client_df["Units"].sum())
    total_amount = client_df["Transaction Amount"].sum()
    total_entries = len(client_df)

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Transactions", f"{total_entries}")
    m2.metric("Total Volume / Units", f"{total_units:,}")
    m3.metric("Cumulative Balance", f"NRs / Rs {total_amount:,.2f}")

    st.markdown("---")

    # Format dataframe for clean presentation
    display_df = client_df.copy()
    display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")

    columns_to_display = ["Date", "Client Code", "Client Name", "Units", "Transaction Amount", "Running Balance", "Notes"]
    available_columns = [col for col in columns_to_display if col in display_df.columns]

    # Render Data Table
    st.dataframe(
        display_df[available_columns],
        use_container_width=True,
        hide_index=True
    )

    # Export / Download Button
    csv_export = display_df[available_columns].to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download Ledger for {selected_client} (CSV)",
        data=csv_export,
        file_name=f"ledger_{selected_client}.csv",
        mime="text/csv"
    )
