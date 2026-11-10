import streamlit as st
import pandas as pd
import math
import io

# --- PAGE SETUP ---
st.set_page_config(
    page_title="ALPINE HERBS | Client 360° Master Dashboard",
    page_icon="🌿",
    layout="wide"
)

# SPREADSHEET ID
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

# --- BRANDING & STYLING ---
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
.client-hero {
    background: #F4FAF6;
    border: 1px solid #B0D4BE;
    border-left: 5px solid #164E33;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 1.2rem;
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

# --- MASTER CLIENT LEDGER (SYNTAX-SAFE CSV TEXT BLOCK) ---
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

# Parse safely into records with zero brace-matching errors
MASTER_CLIENTS = pd.read_csv(io.StringIO(CLIENTS_DATA.strip()), dtype=str).fillna("").to_dict("records")
for c in MASTER_CLIENTS:
    try:
        c["dues"] = float(c["dues"]) if c["dues"] != "" else 0.0
    except:
        c["dues"] = 0.0

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
    cols_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        if cand.strip().lower() in cols_map:
            return cols_map[cand.strip().lower()]
    return None

# --- RESILIENT DATA LOADER ---
def fetch_sheet_tab(tab_name_candidates):
    for tab in tab_name_candidates:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab.replace(' ', '%20')}"
        try:
            df = pd.read_csv(url, dtype=str)
            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
                valid_cols = [c for c in df.columns if not (c.startswith("Unnamed:") and df[c].isna().all())]
                df = df[valid_cols]
                df = df.dropna(how="all", axis=0)
                df = df[~df.apply(lambda r: r.astype(str).str.strip().eq("").all() or r.astype(str).str.strip().eq("nan").all(), axis=1)]
                if not df.empty:
                    return df
        except Exception:
            continue
    return pd.DataFrame()

@st.cache_data(ttl=10)
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

