import streamlit as st
import pandas as pd
import requests
import datetime
import time
import math
import io

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Alpine Herbs | Client 360° Audit Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# SPREADSHEET ID & APPS SCRIPT WEBHOOK URL
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"
# Paste your deployed Google Apps Script Web App URL here (same as Repo A)
WEBHOOK_URL = "YOUR_APPS_SCRIPT_WEBHOOK_URL_HERE"

# --- BRANDING & STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { 
        padding-top: 1.2rem !important; 
        padding-bottom: 2.5rem !important; 
        max-width: 1480px; 
    }
    
    /* Top Brand Header */
    .brand-header {
        background: linear-gradient(135deg, #092013 0%, #164E33 60%, #1e6b46 100%);
        padding: 18px 24px;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 16px rgba(9, 32, 19, 0.12);
        margin-bottom: 1.3rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .brand-title {
        font-size: 1.45rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        color: #C3E2D0;
        margin-top: 4px;
    }
    .status-badge {
        background: rgba(255, 255, 255, 0.15);
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }

    /* Client Profile Card */
    .client-hero {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 6px solid #164E33;
        padding: 18px 22px;
        border-radius: 10px;
        margin-bottom: 1.2rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
    }

    /* Modern KPI Cards */
    .kpi-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-top: 3.5px solid #164E33;
        border-radius: 8px;
        padding: 14px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .kpi-title { 
        font-size: 0.72rem; 
        font-weight: 700; 
        color: #64748B; 
        text-transform: uppercase; 
        letter-spacing: 0.04em;
        margin-bottom: 4px; 
    }
    .kpi-value { 
        font-size: 1.35rem; 
        font-weight: 800; 
        color: #0F172A; 
    }
    .kpi-sub { 
        font-size: 0.74rem; 
        color: #94A3B8; 
        margin-top: 4px; 
    }
</style>
""", unsafe_allow_html=True)

# --- MASTER CLIENT LEDGER (FALLBACK DATA) ---
CLIENTS_DATA = """name,code,area,district,phone,dues
Naresh Medical,BAR-001,Kalaiya,Bara,9807267001,3100
Mahir Health Clinic,BAR-002,Jeetpur,Bara,9807100296,8165
Dev Medical,BAR-003,Kalaiya,Bara,9845227985,1500
Nirajan Pharmacy,BAR-004,Bakuliya,Bara,9804242586,550
Hariom Medical,BAR-005,Kolvi,Bara,9811229323,2300
S.K.S Pharma,BAR-006,Parsauni,Bara,,1175
Aayan First Aid Center,BAR-007,Simara,Bara,,2060
Rupa Medical Hall,BAR-008,Simara,Bara,,5515
Sanjeevani Clinic,BAR-009,Simara,Bara,9845130209,2195
Ale Health Clinic,BAR-010,Ganj Bhawanipur,Bara,,1645
Alex Medical Hall,BAR-011,Bagrampur,Bara,,18000
Kaliyani Medical Hall,BAR-012,Kolvi,Bara,,15580
Shohalal Medical Hall,BAR-013,Ganj Bhawanipur,Bara,9814286651,7175
Everest Health Clinic,BAR-014,Kalaiya,Bara,,2635
Roman Surgical,BAR-015,Khopawa,Bara,9821231370,1660
Nimash Medical,BAR-016,Simara,Bara,9845120836,4620
Advance Poli Clinic,BAR-017,Raghunathpur,Bara,9809153231,4310
Prithvi Medical Hall,BAR-018,Jaitapur,Bara,,6745
Safe Life Hospital,BAR-019,Benauli,Bara,,740
Alina Health Clinic,BAR-020,Kalaiya,Bara,,8250
Hargendra Pande Medical,BAR-021,Rautahar,Bara,,500
Jungbahadur Medical,BAR-022,Bagrampur,Bara,,200
Aarabh Pharmacy,BAR-023,Nijgadh,Bara,9855019764,36725
Aarabh Pharmacy (Narayani),BAR-024,Nijgadh,Bara,9855019764,25915
Sanniya Medical Hall,BAR-025,Jeetpur,Bara,,3460
Bala Ji Medical Hall,BAR-026,Aarnawa Chouk,Bara,,3195
Sapna Health Clinic,BAR-027,Bariyarpur,Bara,,1365
Gudi Pharmacy,BAR-028,Bariyarpur,Bara,,0
OM Shivsakti Pharmacy,BAR-029,Kalaiya,Bara,,3680
Aditi Pharmacy,PAR-001,Manwa Bazar,Parsa,,500
Ashok Medical Hall,PAR-002,Naukatola,Parsa,,12230
Sudama Surgical,PAR-003,Neutan,Parsa,,20200
B.S Health Clinic,PAR-004,Paterwa,Parsa,,24665
Pandey Medical Hall,PAR-005,Badanihar,Parsa,,7065
Bhawani Medical Hall,PAR-006,Bharatwa,Parsa,,9950
Chandip Medical Hall,PAR-007,Kathmandu Tol,Parsa,,0
Dinamik Pharma,PAR-008,Sano Sugauli,Parsa,,15815
Everest Pharmacy,PAR-009,Birwa Chouk,Parsa,,0
Fatepur Health Clinic,PAR-010,Fatepur,Parsa,,0
Gadi Mai Medical Hall,PAR-011,Pachgawa,Parsa,,0
Ganesh Srestha,PAR-012,Birgunj,Parsa,,63390
Harnaiya Aashirvad Medical,PAR-013,Harnaiya,Parsa,,4565
Madhav Medical Hall,PAR-014,Pachgawa,Parsa,,0
Nawal Kishor Medical Hall,PAR-015,Pachgawa,Parsa,,0
Nausad Medical Hall,PAR-016,Rangapur,Parsa,,0
Kohinoor Medical Hall,PAR-017,Milan Chouk,Parsa,,0
Sibil Medical Hall,PAR-018,Milan Chouk,Parsa,,0
Noor Tamana Health Clinic,PAR-019,Derbana,Parsa,,0
Aftab Medical Hall,PAR-020,Derbana,Parsa,,0
Pandey Medical Hall (Murli),PAR-021,Murli,Parsa,,700
Puja Medical Hall,PAR-022,Fatepur,Parsa,,1030
Raina Health Clinic,PAR-023,Veda Tol,Parsa,,3672
Rihansh Medical Hall,PAR-024,Birgunj,Parsa,,1740
Roshan Pharmacy,PAR-025,Birgunj,Parsa,,74290
Samir Medical Hall,PAR-026,Pachgawa,Parsa,,0
Sandip Medical Hall,PAR-027,Langada Chouk,Parsa,,30195
Sohil Medical Hall,PAR-028,Pokhariya,Parsa,,11600
Tarai Medical Hall,PAR-029,Manwa Bazar,Parsa,,235
Tarkeshwar Medical Hall,PAR-030,Nagwa,Parsa,,8885
Jitendra Health Clinic,PAR-031,Mahuwan,Parsa,,4565
Anshari Medical Hall,PAR-032,Derbana,Parsa,,0
Jay Shree Gadhi Mai Medical,PAR-033,Lautan,Parsa,,1575
Dinanath Medical Hall,PAR-034,Harpur,Parsa,,1740
Shahu Pharmacy,PAR-035,Dokaila,Parsa,,0
G.K.S Pharmacy,PAR-036,Narahi Bazar,Parsa,,0
Bagmorcha Mai Medical,PAR-037,Bagmorcha,Parsa,,0
Pushpa Medical Hall,PAR-038,Kathariya,Parsa,,105
Satiya Health Clinic,PAR-039,Lautan,Parsa,,0
Anil Medical Hall,PAR-040,Gadwal,Parsa,,0
Harnaiya City Hospital,PAR-041,Harnaiya,Parsa,,0"""

# --- UTILITIES ---
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

def find_col(df, candidates):
    if df.empty:
        return None
    cols_map = {str(c).strip().lower().replace("_", " "): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower().replace("_", " ")
        if key in cols_map:
            return cols_map[key]
    return None

# --- RESILIENT DATA LOADER (WEBHOOK DIRECT + CACHE-BUSTED CSV) ---
def fetch_sheet_tab_cached_busted(tab_name_candidates):
    """Fetches Google Sheet tab with microsecond cache busting query."""
    timestamp = int(time.time() * 1000)
    for tab in tab_name_candidates:
        urls = [
            f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab.replace(' ', '%20')}&_cb={timestamp}",
            f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&sheet={tab.replace(' ', '%20')}&_cb={timestamp}"
        ]
        for url in urls:
            try:
                df = pd.read_csv(url, dtype=str)
                if not df.empty:
                    df.columns = [str(c).strip() for c in df.columns]
                    valid_cols = [c for c in df.columns if not (c.startswith("Unnamed:") and df[c].isna().all())]
                    df = df[valid_cols].dropna(how="all", axis=0)
                    df = df[~df.apply(lambda r: r.astype(str).str.strip().eq("").all() or r.astype(str).str.strip().eq("nan").all(), axis=1)]
                    if not df.empty:
                        return df
            except Exception:
                continue
    return pd.DataFrame()

@st.cache_data(ttl=5)
def load_all_records():
    """
    1. Attempts to load direct JSON data via WEBHOOK_URL (Zero CDN cache).
    2. Falls back to timestamp cache-busted direct Google Sheets CSV.
    """
    timestamp = int(time.time() * 1000)
    
    # Try Webhook direct GET if configured
    if WEBHOOK_URL and WEBHOOK_URL != "YOUR_APPS_SCRIPT_WEBHOOK_URL_HERE":
        try:
            resp = requests.get(f"{WEBHOOK_URL}?action=readAll&_t={timestamp}", timeout=8)
            if resp.status_code == 200:
                payload = resp.json()
                if payload.get("status") == "success" and "data" in payload:
                    d = payload["data"]
                    return {
                        "Clients": d.get("clients", []),
                        "Sales": pd.DataFrame(d.get("sales", [])),
                        "Collections": pd.DataFrame(d.get("collections", [])),
                        "Returns": pd.DataFrame(d.get("returns", [])),
                        "Expenses": pd.DataFrame(d.get("expenses", [])),
                        "Advances": pd.DataFrame(d.get("advances", [])),
                        "Source": "⚡ Live Webhook Web App"
                    }
        except Exception:
            pass  # Fall back to CSV

    # Fallback to cache-busted Google Sheets CSV
    live_clients_df = fetch_sheet_tab_cached_busted(["Clients", "Client Directory", "Master Clients"])
    if not live_clients_df.empty and "name" in [c.lower() for c in live_clients_df.columns]:
        live_clients_df.columns = [str(c).strip().lower() for c in live_clients_df.columns]
        client_pool = live_clients_df.fillna("").to_dict("records")
    else:
        client_pool = pd.read_csv(io.StringIO(CLIENTS_DATA.strip()), dtype=str).fillna("").to_dict("records")
    
    for c in client_pool:
        c["dues"] = clean_num(c.get("dues", 0.0))

    return {
        "Clients": client_pool,
        "Sales": fetch_sheet_tab_cached_busted(["Sales", "Sales Log", "Daily Sales"]),
        "Collections": fetch_sheet_tab_cached_busted(["Collections", "Receipts", "Cash Collections", "Dues"]),
        "Returns": fetch_sheet_tab_cached_busted(["Returns", "Goods Return", "Goods Returns"]),
        "Expenses": fetch_sheet_tab_cached_busted(["Expenses", "Operating Expenses", "Field Expenses"]),
        "Advances": fetch_sheet_tab_cached_busted(["Staff Advances", "Advances", "Staff"]),
        "Source": "🔄 Cache-Busted Google Sheets Export"
    }

data_store = load_all_records()
master_clients = data_store["Clients"]
sales_df = data_store["Sales"].copy()
col_df   = data_store["Collections"].copy()
ret_df   = data_store["Returns"].copy()
exp_df   = data_store["Expenses"].copy()
adv_df   = data_store["Advances"].copy()
data_source_label = data_store.get("Source", "Online")

# Header Banner
st.markdown(f"""
<div class="brand-header">
    <div>
        <div class="brand-title">🌿 ALPINE HERBS PVT. LTD.</div>
        <div class="brand-subtitle">Central Operations & Client 360° Audit Dashboard (Repository B) | Birgunj, Nepal</div>
    </div>
    <div class="status-badge">{data_source_label}</div>
</div>
""", unsafe_allow_html=True)

# Merge Any New Chemist / Walk-in Names into Pool
known_names = set(str(c.get("name", "")).strip().lower() for c in master_clients)
combined_clients = master_clients.copy()

if not sales_df.empty:
    c_sname = find_col(sales_df, ["Client Name", "client_name", "Party Name", "Customer Name"])
    c_scode = find_col(sales_df, ["Client Code", "client_code", "Code"])
    c_sarea = find_col(sales_df, ["Address", "Area", "Town", "Territory"])
    if c_sname:
        for _, r in sales_df.iterrows():
            nm = str(r.get(c_sname, "")).strip()
            cd = str(r.get(c_scode, "NEW-000")).strip() if c_scode else "NEW-000"
            if nm and nm.lower() not in known_names and nm.lower() != "walk-in party":
                known_names.add(nm.lower())
                combined_clients.append({
                    "name": nm,
                    "code": cd,
                    "area": str(r.get(c_sarea, "Birgunj")).strip() if c_sarea else "Birgunj",
                    "district": "Parsa",
                    "phone": "",
                    "dues": 0.0
                })

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Live Sync Controls")
    if st.button("⚡ Force Live Fetch Now", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.caption(f"Last updated: {datetime.datetime.now().strftime('%H:%M:%S')}")
    st.markdown("---")
    st.markdown("### 🔍 Client Search & Route Filter")
    
    all_areas = sorted(list(set(str(c.get("area", "")).strip() for c in combined_clients if c.get("area"))))
    area_options = ["All Areas / Routes"] + all_areas
    filter_area = st.selectbox("Route / Area", area_options)

    if filter_area != "All Areas / Routes":
        filtered_clients = [c for c in combined_clients if str(c.get("area", "")).strip().lower() == filter_area.lower()]
    else:
        filtered_clients = combined_clients

    client_display_list = [f"{c.get('name')}  [{c.get('code', 'PAR-000')}] — 📍 {c.get('area', 'Local')}" for c in sorted(filtered_clients, key=lambda x: str(x.get('name', '')).lower())]
    if not client_display_list:
        client_display_list = ["No Clients Found [N/A]"]
        
    selected_client_str = st.selectbox("Select Chemist / Account", client_display_list)

# Resolve Selected Client
selected_client_name = selected_client_str.split("  [")[0].strip()
client_profile = next((c for c in combined_clients if str(c.get("name", "")).strip().lower() == selected_client_name.lower()), {
    "name": selected_client_name, "code": "PAR-000", "area": "Birgunj", "district": "Parsa", "phone": "", "dues": 0.0
})
client_code = str(client_profile.get("code", "")).strip().lower()

# --- REPO A SCHEMA-AWARE FILTERING FUNCTION ---
def filter_client_txns(df):
    if df.empty:
        return pd.DataFrame()
    c_name = find_col(df, ["Client Name", "client_name", "Party Name", "Customer Name"])
    c_code = find_col(df, ["Client Code", "client_code", "Code"])
    
    mask = pd.Series([False] * len(df), index=df.index)
    if c_name:
        mask = mask | (df[c_name].astype(str).str.strip().str.lower() == selected_client_name.lower())
    if c_code and client_code and client_code not in ["par-000", "bar-000", "new-000", "n/a", ""]:
        mask = mask | (df[c_code].astype(str).str.strip().str.lower() == client_code)
    return df[mask].copy()

cli_sales = filter_client_txns(sales_df)
cli_col   = filter_client_txns(col_df)
cli_ret   = filter_client_txns(ret_df)

# Financial Calculations
op_dues = clean_num(client_profile.get("dues", 0.0))

col_stot  = find_col(cli_sales, ["Total Sale", "Total Sale (Rs.)", "total_sale", "Total Billed", "Total", "Amount"])
col_scash = find_col(cli_sales, ["Cash Collected", "Cash Recd", "Cash Recd (Rs.)", "cash_collected", "Cash"])

tot_cli_billed = cli_sales[col_stot].apply(clean_num).sum() if col_stot and not cli_sales.empty else 0.0
tot_cli_direct_cash = cli_sales[col_scash].apply(clean_num).sum() if col_scash and not cli_sales.empty else 0.0

col_camt = find_col(cli_col, ["Amount Collected", "Amount Collected (Rs.)", "amount", "Amount"])
tot_cli_dues_paid = cli_col[col_camt].apply(clean_num).sum() if col_camt and not cli_col.empty else 0.0

col_rtot = find_col(cli_ret, ["Total Return", "Total Return (Rs.)", "total", "Total Value", "Amount"])
tot_cli_returns = cli_ret[col_rtot].apply(clean_num).sum() if col_rtot and not cli_ret.empty else 0.0

total_cash_paid = tot_cli_direct_cash + tot_cli_dues_paid
current_outstanding = op_dues + tot_cli_billed - total_cash_paid - tot_cli_returns

# --- CLIENT BANNER & FINANCIAL SUMMARY ---
phone_info = f" &nbsp;|&nbsp; 📞 <b>Phone:</b> {client_profile['phone']}" if client_profile.get('phone') else ""
st.markdown(f"""
<div class="client-hero">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="background:#164E33; color:white; padding:4px 10px; border-radius:6px; font-weight:700; font-size:0.82rem; letter-spacing:0.02em;">
                {client_profile.get('code', 'PAR-000')}
            </span>
            <span style="font-size:1.35rem; font-weight:800; color:#0F172A; margin-left:10px;">
                {client_profile.get('name')}
            </span>
            <div style="font-size:0.86rem; color:#475569; margin-top:6px;">
                📍 <b>Territory:</b> {client_profile.get('area', 'Birgunj')}, {client_profile.get('district', 'Parsa')} {phone_info}
            </div>
        </div>
        <div style="text-align:right;">
            <span style="font-size:0.75rem; text-transform:uppercase; color:#64748B; font-weight:700;">Account Status</span><br>
            <span style="color:{'#DC2626' if current_outstanding > 0 else '#164E33'}; font-weight:800; font-size:1.1rem;">
                {'⚠️ Outstanding Balance' if current_outstanding > 0 else '✅ Ledger Settled'}
            </span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI Cards
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">📜 Opening Dues</div>
        <div class="kpi-value">{money(op_dues)}</div>
        <div class="kpi-sub">Initial Ledger Balance</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">🛒 New Invoiced Sales</div>
        <div class="kpi-value">{money(tot_cli_billed)}</div>
        <div class="kpi-sub">{len(cli_sales)} line item(s) invoiced</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#164E33;">
        <div class="kpi-title">💵 Total Payments Recd</div>
        <div class="kpi-value" style="color:#164E33;">{money(total_cash_paid)}</div>
        <div class="kpi-sub">Delivery: {money(tot_cli_direct_cash)} | Dues: {money(tot_cli_dues_paid)}</div>
    </div>""", unsafe_allow_html=True)

with k4:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#7C3AED;">
        <div class="kpi-title">🔄 Returns / Damages</div>
        <div class="kpi-value" style="color:#7C3AED;">{money(tot_cli_returns)}</div>
        <div class="kpi-sub">{len(cli_ret)} item(s) credited back</div>
    </div>""", unsafe_allow_html=True)

with k5:
    due_color = "#DC2626" if current_outstanding > 0 else "#164E33"
    st.markdown(f"""<div class="kpi-card" style="border-top-color:{due_color}; background:#FAFCF8;">
        <div class="kpi-title">💰 Current Balance Payable</div>
        <div class="kpi-value" style="color:{due_color};">{money(current_outstanding)}</div>
        <div class="kpi-sub">Closing Outstanding Today</div>
    </div>""", unsafe_allow_html=True)

st.write("")

# --- BUILD DETAILED GRANULAR STATEMENT WITH ALL DETAILS ---
statement_rows = []

# 1. Opening Balance Entry
statement_rows.append({
    "Date (AD)": "Opening",
    "Miti (BS)": "-",
    "Ref / Invoice #": "INIT-DUES",
    "Client Code": client_profile.get("code", "PAR-000"),
    "Client Name": client_profile.get("name", ""),
    "Entry Type": "OPENING BALANCE",
    "Product Name": "-",
    "Billed Qty": "-",
    "FOC Qty": "-",
    "Rate (Rs.)": "-",
    "Debit (+Sale)": op_dues,
    "Credit (-Paid/Ret)": 0.0,
    "Running Balance": op_dues,
    "Payment Mode": "-",
    "MR / Staff": "-",
    "Remarks / Notes": "Initial ledger balance from directory"
})

# 2. Sales Invoices
if not cli_sales.empty:
    c_dt   = find_col(cli_sales, ["Date (A.D.)", "Date", "date"])
    c_bs   = find_col(cli_sales, ["Nepali Miti", "BS Date", "bs_date", "Miti"])
    c_inv  = find_col(cli_sales, ["Invoice Number", "Invoice No", "Invoice No.", "invoice", "Invoice"])
    c_prod = find_col(cli_sales, ["Product Name", "product_name", "Product"])
    c_qty  = find_col(cli_sales, ["Qty", "qty", "Quantity"])
    c_foc  = find_col(cli_sales, ["FOC", "foc_qty", "FOC Qty", "Free"])
    c_rt   = find_col(cli_sales, ["Rate", "Rate (Rs.)", "rate"])
    c_tot  = find_col(cli_sales, ["Total Sale", "Total Sale (Rs.)", "total_sale", "Total"])
    c_cash = find_col(cli_sales, ["Cash Collected", "Cash Recd", "Cash Recd (Rs.)", "cash_collected", "Cash"])
    c_mr   = find_col(cli_sales, ["Staff Name", "staff_name", "MR Name", "Executive", "Staff"])

    # Aggregate invoice delivery cash cleanly per invoice
    invoice_cash_map = {}
    if c_inv and c_cash:
        for _, r in cli_sales.iterrows():
            inv = str(r.get(c_inv, "INV")).strip()
            invoice_cash_map[inv] = invoice_cash_map.get(inv, 0.0) + clean_num(r.get(c_cash, 0))

    credited_invoices = set()

    for _, r in cli_sales.iterrows():
        b_val  = clean_num(r.get(c_tot, 0))
        p_name = str(r.get(c_prod, "Pharmaceutical Item")).strip()
        q_val  = clean_num(r.get(c_qty, 0))
        f_val  = clean_num(r.get(c_foc, 0)) if c_foc else 0.0
        rt_val = clean_num(r.get(c_rt, 0))
        inv_no = str(r.get(c_inv, "INV")).strip() if c_inv else "INV"
        tx_dt  = str(r.get(c_dt, "-")).strip() if c_dt else "-"
        tx_bs  = str(r.get(c_bs, "-")).strip() if c_bs else "-"
        staff  = str(r.get(c_mr, "-")).strip() if c_mr and pd.notna(r.get(c_mr)) else "-"

        statement_rows.append({
            "Date (AD)": tx_dt,
            "Miti (BS)": tx_bs,
            "Ref / Invoice #": inv_no,
            "Client Code": client_profile.get("code", "PAR-000"),
            "Client Name": client_profile.get("name", ""),
            "Entry Type": "PURCHASE / SALE",
            "Product Name": p_name,
            "Billed Qty": f"{q_val:g}",
            "FOC Qty": f"{f_val:g}" if f_val > 0 else "-",
            "Rate (Rs.)": f"{rt_val:,.2f}",
            "Debit (+Sale)": b_val,
            "Credit (-Paid/Ret)": 0.0,
            "Running Balance": 0.0,
            "Payment Mode": "Invoice Bill",
            "MR / Staff": staff,
            "Remarks / Notes": f"Billed purchase on delivery"
        })

        # Insert single delivery cash credit entry per invoice
        if inv_no in invoice_cash_map and inv_no not in credited_invoices:
            c_val = invoice_cash_map[inv_no]
            if c_val > 0:
                statement_rows.append({
                    "Date (AD)": tx_dt,
                    "Miti (BS)": tx_bs,
                    "Ref / Invoice #": f"{inv_no}-CASH",
                    "Client Code": client_profile.get("code", "PAR-000"),
                    "Client Name": client_profile.get("name", ""),
                    "Entry Type": "DELIVERY CASH",
                    "Product Name": "-",
                    "Billed Qty": "-",
                    "FOC Qty": "-",
                    "Rate (Rs.)": "-",
                    "Debit (+Sale)": 0.0,
                    "Credit (-Paid/Ret)": c_val,
                    "Running Balance": 0.0,
                    "Payment Mode": "Cash (COD)",
                    "MR / Staff": staff,
                    "Remarks / Notes": f"Direct cash received against #{inv_no}"
                })
            credited_invoices.add(inv_no)

# 3. Dues Collections / Receipts
if not cli_col.empty:
    c_dt  = find_col(cli_col, ["Date (A.D.)", "Date", "date"])
    c_bs  = find_col(cli_col, ["Nepali Miti", "BS Date", "bs_date", "Miti"])
    c_rec = find_col(cli_col, ["Receipt / Ref No.", "Receipt No", "receipt_no", "Receipt"])
    c_amt = find_col(cli_col, ["Amount Collected", "Amount Collected (Rs.)", "amount", "Amount"])
    c_mod = find_col(cli_col, ["Payment Instrument", "Payment Mode", "mode", "Instrument"])
    c_rem = find_col(cli_col, ["Transaction Note", "Remarks / Ref", "remarks", "Remarks"])
    c_mr  = find_col(cli_col, ["Staff Name", "staff_name", "MR Name", "Staff"])

    for _, r in cli_col.iterrows():
        amt = clean_num(r.get(c_amt, 0))
        if amt > 0:
            rec_no = str(r.get(c_rec, "REC")).strip() if c_rec else "REC"
            tx_dt  = str(r.get(c_dt, "-")).strip() if c_dt else "-"
            tx_bs  = str(r.get(c_bs, "-")).strip() if c_bs else "-"
            mode   = str(r.get(c_mod, "Cash")).strip() if c_mod else "Cash"
            note   = str(r.get(c_rem, "Dues Clearance")).strip() if c_rem else "Dues Clearance"
            staff  = str(r.get(c_mr, "-")).strip() if c_mr and pd.notna(r.get(c_mr)) else "-"

            statement_rows.append({
                "Date (AD)": tx_dt,
                "Miti (BS)": tx_bs,
                "Ref / Invoice #": rec_no,
                "Client Code": client_profile.get("code", "PAR-000"),
                "Client Name": client_profile.get("name", ""),
                "Entry Type": "DUES PAYMENT",
                "Product Name": "-",
                "Billed Qty": "-",
                "FOC Qty": "-",
                "Rate (Rs.)": "-",
                "Debit (+Sale)": 0.0,
                "Credit (-Paid/Ret)": amt,
                "Running Balance": 0.0,
                "Payment Mode": mode,
                "MR / Staff": staff,
                "Remarks / Notes": note
            })

# 4. Product Returns
if not cli_ret.empty:
    c_dt  = find_col(cli_ret, ["Date (A.D.)", "Date", "date"])
    c_bs  = find_col(cli_ret, ["Nepali Miti", "BS Date", "bs_date", "Miti"])
    c_prd = find_col(cli_ret, ["Returned Item Name", "Product Name", "product_name"])
    c_qty = find_col(cli_ret, ["Units Returned", "Return Qty", "qty"])
    c_rt  = find_col(cli_ret, ["Credit Rate (Rs.)", "Rate", "rate"])
    c_tot = find_col(cli_ret, ["Total Return", "Total Return (Rs.)", "total", "Amount"])
    c_rsn = find_col(cli_ret, ["Reason", "reason"])
    c_mr  = find_col(cli_ret, ["Staff Name", "staff_name", "MR Name", "Staff"])

    for _, r in cli_ret.iterrows():
        ret_val = clean_num(r.get(c_tot, 0))
        if ret_val > 0:
            tx_dt = str(r.get(c_dt, "-")).strip() if c_dt else "-"
            tx_bs = str(r.get(c_bs, "-")).strip() if c_bs else "-"
            item  = str(r.get(c_prd, "Stock Item")).strip() if c_prd else "Stock Item"
            qty   = clean_num(r.get(c_qty, 0)) if c_qty else 0
            rate  = clean_num(r.get(c_rt, 0)) if c_rt else 0
            rsn   = str(r.get(c_rsn, "Damage / Expiry")).strip() if c_rsn else ""
            staff = str(r.get(c_mr, "-")).strip() if c_mr and pd.notna(r.get(c_mr)) else "-"

            statement_rows.append({
                "Date (AD)": tx_dt,
                "Miti (BS)": tx_bs,
                "Ref / Invoice #": "CREDIT-NOTE",
                "Client Code": client_profile.get("code", "PAR-000"),
                "Client Name": client_profile.get("name", ""),
                "Entry Type": "GOODS RETURN",
                "Product Name": item,
                "Billed Qty": f"{qty:g}",
                "FOC Qty": "-",
                "Rate (Rs.)": f"{rate:,.2f}" if rate > 0 else "-",
                "Debit (+Sale)": 0.0,
                "Credit (-Paid/Ret)": ret_val,
                "Running Balance": 0.0,
                "Payment Mode": "Credit Adjustment",
                "MR / Staff": staff,
                "Remarks / Notes": rsn
            })

# Calculate Running Balance
running_bal = op_dues
for i in range(1, len(statement_rows)):
    row = statement_rows[i]
    running_bal = running_bal + row["Debit (+Sale)"] - row["Credit (-Paid/Ret)"]
    row["Running Balance"] = running_bal

raw_stmt_df = pd.DataFrame(statement_rows)

# Formatted DataFrame for Presentation
disp_stmt = raw_stmt_df.copy()
disp_stmt["Debit (+Sale)"] = disp_stmt["Debit (+Sale)"].apply(lambda v: f"Rs. {v:,.2f}" if v > 0 else "-")
disp_stmt["Credit (-Paid/Ret)"] = disp_stmt["Credit (-Paid/Ret)"].apply(lambda v: f"Rs. {v:,.2f}" if v > 0 else "-")
disp_stmt["Running Balance"] = disp_stmt["Running Balance"].apply(lambda v: f"Rs. {v:,.2f}")

# --- DRILLDOWN TABS ---
t1, t2, t3, t4, t5 = st.tabs([
    f"📜 Full Ledger Statement ({len(raw_stmt_df)})",
    f"🛒 Invoiced Purchases ({len(cli_sales)})",
    f"💵 Payment Receipts ({len(cli_col)})",
    f"🔄 Stock Returns ({len(cli_ret)})",
    "🏢 Central Master Feeds"
])

# TAB 1: FULL DETAILED STATEMENT
with t1:
    st.markdown(f"##### 📜 Official Account Statement & Audit Trail — {client_profile.get('name')}")
    st.caption("Complete breakdown showing date, miti, product details, billed/FOC quantities, rates, debits, credits, and live running balance.")

    # Statement Summary Card
    st.markdown(f"""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; padding:12px 18px; margin-bottom:14px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:10px; font-size:0.86rem;">
        <div><b>Client:</b> {client_profile.get('name')} [{client_profile.get('code')}]</div>
        <div><b>Opening Dues:</b> Rs. {op_dues:,.2f}</div>
        <div><b>Total Billed:</b> Rs. {tot_cli_billed:,.2f}</div>
        <div><b>Total Paid:</b> Rs. {total_cash_paid:,.2f}</div>
        <div><b>Returns:</b> Rs. {tot_cli_returns:,.2f}</div>
        <div style="color:{'#DC2626' if current_outstanding > 0 else '#164E33'}; font-weight:700;"><b>Closing Balance:</b> Rs. {current_outstanding:,.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(disp_stmt, use_container_width=True, hide_index=True)

    col_d1, col_d2 = st.columns([2, 5])
    with col_d1:
        csv_buf = io.BytesIO()
        raw_stmt_df.to_csv(csv_buf, index=False)
        st.download_button(
            label=f"📥 Download Full Statement (CSV)",
            data=csv_buf.getvalue(),
            file_name=f"Statement_{client_profile.get('code','PAR')}_{client_profile.get('name','Client').replace(' ', '_')}.csv",
            mime="text/csv",
            use_container_width=True
        )

# TAB 2: INVOICED PURCHASES
with t2:
    st.markdown(f"##### 🛒 Invoiced Product Purchases — {client_profile.get('name')}")
    if not cli_sales.empty:
        st.dataframe(cli_sales, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No purchase invoices recorded for this client yet.")

# TAB 3: COLLECTIONS
with t3:
    st.markdown(f"##### 💵 Dues Collected & Payment Receipts — {client_profile.get('name')}")
    if not cli_col.empty:
        st.dataframe(cli_col, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No payment receipts recorded for this client yet.")

# TAB 4: RETURNS
with t4:
    st.markdown(f"##### 🔄 Returned Products & Breakages — {client_profile.get('name')}")
    if not cli_ret.empty:
        st.dataframe(cli_ret, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No product returns recorded for this client.")

# TAB 5: ALL FEEDS & SYSTEM SETUP
with t5:
    st.markdown("##### 🏢 Company-Wide Live Operations Master Feeds")
    sub_tab1, sub_tab2, sub_tab3, sub_tab4, sub_tab5 = st.tabs([
        f"All Sales ({len(sales_df)})",
        f"All Collections ({len(col_df)})",
        f"All Returns ({len(ret_df)})",
        f"All Expenses ({len(exp_df)})",
        f"All Advances ({len(adv_df)})"
    ])
    with sub_tab1: st.dataframe(sales_df, use_container_width=True, hide_index=True)
    with sub_tab2: st.dataframe(col_df, use_container_width=True, hide_index=True)
    with sub_tab3: st.dataframe(ret_df, use_container_width=True, hide_index=True)
    with sub_tab4: st.dataframe(exp_df, use_container_width=True, hide_index=True)
    with sub_tab5: st.dataframe(adv_df, use_container_width=True, hide_index=True)
