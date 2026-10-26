import streamlit as st
import pandas as pd
from fpdf import FPDF
import tempfile
import os

st.set_page_config(
    page_title="Alpine Herbs — Master Operations Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Alpine Herbs Pvt. Ltd. — Operations & Financial Dashboard")
st.caption("Repository B: Live Party Ledger, Expenses, Staff Advances & Product Sales Intelligence")

# Google Sheet CSV Export Link (Real-Time Sync)
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Swift refresh cache (1-second TTL for real-time updates)
@st.cache_data(ttl=1)
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
    # Sidebar Navigation & View Switcher
    with st.sidebar:
        st.header("📌 Navigation")
        app_view = st.radio(
            "Select Dashboard Segment",
            options=[
                "📊 Party Ledger & Passbooks", 
                "📦 Product Sales & Best Sellers", 
                "💸 Operating Expenses", 
                "💼 Staff Advances"
            ]
        )

        if st.button("⚡ Force Swift Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("---")

    # =========================================================
    # SEGMENT 1: PARTY LEDGER & BANK-GRADE CLIENT PASSBOOKS
    # =========================================================
    if app_view == "📊 Party Ledger & Passbooks":
        st.subheader("📋 Client Outstanding Ledger & Individual Passbook Statements")

        if "Outstanding Cash (NRs)" in df.columns:
            df["Outstanding Cash (NRs)"] = pd.to_numeric(df["Outstanding Cash (NRs)"], errors="coerce").fillna(0.0)

        with st.sidebar:
            with st.expander("🔍 Ledger Filters", expanded=True):
                categories = df["Category / Status"].dropna().unique().tolist() if "Category / Status" in df.columns else []
                category_filter = st.multiselect("Category / Status", options=categories, default=categories)
                
                districts = df["District / Area"].dropna().unique().tolist() if "District / Area" in df.columns else []
                district_filter = st.multiselect("District / Area", options=districts, default=districts)

        if 'category_filter' in locals() and categories:
            filtered_df = df[
                df["Category / Status"].isin(category_filter) & 
                df["District / Area"].isin(district_filter)
            ]
        else:
            filtered_df = df

        client_codes = sorted(filtered_df["Client Code"].dropna().astype(str).unique().tolist()) if "Client Code" in filtered_df.columns else []
        client_list = ["ALL CLIENTS"] + client_codes
        selected_client = st.sidebar.selectbox("Select Client Code / Party", options=client_list)

        if selected_client != "ALL CLIENTS":
            display_df = filtered_df[filtered_df["Client Code"].astype(str) == selected_client]
        else:
            display_df = filtered_df

        total_outstanding = display_df["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in display_df.columns else 0.0
        total_parties = len(display_df)
        
        bad_debt_mask = display_df["Category / Status"] == "Bad Debt / Recovery" if "Category / Status" in display_df.columns else False
        bad_debt_total = display_df[bad_debt_mask]["Outstanding Cash (NRs)"].sum() if "Outstanding Cash (NRs)" in display_df.columns else 0.0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Parties Filtered", f"{total_parties}")
        col2.metric("Total Outstanding Cash", f"NRs {total_outstanding:,.2f}")
        col3.metric("Bad Debt / Recovery Amount", f"NRs {bad_debt_total:,.2f}")

        st.markdown("---")

        if selected_client != "ALL CLIENTS" and not display_df.empty:
            party_name = display_df.iloc[0].get("Party Name", selected_client)
            party_district = display_df.iloc[0].get("District / Area", "—")
            party_address = display_df.iloc[0].get("Address", "—")
            party_mobile = display_df.iloc[0].get("Mobile No.", "—")

            st.markdown(f"### 🏦 Official Passbook Statement: {party_name} (`{selected_client}`)")
            st.info(f"📍 **District:** {party_district} &nbsp;|&nbsp; 🏠 **Address:** {party_address} &nbsp;|&nbsp; 📱 **Mobile:** {party_mobile}")

            if "Date" in display_df.columns:
                statement_df = display_df.sort_values(by="Date", ascending=True).reset_index(drop=True)
            else:
                statement_df = display_df.reset_index(drop=True)

            passbook_view = pd.DataFrame()
            passbook_view["Date (A.D.)"] = statement_df.get("Date", "")
            passbook_view["Invoice / Ref"] = statement_df.get("Invoice No.", "—")
            passbook_view["Particulars / Products"] = statement_df.get("Goods / Product Name", "General Purchase")
            passbook_view["Qty"] = statement_df.get("Qty", 0.0)
            passbook_view["Billed Purchase (Rs.)"] = statement_df.get("Total Sale (Rs.)", statement_df.get("Outstanding Cash (NRs)", 0.0))
            passbook_view["Payment Received (Rs.)"] = statement_df.get("Cash Collected (Rs.)", 0.0)
            passbook_view["Running Balance (Rs.)"] = statement_df.get("Outstanding Cash (NRs)", 0.0)

            st.dataframe(passbook_view, use_container_width=True, hide_index=True)

            def generate_passbook_pdf(p_df, code, name, dist, addr, mob):
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 15)
                pdf.cell(0, 10, "ALPINE HERBS PVT. LTD.", ln=True, align="C")
                pdf.set_font("Helvetica", "I", 9)
                pdf.cell(0, 5, "Birgunj, Nepal | Official Client Passbook & Statement of Account", ln=True, align="C")
                pdf.ln(5)

                pdf.set_font("Helvetica", "B", 9)
                pdf.cell(0, 6, f"Client Code / Party: {code} — {name}", ln=True)
                pdf.set_font("Helvetica", "", 9)
                pdf.cell(0, 6, f"District: {dist} | Address: {addr} | Mobile: {mob}", ln=True)
                pdf.ln(4)

                pdf.set_font("Helvetica", "B", 8)
                headers = ["Date", "Invoice", "Particulars", "Qty", "Billed (Rs.)", "Paid (Rs.)", "Balance (Rs.)"]
                col_widths = [22, 22, 50, 12, 28, 28, 28]

                for i, h in enumerate(headers):
                    pdf.cell(col_widths[i], 8, h, border=1, align="C")
                pdf.ln()

                pdf.set_font("Helvetica", "", 7.5)
                for _, r in p_df.iterrows():
                    pdf.cell(col_widths[0], 6, str(r["Date (A.D.)"]), border=1, align="C")
                    pdf.cell(col_widths[1], 6, str(r["Invoice / Ref"]), border=1, align="C")
                    pdf.cell(col_widths[2], 6, str(r["Particulars / Products"])[:25], border=1)
                    pdf.cell(col_widths[3], 6, f"{r['Qty']:g}", border=1, align="C")
                    
                    billed = float(r["Billed Purchase (Rs.)"])
                    paid = float(r["Payment Received (Rs.)"])
                    bal = float(r["Running Balance (Rs.)"])

                    pdf.cell(col_widths[4], 6, f"{billed:,.2f}", border=1, align="R")
                    pdf.cell(col_widths[5], 6, f"{paid:,.2f}", border=1, align="R")
                    pdf.cell(col_widths[6], 6, f"{bal:,.2f}", border=1, align="R")
                    pdf.ln()

                pdf.set_font("Helvetica", "B", 9)
                total_bal = p_df["Running Balance (Rs.)"].sum() if "Running Balance (Rs.)" in p_df.columns else 0.0
                pdf.cell(sum(col_widths[:6]), 8, "Total Current Outstanding Balance:", border=1, align="R")
                pdf.cell(col_widths[6], 8, f"{total_bal:,.2f}", border=1, align="R")

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp_name = tmp.name
                pdf.output(tmp_name)
                with open(tmp_name, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(tmp_name)
                return pdf_bytes

            st.write("")
            passbook_pdf_bytes = generate_passbook_pdf(passbook_view, selected_client, party_name, party_district, party_address, party_mobile)
            st.download_button(
                label=f"📥 Download Official Passbook Statement ({selected_client})",
                data=passbook_pdf_bytes,
                file_name=f"Passbook_Statement_{selected_client}.pdf",
                mime="application/pdf"
            )
            st.markdown("---")

        st.markdown("##### 📊 Summary Ledger Table")
        cols_to_show = ["Date", "Client Code", "District / Area", "Category / Status", "Party Name", "Address", "Mobile No.", "Outstanding Cash (NRs)", "Notes / Status"]
        avail_cols = [c for c in cols_to_show if c in display_df.columns]
        st.dataframe(display_df[avail_cols], use_container_width=True, hide_index=True)

    # =========================================================
    # SEGMENT 2: PRODUCT SALES & BEST SELLERS
    # =========================================================
    elif app_view == "📦 Product Sales & Best Sellers":
        st.subheader("📦 Product Sales Analytics & Best-Seller Tracking")
        st.caption("Track total units sold, FOC/bonus items, revenue generated, and best-selling products date-wise.")

        # Clean numeric quantity and sales columns if present
        prod_df = df.copy()
        if "Qty" in prod_df.columns:
            prod_df["Qty"] = pd.to_numeric(prod_df["Qty"], errors="coerce").fillna(0.0)
        else:
            prod_df["Qty"] = 0.0

        if "FOC Qty" in prod_df.columns:
            prod_df["FOC Qty"] = pd.to_numeric(prod_df["FOC Qty"], errors="coerce").fillna(0.0)
        else:
            prod_df["FOC Qty"] = 0.0

        if "Total Sale (Rs.)" in prod_df.columns:
            prod_df["Total Sale (Rs.)"] = pd.to_numeric(prod_df["Total Sale (Rs.)"], errors="coerce").fillna(0.0)
        else:
            prod_df["Total Sale (Rs.)"] = 0.0

        # Filter out rows without product names
        if "Goods / Product Name" in prod_df.columns:
            valid_prod_df = prod_df[prod_df["Goods / Product Name"].astype(str).str.strip() != ""]
        else:
            valid_prod_df = pd.DataFrame()

        if not valid_prod_df.empty:
            # Aggregate by Product Name
            product_summary = valid_prod_df.groupby("Goods / Product Name").agg(
                Total_Billed_Qty=("Qty", "sum"),
                Total_FOC_Qty=("FOC Qty", "sum"),
                Total_Revenue=("Total Sale (Rs.)", "sum")
            ).reset_index().sort_values(by="Total_Billed_Qty", ascending=False)

            best_seller = product_summary.iloc[0]["Goods / Product Name"] if not product_summary.empty else "N/A"
            best_seller_qty = product_summary.iloc[0]["Total_Billed_Qty"] if not product_summary.empty else 0
            total_units_sold = product_summary["Total_Billed_Qty"].sum()
            total_product_revenue = product_summary["Total_Revenue"].sum()

            # Top Metrics Row
            m1, m2, m3 = st.columns(3)
            m1.metric("🏆 Best-Selling Product", f"{best_seller}", f"{best_seller_qty:g} units sold")
            m2.metric("📦 Total Units Sold", f"{total_units_sold:g} units")
            m3.metric("💰 Total Product Revenue", f"NRs {total_product_revenue:,.2f}")

            st.markdown("---")

            st.markdown("##### 📈 Product Performance Breakdown")
            st.dataframe(
                product_summary.rename(columns={
                    "Goods / Product Name": "Product Name",
                    "Total_Billed_Qty": "Total Billed Qty",
                    "Total_FOC_Qty": "Total Free (FOC) Qty",
                    "Total_Revenue": "Total Revenue (Rs.)"
                }),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Total Revenue (Rs.)": st.column_config.NumberColumn("Total Revenue (Rs.)", format="%.2f")
                }
            )

            if not product_summary.empty:
                st.markdown("##### 📊 Top Products Bar Chart")
                chart_data = product_summary.set_index("Goods / Product Name")[["Total_Billed_Qty"]]
                st.bar_chart(chart_data, use_container_width=True)
        else:
            st.info("📌 No product sales records found in the current sheet data.")

    # =========================================================
    # SEGMENT 3: OPERATING EXPENSES
    # =========================================================
    elif app_view == "💸 Operating Expenses":
        st.subheader("💸 Operating & Field Expenses Analytics")

        exp_cols = ["Date", "Expense Details", "Paid To / Vendor", "Payment Mode", "Expense Amount (Rs.)", "Remarks"]
        
        if "Expense Amount (Rs.)" in df.columns:
            exp_df = df.copy()
            exp_df["Expense Amount (Rs.)"] = pd.to_numeric(exp_df["Expense Amount (Rs.)"], errors="coerce").fillna(0.0)
        else:
            exp_df = pd.DataFrame(columns=exp_cols)

        with st.sidebar:
            with st.expander("📅 Expense Date Filters", expanded=True):
                if "Date" in exp_df.columns and not exp_df["Date"].dropna().empty:
                    available_dates = sorted(exp_df["Date"].dropna().unique().tolist())
                    selected_dates = st.multiselect("Select Dates", options=available_dates, default=available_dates)
                    exp_filtered = exp_df[exp_df["Date"].isin(selected_dates)]
                else:
                    exp_filtered = exp_df

        total_exp_till_date = exp_filtered["Expense Amount (Rs.)"].sum() if "Expense Amount (Rs.)" in exp_filtered.columns else 0.0
        total_entries = len(exp_filtered)

        m1, m2 = st.columns(2)
        m1.metric("Total Operating Expenses (Till Date)", f"NRs {total_exp_till_date:,.2f}")
        m2.metric("Total Expense Entries Logged", f"{total_entries}")

        st.markdown("---")

        if "Date" in exp_filtered.columns and not exp_filtered.empty and total_exp_till_date > 0:
            st.markdown("##### 📈 Date-Wise Expense Trend")
            date_chart = exp_filtered.groupby("Date")["Expense Amount (Rs.)"].sum().reset_index()
            st.bar_chart(date_chart.set_index("Date"), use_container_width=True)

        st.markdown("##### 📋 Detailed Expense Records")
        st.dataframe(exp_filtered, use_container_width=True, hide_index=True)

    # =========================================================
    # SEGMENT 4: STAFF ADVANCES
    # =========================================================
    elif app_view == "💼 Staff Advances":
        st.subheader("💼 Staff Advances & Allowance Disbursements")

        staff_cols = ["Date", "Staff / Personnel Name", "Purpose / Details", "Payment Type", "Advance Amount (Rs.)", "Remarks"]

        if "Advance Amount (Rs.)" in df.columns:
            staff_df = df.copy()
            staff_df["Advance Amount (Rs.)"] = pd.to_numeric(staff_df["Advance Amount (Rs.)"], errors="coerce").fillna(0.0)
        else:
            staff_df = pd.DataFrame(columns=staff_cols)

        total_advances = staff_df["Advance Amount (Rs.)"].sum() if "Advance Amount (Rs.)" in staff_df.columns else 0.0
        total_staff_entries = len(staff_df)

        m1, m2 = st.columns(2)
        m1.metric("Total Staff Advances Disbursed (Till Date)", f"NRs {total_advances:,.2f}")
        m2.metric("Total Disbursement Entries", f"{total_staff_entries}")

        st.markdown("---")

        if "Staff / Personnel Name" in staff_df.columns and not staff_df.empty and total_advances > 0:
            st.markdown("##### 👤 Personnel-Wise Advances Summary")
            staff_chart = staff_df.groupby("Staff / Personnel Name")["Advance Amount (Rs.)"].sum().reset_index()
            st.bar_chart(staff_chart.set_index("Staff / Personnel Name"), use_container_width=True)

        st.markdown("##### 📋 Staff Advance Logs")
        st.dataframe(staff_df, use_container_width=True, hide_index=True)
