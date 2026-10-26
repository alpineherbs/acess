import streamlit as st
import pandas as pd

st.set_page_config(page_title="ALPINE HERBS | Master Dashboard", page_icon="📈", layout="wide")

SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

SALES_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sales"
EXPENSES_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Expenses"
ADVANCES_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Staff%20Advances"

@st.cache_data(ttl=5)
def load_data():
    try:
        sales_df = pd.read_csv(SALES_CSV_URL)
    except Exception:
        sales_df = pd.DataFrame()

    try:
        expenses_df = pd.read_csv(EXPENSES_CSV_URL)
    except Exception:
        expenses_df = pd.DataFrame()

    try:
        advances_df = pd.read_csv(ADVANCES_CSV_URL)
    except Exception:
        advances_df = pd.DataFrame()

    return sales_df, expenses_df, advances_df

sales_df, expenses_df, advances_df = load_data()

st.markdown("""
<div style="background: linear-gradient(135deg, #0D2818 0%, #164E33 100%); color: white; padding: 1.2rem 1.8rem; border-radius: 10px; margin-bottom: 1.2rem;">
    <h2 style="margin:0; color:white;">🌿 ALPINE HERBS PVT. LTD. - Master Analytics (Repository B)</h2>
    <p style="margin:0; color:#D3E6DA; font-size:0.85rem;">Centralized Field Operations & Real-Time Performance Dashboard</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Dashboard Controls")
    if st.button("⚡ Force Swift Refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.info("Repository B pulls live records directly from your multi-tab Google Sheet database.")

# Display Sales Tab Data
st.subheader("📦 Sales & Collections Master Feed")
if not sales_df.empty:
    st.dataframe(sales_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ No sales data found in the 'Sales' tab yet. Submit a report from Repository A to populate this view.")

# Display Expenses Tab Data
st.subheader("💸 Operating Expenses Master Feed")
if not expenses_df.empty:
    st.dataframe(expenses_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ No expense records found in the 'Expenses' tab yet.")

# Display Staff Advances Tab Data
st.subheader("👤 Staff Advances Master Feed")
if not advances_df.empty:
    st.dataframe(advances_df, use_container_width=True, hide_index=True)
else:
    st.info("ℹ️ No staff advance records found in the 'Staff Advances' tab yet.")
