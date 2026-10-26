import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

st.set_page_config(
    page_title="Alpine Herbs — Party Ledger Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Alpine Herbs Pvt. Ltd. — Client Ledger Dashboard")
st.caption("Repository B: Live Party Outstanding & Recovery Tracking System")

# Google Sheet CSV Export Link (Real-Time Sync)
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

@st.cache_data(ttl=5)
def load_data():
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

    # Sidebar Filters (Collapsible via sidebar arrow)
    with st.sidebar:
        st.header("🔍 Filters & Controls")
        
        categories = df["Category / Status"].dropna().unique().tolist() if "Category / Status" in df.columns else []
        category_filter = st.multiselect("Category / Status", options=categories, default=categories)
        
        districts = df["District / Area"].dropna().unique().tolist() if "District / Area" in df.columns else []
        district_filter = st.multiselect("District / Area", options=districts, default=districts)

    if categories or districts:
        filtered_df = df[
            df["Category / Status"].isin(category_filter) & 
            df["District / Area"].isin(district_filter)
        ]
    else:
        filtered_df = df

    # Client Code Selector in Sidebar
    client_codes = sorted(filtered_df["Client Code"].dropna().astype(str).unique().tolist()) if "Client Code" in filtered_df.columns else []
    client_list = ["ALL CLIENTS"] + client_codes
    selected_client = st.sidebar.selectbox("Select Client Code / Party", options=client_list)

    if selected_client != "ALL CLIENTS":
        display_df = filtered_df[filtered_df["Client Code"].astype(str) == selected_client]
    else:
        display_df = filtered_df

    # Summary Metrics Row
    total_outstanding = display_df["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in display_df.columns else 0.0
    total_parties = len(display_df)
    
    bad_debt_mask = display_df["Category / Status"] == "Bad Debt / Recovery" if "Category / Status" in display_df.columns else False
    bad_debt_total = display_df[bad_debt_mask]["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in display_df.columns else 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Parties Filtered", f"{total_parties}")
    col2.metric("Total Outstanding Cash", f"NRs {total_outstanding:,.2f}")
    col3.metric("Bad Debt / Recovery Amount", f"NRs {bad_debt_total:,.2f}")

    st.markdown("---")

    # Display Full Table
    cols_to_show = ["Date", "Client Code", "District / Area", "Category / Status", "Party Name", "Address", "Mobile No.", "Outstanding Cash (NRs)", "Notes / Status"]
    avail_cols = [c for c in cols_to_show if c in display_df.columns]

    st.dataframe(display_df[avail_cols], use_container_width=True, hide_index=True)

    # PDF Generation Function using Temp File
    def generate_pdf(dataframe, client_title):
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Alpine Herbs Pvt. Ltd. - Client Ledger Report", ln=True, align="C")
        
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 6, f"Selection: {client_title}", ln=True, align="C")
        pdf.ln(5)

        # Table Header
        pdf.set_font("Helvetica", "B", 9)
        headers = ["Date", "Code", "District", "Category", "Party Name", "Address", "Mobile", "Outstanding (NRs)"]
        col_widths = [22, 20, 22, 35, 45, 35, 25, 35]
        
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, h, border=1, align="C")
        pdf.ln()

        # Table Rows
        pdf.set_font("Helvetica", "", 8)
        for _, row in dataframe.iterrows():
            pdf.cell(col_widths[0], 6, str(row.get("Date", "")), border=1)
            pdf.cell(col_widths[1], 6, str(row.get("Client Code", "")), border=1, align="C")
            pdf.cell(col_widths[2], 6, str(row.get("District / Area", "")), border=1)
            pdf.cell(col_widths[3], 6, str(row.get("Category / Status", ""))[:20], border=1)
            pdf.cell(col_widths[4], 6, str(row.get("Party Name", ""))[:25], border=1)
            pdf.cell(col_widths[5], 6, str(row.get("Address", ""))[:20], border=1)
            pdf.cell(col_widths[6], 6, str(row.get("Mobile No.", "")), border=1, align="C")
            
            amt = row.get("Outstanding Cash (NRs)", 0.0)
            pdf.cell(col_widths[7], 6, f"{amt:,.2f}", border=1, align="R")
            pdf.ln()

        # Total Row
        pdf.set_font("Helvetica", "B", 9)
        total_sum = dataframe["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in dataframe.columns else 0.0
        pdf.cell(sum(col_widths[:7]), 8, "Total Outstanding:", border=1, align="R")
        pdf.cell(col_widths[7], 8, f"{total_sum:,.2f}", border=1, align="R")
        
        # Save to temp file and read bytes
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp_name = tmp.name
        
        pdf.output(tmp_name)
        
        with open(tmp_name, "rb") as f:
            pdf_bytes = f.read()
            
        os.unlink(tmp_name)
        return pdf_bytes

    # PDF Download Button
    if not display_df.empty:
        pdf_bytes = generate_pdf(display_df, selected_client)
        st.download_button(
            label="📄 Download Ledger as PDF",
            data=pdf_bytes,
            file_name=f"alpine_herbs_ledger_{selected_client}.pdf",
            mime="application/pdf"
        )
        
