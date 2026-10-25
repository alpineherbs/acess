import streamlit as st
import pandas as pd
from github import Github
import json

# Set Page Config
st.set_page_config(
    page_title="Client Ledger Statement (Repo B)",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Client Ledger & Statement System")
st.caption("Repository B: Real-time ledger updates mapped by Client Code")

# Connect to GitHub
@st.cache_resource
def get_github_repo():
    try:
        g = Github(st.secrets["GITHUB_TOKEN"])
        return g.get_repo(st.secrets["GITHUB_REPO"])
    except Exception as e:
        st.error(f"Failed to connect to GitHub repository: {e}")
        return None

# Load Ledger Data from Shared JSON in GitHub
@st.cache_data(ttl=30)  # Auto refresh every 30 seconds
def fetch_ledger_data():
    repo = get_github_repo()
    if repo is None:
        return pd.DataFrame()
    
    file_path = st.secrets.get("DATA_FILE_PATH", "data/ledger_data.json")
    try:
        file_content = repo.get_contents(file_path)
        data = json.loads(file_content.decoded_content.decode("utf-8"))
        df = pd.DataFrame(data)
        
        # Ensure correct data types
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["units"] = pd.to_numeric(df["units"], errors="coerce").fillna(0)
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
            df = df.sort_values(by="date", ascending=True)
        return df
    except Exception as e:
        st.warning("No existing data file found or file is empty yet. Waiting for entries from Repository A.")
        return pd.DataFrame()

# Refresh button
col_title, col_btn = st.columns([4, 1])
with col_btn:
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# Load Data
df_ledger = fetch_ledger_data()

if df_ledger.empty:
    st.info("📌 No ledger entries found. Once data is submitted via Repository A, client statements will appear here.")
else:
    # Get List of Unique Clients
    client_list = sorted(df_ledger["client_code"].dropna().unique().tolist())
    
    # Sidebar Filters
    st.sidebar.header("Client Selector")
    selected_client = st.sidebar.selectbox("Select Client Code", options=client_list)
    
    # Filter Data for Selected Client
    client_df = df_ledger[df_ledger["client_code"] == selected_client].copy()
    
    # Compute Running Balance
    client_df["running_balance"] = client_df["amount"].cumsum()
    
    st.subheader(f"📋 Statement for Client: `{selected_client}`")
    
    # Metrics Row
    total_units = int(client_df["units"].sum())
    total_amount = client_df["amount"].sum()
    entry_count = len(client_df)
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Transactions", f"{entry_count}")
    m2.metric("Total Volume / Units", f"{total_units:,}")
    m3.metric("Cumulative Amount Balance", f"NRs / Rs {total_amount:,.2f}")
    
    st.markdown("---")
    
    # Client Ledger Table Format
    display_df = client_df.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    
    # Rename columns for presentation
    display_df = display_df.rename(columns={
        "date": "Date",
        "client_code": "Client Code",
        "units": "Units / Quantity",
        "amount": "Transaction Amount",
        "running_balance": "Running Balance",
        "notes": "Notes / Remarks"
    })
    
    # Display Data Table
    st.dataframe(
        display_df[["Date", "Client Code", "Units / Quantity", "Transaction Amount", "Running Balance", "Notes / Remarks"]],
        use_container_width=True,
        hide_index=True
    )
    
    # Download Ledger Option
    csv_data = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label=f"📥 Download {selected_client} Ledger CSV",
        data=csv_data,
        file_name=f"ledger_{selected_client}.csv",
        mime="text/csv"
    )
