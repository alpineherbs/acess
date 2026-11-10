import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="ALPINE HERBS | Master Audit Dashboard",
    page_icon="🌿",
    layout="wide"
)

SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

# Refined Alpine Herbs Corporate Theme
st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
.block-container { 
    padding-top: 1.8rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 1560px; 
}
.main-header {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    padding: 16px 22px;
    border-radius: 8px;
    color: white;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.08);
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #C8DCCF;
    border-top: 3.5px solid #164E33;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.kpi-title { 
    font-size: 0.75rem; 
    font-weight: 700; 
    color: #4A6354; 
    text-transform: uppercase; 
    margin-bottom: 3px; 
}
.kpi-value { 
    font-size: 1.35rem; 
    font-weight: 800; 
    color: #0D2818; 
}
.kpi-sub { 
    font-size: 0.72rem; 
    color: #738C7D; 
    margin-top: 2px; 
}
</style>""", unsafe_allow_html=True)

# --- SAFE STRING & NUMERIC PARSERS ---
def clean_num(val):
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).replace("Rs.", "").replace("Rs", "").replace(",", "").strip()
    try:
        v = float(s)
        return 0.0 if (math.isnan(v) or math.isinf(v)) else v
    except Exception:
        return 0.0

def money(val):
    return f"Rs. {clean_num(val):,.2f}"

def find_column(df, candidates):
    """Case-insensitive, whitespace-tolerant column matcher."""
    if df.empty:
        return None
    cols_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand.strip().lower() in cols_map:
            return cols_map[cand.strip().lower()]
    return None

# --- RESILIENT DATA LOADER ---
# Reads data as string first to prevent losing zero-padded codes, IDs, or invoice numbers
def fetch_sheet_tab(tab_name_candidates):
    for tab in tab_name_candidates:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab.replace(' ', '%20')}"
        try:
            df = pd.read_csv(url, dtype=str)
            if not df.empty:
                # Strip extra whitespaces from column headers
                df.columns = [str(c).strip() for c in df.columns]
                
                # Remove unneeded 'Unnamed' empty columns
                valid_cols = [c for c in df.columns if not (c.startswith("Unnamed:") and df[c].isna().all())]
                df = df[valid_cols]
                
                # Drop rows where every single cell is empty/NaN
                df = df.dropna(how="all", axis=0)
                df = df[~df.apply(lambda row: row.astype(str).str.strip().eq("").all() or row.astype(str).str.strip().eq("nan").all(), axis=1)]
                
                if not df.empty:
                    return df
        except Exception:
            continue
    return pd.DataFrame()

@st.cache_data(ttl=8)
def load_all_records():
    return {
        "Sales": fetch_sheet_tab(["Sales"]),
        "Collections": fetch_sheet_tab(["Collections", "Receipts", "Cash Collections"]),
        "Returns": fetch_sheet_tab(["Returns", "Goods Return", "Goods Returns"]),
        "Expenses": fetch_sheet_tab(["Expenses", "Operating Expenses"]),
        "Advances": fetch_sheet_tab(["Staff Advances", "Advances", "Staff"])
    }

raw_data = load_all_records()
sales_df = raw_data["Sales"].copy()
col_df   = raw_data["Collections"].copy()
ret_df   = raw_data["Returns"].copy()
exp_df   = raw_data["Expenses"].copy()
adv_df   = raw_data["Advances"].copy()

# --- TOP HEADER BANNER ---
st.markdown("""
<div class="main-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="margin:0; font-weight:800; font-size:1.5rem; color:#FFFFFF;">🌿 ALPINE HERBS PVT. LTD.</h2>
            <div style="font-size:0.84rem; color:#D3E6DA; margin-top:2px;">
                CENTRAL OPERATIONS AUDIT & LIVE MONITORING (REPOSITORY B) &nbsp;|&nbsp; BIRGUNJ, NEPAL
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR: REFRESH & SEARCH CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Live Controls")
    if st.button("⚡ Force Live Refresh", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### 🔍 Filter Audit Data")

    # Representative / MR Filter
    mr_pool = []
    for d in [sales_df, col_df, ret_df, exp_df, adv_df]:
        c = find_column(d, ["MR Name", "Staff Name", "Personnel Name", "MR", "Rep Name"])
        if c:
            mr_pool.extend(d[c].dropna().astype(str).str.strip().tolist())
    clean_mrs = sorted(list(set([m for m in mr_pool if m and m.lower() not in ("nan", "none", "")])))
    sel_mr = st.selectbox("Filter by Representative", ["All Staff / MRs"] + clean_mrs)

    # Date Filter
    date_pool = []
    for d in [sales_df, col_df, ret_df, exp_df, adv_df]:
        c = find_column(d, ["Date (A.D.)", "Date", "A.D. Date", "Date(A.D.)"])
        if c:
            date_pool.extend(d[c].dropna().astype(str).str.strip().tolist())
    clean_dates = sorted(list(set([dt for dt in date_pool if dt and dt.lower() not in ("nan", "none", "")])), reverse=True)
    sel_date = st.selectbox("Filter by Date (A.D.)", ["All Dates"] + clean_dates)

    # Free-text Search Filter
    query = st.text_input("Search (Invoice, Chemist, Town)", placeholder="e.g. Naresh, INV-01").strip().lower()

# --- FILTERING FUNCTION ---
def filter_df(df):
    if df.empty:
        return df
    filtered = df.copy()

    # Apply MR filter
    if sel_mr != "All Staff / MRs":
        c_mr = find_column(filtered, ["MR Name", "Staff Name", "Personnel Name", "MR", "Rep Name"])
        if c_mr:
            filtered = filtered[filtered[c_mr].astype(str).str.strip() == sel_mr]

    # Apply Date filter
    if sel_date != "All Dates":
        c_dt = find_column(filtered, ["Date (A.D.)", "Date", "A.D. Date", "Date(A.D.)"])
        if c_dt:
            filtered = filtered[filtered[c_dt].astype(str).str.strip() == sel_date]

    # Apply Global Text Search
    if query:
        mask = filtered.apply(lambda row: row.astype(str).str.lower().str.contains(query, regex=False).any(), axis=1)
        filtered = filtered[mask]

    return filtered

f_sales = filter_df(sales_df)
f_col   = filter_df(col_df)
f_ret   = filter_df(ret_df)
f_exp   = filter_df(exp_df)
f_adv   = filter_df(adv_df)

# --- RECONCILIATION TOTALS (MATCHING REPO A EXACT FORMULAS) ---
# 1. Sales
col_stot  = find_column(f_sales, ["Total Sale (Rs.)", "Total Sale", "Total Billed", "Total", "total_sale"])
col_scash = find_column(f_sales, ["Cash Recd (Rs.)", "Cash Collected", "Cash Recd", "cash_collected", "Cash"])
col_scred = find_column(f_sales, ["Credit Given (Rs.)", "Credit Given", "Credit", "credit_given"])

tot_sales_val  = f_sales[col_stot].apply(clean_num).sum() if col_stot else 0.0
tot_sales_cash = f_sales[col_scash].apply(clean_num).sum() if col_scash else 0.0
tot_sales_cred = f_sales[col_scred].apply(clean_num).sum() if col_scred else 0.0

# 2. Collections / Receipts
col_camt = find_column(f_col, ["Amount Collected (Rs.)", "Amount Collected", "Amount", "amount"])
tot_rec_cash = f_col[col_camt].apply(clean_num).sum() if col_camt else 0.0

# 3. Goods Returns
col_rtot = find_column(f_ret, ["Total Return (Rs.)", "Total Value", "Total Return", "Total", "total", "Amount"])
tot_returns = f_ret[col_rtot].apply(clean_num).sum() if col_rtot else 0.0

# 4. Outflows
col_eamt = find_column(f_exp, ["Amount (Rs.)", "Amount", "amount"])
tot_expenses = f_exp[col_eamt].apply(clean_num).sum() if col_eamt else 0.0

col_aamt = find_column(f_adv, ["Amount (Rs.)", "Amount", "amount"])
tot_advances = f_adv[col_aamt].apply(clean_num).sum() if col_aamt else 0.0

# Cash balance logic from Repo A
total_gross_cash = tot_sales_cash + tot_rec_cash
total_outflow    = tot_expenses + tot_advances
net_cash_balance = total_gross_cash - total_outflow

# --- FINANCIAL KPI ROW ---
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">🛒 Total Billed Sales</div>
        <div class="kpi-value">{money(tot_sales_val)}</div>
        <div class="kpi-sub">Direct Cash: {money(tot_sales_cash)}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#2D7D52;">
        <div class="kpi-title">💵 Total Cash Recd</div>
        <div class="kpi-value" style="color:#164E33;">{money(total_gross_cash)}</div>
        <div class="kpi-sub">Receipt Dues: {money(tot_rec_cash)}</div>
    </div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#A04000;">
        <div class="kpi-title">📑 Credit Outstanding</div>
        <div class="kpi-value" style="color:#A04000;">{money(tot_sales_cred)}</div>
        <div class="kpi-sub">Returns Value: {money(tot_returns)}</div>
    </div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#800000;">
        <div class="kpi-title">🏢 Total Disbursed</div>
        <div class="kpi-value" style="color:#800000;">{money(total_outflow)}</div>
        <div class="kpi-sub">Ops: {money(tot_expenses)} | Adv: {money(tot_advances)}</div>
    </div>""", unsafe_allow_html=True)
with k5:
    net_col = "#0D2818" if net_cash_balance >= 0 else "#900C3F"
    st.markdown(f"""<div class="kpi-card" style="border-top-color:{net_col}; background:#F4FAF6;">
        <div class="kpi-title">💰 Net Cash Balance</div>
        <div class="kpi-value" style="color:{net_col};">{money(net_cash_balance)}</div>
        <div class="kpi-sub">Closing Cash in Hand</div>
    </div>""", unsafe_allow_html=True)

st.write("")

# --- TABLE RENDERER ---
def show_section(df, tab_name, description):
    st.markdown(f"##### {description}")
    if not df.empty:
        # Display table preserving all original columns entered in Repo A
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # CSV Export Option
        buf = BytesIO()
        df.to_csv(buf, index=False)
        st.download_button(
            label=f"📥 Download {tab_name} ({len(df)} rows)",
            data=buf.getvalue(),
            file_name=f"{tab_name.lower().replace(' ', '_')}_export.csv",
            mime="text/csv",
            key=f"dl_{tab_name}"
        )
    else:
        st.info(f"ℹ️ No records found for '{tab_name}'. If data was just submitted from Repo A, click '⚡ Force Live Refresh' in the sidebar.")

# --- TABS FOR ALL 5 FEEDS ---
t1, t2, t3, t4, t5 = st.tabs([
    f"🛒 1. Sales Ledger ({len(f_sales)})",
    f"💵 2. Dues Collections ({len(f_col)})",
    f"🔄 3. Goods Return ({len(f_ret)})",
    f"🏢 4. Operating Expenses ({len(f_exp)})",
    f"👥 5. Staff Advances ({len(f_adv)})"
])

with t1:
    show_section(f_sales, "Sales", "Invoiced Product Sales, Promotional FOC, & Cash/Credit Ledger")

with t2:
    show_section(f_col, "Collections", "Customer Payment Receipts & Recovered Dues")

with t3:
    show_section(f_ret, "Returns", "Client Returned Stock, Near Expiry, & Breakages")

with t4:
    show_section(f_exp, "Expenses", "Route Operational Expenses & Fuel/Logistics Disbursed")

with t5:
    show_section(f_adv, "Staff Advances", "Field Staff Allowances & Tour Advances")
