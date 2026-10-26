# PDF Generation Function
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
        
        # Return bytes directly
        return pdf.output()