# Header Banner
st.markdown("""
<div class="main-header">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="margin:0; font-weight:800; font-size:1.55rem; color:#FFFFFF;">🌿 ALPINE HERBS PVT. LTD.</h2>
            <div style="font-size:0.86rem; color:#D3E6DA; margin-top:2px;">
                CENTRAL OPERATIONS & CLIENT 360° AUDIT DASHBOARD (REPOSITORY B) &nbsp;|&nbsp; BIRGUNJ, NEPAL
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Build Comprehensive Client Pool (Master Directory + Any New Parties from Sales)
known_names = set(c["name"].lower() for c in MASTER_CLIENTS)
combined_clients = MASTER_CLIENTS.copy()

if not sales_df.empty:
    c_sname = find_col(sales_df, ["Client Name", "client_name", "Party Name"])
    c_scode = find_col(sales_df, ["Client Code", "client_code", "Code"])
    c_sarea = find_col(sales_df, ["Address", "Area", "Town"])
    if c_sname:
        for _, r in sales_df.iterrows():
            nm = str(r.get(c_sname, "")).strip()
            if nm and nm.lower() not in known_names and nm.lower() != "walk-in party":
                known_names.add(nm.lower())
                combined_clients.append({
                    "name": nm,
                    "code": str(r.get(c_scode, "NEW-000")).strip() if c_scode else "NEW-000",
                    "area": str(r.get(c_sarea, "Birgunj")).strip() if c_sarea else "Birgunj",
                    "district": "Parsa",
                    "phone": "",
                    "dues": 0.0
                })

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚙️ Live Controls")
    if st.button("⚡ Force Live Refresh", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### 👤 Select Client / Chemist")
    
    # Area Filter for Client Search
    area_options = ["All Areas"] + sorted(list(set(c["area"] for c in combined_clients if c.get("area"))))
    filter_area = st.selectbox("Filter Clients by Route / Area", area_options)

    if filter_area != "All Areas":
        filtered_client_pool = [c for c in combined_clients if c["area"].lower() == filter_area.lower()]
    else:
        filtered_client_pool = combined_clients

    client_display_list = [f"{c['name']}  [{c['code']}] — 📍 {c['area']}" for c in sorted(filtered_client_pool, key=lambda x: x["name"].lower())]
    selected_client_str = st.selectbox("Choose Client to View Statement", client_display_list)

# Resolve Selected Client Info
selected_client_name = selected_client_str.split("  [")[0].strip()
client_profile = next((c for c in combined_clients if c["name"].lower() == selected_client_name.lower()), {
    "name": selected_client_name, "code": "N/A", "area": "N/A", "district": "N/A", "phone": "N/A", "dues": 0.0
})

# --- CLIENT SPECIFIC DATA EXTRACTION ---
c_client_in_sales = find_col(sales_df, ["Client Name", "client_name", "Party Name"])
if c_client_in_sales and not sales_df.empty:
    cli_sales = sales_df[sales_df[c_client_in_sales].astype(str).str.strip().str.lower() == selected_client_name.lower()].copy()
else:
    cli_sales = pd.DataFrame()

c_client_in_col = find_col(col_df, ["Client Name", "client_name", "Party Name"])
if c_client_in_col and not col_df.empty:
    cli_col = col_df[col_df[c_client_in_col].astype(str).str.strip().str.lower() == selected_client_name.lower()].copy()
else:
    cli_col = pd.DataFrame()

c_client_in_ret = find_col(ret_df, ["Client Name", "client_name", "Party Name"])
if c_client_in_ret and not ret_df.empty:
    cli_ret = ret_df[ret_df[c_client_in_ret].astype(str).str.strip().str.lower() == selected_client_name.lower()].copy()
else:
    cli_ret = pd.DataFrame()

# Calculations for Selected Client
op_dues = float(client_profile.get("dues", 0.0))

col_stot  = find_col(cli_sales, ["Total Sale", "Total Sale (Rs.)", "Total Billed", "Total"])
col_scash = find_col(cli_sales, ["Cash Recd", "Cash Recd (Rs.)", "Cash Collected", "Cash"])

tot_cli_billed = cli_sales[col_stot].apply(clean_num).sum() if col_stot and not cli_sales.empty else 0.0
tot_cli_direct_cash = cli_sales[col_scash].apply(clean_num).sum() if col_scash and not cli_sales.empty else 0.0

col_camt = find_col(cli_col, ["Amount Collected", "Amount Collected (Rs.)", "Amount"])
tot_cli_dues_paid = cli_col[col_camt].apply(clean_num).sum() if col_camt and not cli_col.empty else 0.0

col_rtot = find_col(cli_ret, ["Total Return", "Total Return (Rs.)", "Total Value", "Total", "Amount"])
tot_cli_returns = cli_ret[col_rtot].apply(clean_num).sum() if col_rtot and not cli_ret.empty else 0.0

total_cash_paid = tot_cli_direct_cash + tot_cli_dues_paid
current_outstanding = op_dues + tot_cli_billed - total_cash_paid - tot_cli_returns

# --- CLIENT BANNER & FINANCIAL SUMMARY ---
phone_info = f" | 📞 **Phone:** {client_profile['phone']}" if client_profile.get('phone') else ""
st.markdown(f"""
<div class="client-hero">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <span style="background:#164E33; color:white; padding:3px 8px; border-radius:4px; font-weight:700; font-size:0.8rem;">
                {client_profile.get('code', 'PAR-000')}
            </span>
            <span style="font-size:1.4rem; font-weight:800; color:#0D2818; margin-left:8px;">
                {client_profile['name']}
            </span>
            <div style="font-size:0.88rem; color:#2D5A40; margin-top:4px;">
                📍 <b>Territory:</b> {client_profile.get('area', 'Birgunj')} ({client_profile.get('district', 'Parsa')}) {phone_info}
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI Cards
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">📜 Opening Dues</div>
        <div class="kpi-value">{money(op_dues)}</div>
        <div class="kpi-sub">Initial Ledger Balance</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="kpi-card">
        <div class="kpi-title">🛒 New Billed Sales</div>
        <div class="kpi-value">{money(tot_cli_billed)}</div>
        <div class="kpi-sub">Invoiced Products Total</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#2D7D52;">
        <div class="kpi-title">💵 Total Cash Paid</div>
        <div class="kpi-value" style="color:#164E33;">{money(total_cash_paid)}</div>
        <div class="kpi-sub">Sales: {money(tot_cli_direct_cash)} | Dues: {money(tot_cli_dues_paid)}</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="kpi-card" style="border-top-color:#6B46C1;">
        <div class="kpi-title">🔄 Goods Returned</div>
        <div class="kpi-value" style="color:#6B46C1;">{money(tot_cli_returns)}</div>
        <div class="kpi-sub">Damage / Expiry Value</div>
    </div>""", unsafe_allow_html=True)
with c5:
    due_color = "#900C3F" if current_outstanding > 0 else "#0D2818"
    st.markdown(f"""<div class="kpi-card" style="border-top-color:{due_color}; background:#F4FAF6;">
        <div class="kpi-title">💰 Current Net Balance</div>
        <div class="kpi-value" style="color:{due_color};">{money(current_outstanding)}</div>
        <div class="kpi-sub">Total Payable Today</div>
    </div>""", unsafe_allow_html=True)

st.write("")

# --- BUILD CHRONOLOGICAL STATEMENT ---
statement_rows = []

statement_rows.append({
    "Date": "Opening", "Time": "-", "Ref #": "INIT-DUES",
    "Type": "OPENING BALANCE", "Particulars": "Previous Ledger Outstanding Balance",
    "Debit (+Sale)": op_dues, "Credit (-Paid/Ret)": 0.0, "Balance": op_dues
})

if not cli_sales.empty:
    c_dt   = find_col(cli_sales, ["Date (A.D.)", "Date", "date"])
    c_tm   = find_col(cli_sales, ["Time", "time"])
    c_inv  = find_col(cli_sales, ["Invoice No", "Invoice No.", "invoice"])
    c_prod = find_col(cli_sales, ["Product Name", "product_name", "Product"])
    c_qty  = find_col(cli_sales, ["Qty", "qty"])
    c_rt   = find_col(cli_sales, ["Rate", "Rate (Rs.)", "rate"])
    c_tot  = find_col(cli_sales, ["Total Sale", "Total Sale (Rs.)", "total_sale"])
    c_cash = find_col(cli_sales, ["Cash Recd", "Cash Recd (Rs.)", "cash_collected"])

    for _, r in cli_sales.iterrows():
        b_val = clean_num(r.get(c_tot, 0))
        c_val = clean_num(r.get(c_cash, 0))
        p_name = str(r.get(c_prod, "Stock Item"))
        q_val  = clean_num(r.get(c_qty, 0))
        rt_val = clean_num(r.get(c_rt, 0))

        statement_rows.append({
            "Date": str(r.get(c_dt, "-")), "Time": str(r.get(c_tm, "-")),
            "Ref #": str(r.get(c_inv, "INV")), "Type": "PURCHASE / SALE",
            "Particulars": f"{p_name} (Qty: {q_val:g}, Rate: Rs. {rt_val:,.2f})",
            "Debit (+Sale)": b_val, "Credit (-Paid/Ret)": 0.0, "Balance": 0.0
        })

        if c_val > 0:
            statement_rows.append({
                "Date": str(r.get(c_dt, "-")), "Time": str(r.get(c_tm, "-")),
                "Ref #": str(r.get(c_inv, "INV")) + "-CASH", "Type": "DELIVERY CASH",
                "Particulars": f"Direct Cash Received against {r.get(c_inv, 'Invoice')}",
                "Debit (+Sale)": 0.0, "Credit (-Paid/Ret)": c_val, "Balance": 0.0
            })

if not cli_col.empty:
    c_dt  = find_col(cli_col, ["Date (A.D.)", "Date", "date"])
    c_tm  = find_col(cli_col, ["Time", "time"])
    c_rec = find_col(cli_col, ["Receipt No", "receipt_no", "Receipt"])
    c_amt = find_col(cli_col, ["Amount Collected", "Amount Collected (Rs.)", "amount"])
    c_mod = find_col(cli_col, ["Payment Mode", "mode"])
    c_rem = find_col(cli_col, ["Remarks / Ref", "remarks", "Remarks"])

    for _, r in cli_col.iterrows():
        amt = clean_num(r.get(c_amt, 0))
        if amt > 0:
            statement_rows.append({
                "Date": str(r.get(c_dt, "-")), "Time": str(r.get(c_tm, "-")),
                "Ref #": str(r.get(c_rec, "REC")), "Type": "PAYMENT RECEIPT",
                "Particulars": f"Dues Recovery ({r.get(c_mod, 'Cash')}) - {r.get(c_rem, 'Old Dues')}",
                "Debit (+Sale)": 0.0, "Credit (-Paid/Ret)": amt, "Balance": 0.0
            })

if not cli_ret.empty:
    c_dt  = find_col(cli_ret, ["Date (A.D.)", "Date", "date"])
    c_tm  = find_col(cli_ret, ["Time", "time"])
    c_prd = find_col(cli_ret, ["Product Name", "product_name"])
    c_qty = find_col(cli_ret, ["Return Qty", "qty"])
    c_tot = find_col(cli_ret, ["Total Return", "Total Return (Rs.)", "total"])
    c_rsn = find_col(cli_ret, ["Reason", "reason"])

    for _, r in cli_ret.iterrows():
        ret_val = clean_num(r.get(c_tot, 0))
        if ret_val > 0:
            statement_rows.append({
                "Date": str(r.get(c_dt, "-")), "Time": str(r.get(c_tm, "-")),
                "Ref #": "RETURN", "Type": "STOCK RETURN",
                "Particulars": f"Credit: {r.get(c_prd, 'Item')} (Qty: {clean_num(r.get(c_qty, 0)):g}) - {r.get(c_rsn, '')}",
                "Debit (+Sale)": 0.0, "Credit (-Paid/Ret)": ret_val, "Balance": 0.0
            })

running_bal = op_dues
for i in range(1, len(statement_rows)):
    row = statement_rows[i]
    running_bal = running_bal + row["Debit (+Sale)"] - row["Credit (-Paid/Ret)"]
    row["Balance"] = running_bal

stmt_df = pd.DataFrame(statement_rows)

disp_stmt = stmt_df.copy()
disp_stmt["Debit (+Sale)"] = disp_stmt["Debit (+Sale)"].apply(lambda v: f"Rs. {v:,.2f}" if v > 0 else "-")
disp_stmt["Credit (-Paid/Ret)"] = disp_stmt["Credit (-Paid/Ret)"].apply(lambda v: f"Rs. {v:,.2f}" if v > 0 else "-")
disp_stmt["Balance"] = disp_stmt["Balance"].apply(lambda v: f"Rs. {v:,.2f}")

# --- DRILLDOWN TABS ---
t1, t2, t3, t4, t5 = st.tabs([
    f"📜 Full Ledger Statement ({len(stmt_df)})",
    f"🛒 Invoiced Purchases ({len(cli_sales)})",
    f"💵 Payment Receipts ({len(cli_col)})",
    f"🔄 Stock Returns ({len(cli_ret)})",
    "🏢 All Master Feeds"
])

with t1:
    st.markdown(f"##### 📜 Official Account Statement — {client_profile['name']}")
    st.dataframe(disp_stmt, use_container_width=True, hide_index=True)
    
    csv_buf = io.BytesIO()
    stmt_df.to_csv(csv_buf, index=False)
    st.download_button(
        label=f"📥 Download Official Statement for {client_profile['name']} (CSV)",
        data=csv_buf.getvalue(),
        file_name=f"Statement_{client_profile.get('code','PAR')}_{client_profile['name'].replace(' ', '_')}.csv",
        mime="text/csv"
    )

with t2:
    st.markdown(f"##### 🛒 Invoiced Product Purchases — {client_profile['name']}")
    if not cli_sales.empty:
        st.dataframe(cli_sales, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No new purchase invoices recorded for this client yet.")

with t3:
    st.markdown(f"##### 💵 Dues Collected & Payment Receipts — {client_profile['name']}")
    if not cli_col.empty:
        st.dataframe(cli_col, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No payment receipts recorded for this client yet.")

with t4:
    st.markdown(f"##### 🔄 Returned Products & Breakages — {client_profile['name']}")
    if not cli_ret.empty:
        st.dataframe(cli_ret, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ No product returns recorded for this client.")

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
