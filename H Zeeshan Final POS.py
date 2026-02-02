import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# --- Page Config ---
st.set_page_config(page_title="Zeeshan Mobile POS", layout="wide")

# --- CSS for Watermark ---
st.markdown("""
    <style>
    .watermark {
        position: fixed;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        opacity: 0.05; font-size: 80px; color: gray;
        z-index: -1; pointer-events: none;
    }
    </style>
    <div class="watermark">ZEESHAN MOBILE ACCESSORIES</div>
    """, unsafe_allow_html=True)

# --- Data Persistence ---
if 'customer_db' not in st.session_state:
    st.session_state.customer_db = {"Walking Customer": {"phone": "-", "balance": 0.0}}

if 'temp_items' not in st.session_state:
    st.session_state.temp_items = []

# --- PDF Function with Watermark ---
def create_pdf(cust_name, phone, items, bill_total, old_bal, paid_amt, is_only_payment=False):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Background Watermark
    pdf.set_font("Arial", 'B', 50)
    pdf.set_text_color(240, 240, 240)
    pdf.text(35, 150, "ZEESHAN MOBILE")
    
    # Header
    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", 'B', 22)
    pdf.cell(190, 12, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, "Contact: 03296971255", ln=True, align='C')
    pdf.ln(10)
    
    # Customer Details
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 8, f"Customer: {cust_name}")
    pdf.cell(95, 8, f"Date: {pd.Timestamp.now().strftime('%d-%b-%Y')}", ln=True, align='R')
    pdf.cell(95, 8, f"Phone: {phone}")
    pdf.ln(8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    if not is_only_payment:
        # Table Header
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(85, 10, " Item (Use - for Return)", 1, 0, 'L', True)
        pdf.cell(25, 10, "Qty", 1, 0, 'C', True)
        pdf.cell(40, 10, "Price", 1, 0, 'C', True)
        pdf.cell(40, 10, "Total", 1, 1, 'C', True)
        
        # Items
        pdf.set_font("Arial", '', 10)
        for item in items:
            pdf.cell(85, 10, f" {item['Item']}", 1)
            pdf.cell(25, 10, str(item['Qty']), 1, 0, 'C')
            pdf.cell(40, 10, str(item['Price']), 1, 0, 'C')
            pdf.cell(40, 10, str(item['Total']), 1, 1, 'C')
        pdf.ln(5)

    # Totals
    new_bal = (bill_total + old_bal) - paid_amt
    pdf.set_font("Arial", 'B', 11)
    if not is_only_payment:
        pdf.cell(150, 8, "Current Bill Total:", 0, 0, 'R'); pdf.cell(40, 8, f"{bill_total}", 1, 1, 'C')
    
    pdf.cell(150, 8, "Previous Udhaar:", 0, 0, 'R'); pdf.cell(40, 8, f"{old_bal}", 1, 1, 'C')
    pdf.set_fill_color(220, 255, 220)
    pdf.cell(150, 8, "Amount Received:", 0, 0, 'R'); pdf.cell(40, 8, f"{paid_amt}", 1, 1, 'C', True)
    
    pdf.set_text_color(200, 0, 0)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(150, 10, "New Balance:", 0, 0, 'R'); pdf.cell(40, 10, f"{new_bal}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI Layout ---
st.title("📱 Zeeshan Mobile POS")
st.write("Contact: **03296971255**")

col_main, col_sidebar = st.columns([2, 1])

with col_sidebar:
    st.header("👤 Customer Ledger")
    c_list = sorted(list(st.session_state.customer_db.keys()))
    sel_c = st.selectbox("Select Customer", c_list)
    c_data = st.session_state.customer_db[sel_c]
    
    st.info(f"💰 Current Udhaar: **Rs. {c_data['balance']}**")
    
    # Receive Payment only
    st.subheader("Wasooli (No Bill)")
    wasool = st.number_input("Amount Received", 0.0, key="w1")
    if st.button("Save Payment"):
        if wasool > 0:
            st.session_state.customer_db[sel_c]['balance'] -= wasool
            pdf_w = create_pdf(sel_c, c_data['phone'], [], 0, c_data['balance']+wasool, wasool, True)
            st.download_button("📥 Get Receipt", pdf_w, f"Receipt_{sel_c}.pdf", "application/pdf")
            st.rerun()

with col_main:
    st.header("📦 Billing & Returns")
    st.write("_Hint: Item return ke liye Quantity ko minus mein likhein (e.g. -1)_")
    
    c1, c2, c3 = st.columns([3, 1, 1])
    it_name = c1.text_input("Item")
    # Return ke liye step -1 set kiya hai
    it_qty = c2.number_input("Qty", step=1, value=1)
    it_prc = c3.number_input("Price", 0)
    
    if st.button("Add to List"):
        if it_name:
            st.session_state.temp_items.append({"Item": it_name, "Qty": it_qty, "Price": it_prc, "Total": it_qty * it_prc})
    
    if st.session_state.temp_items:
        df = pd.DataFrame(st.session_state.temp_items)
        st.table(df)
        b_total = df['Total'].sum()
        st.write(f"### Final Total: {b_total}")
        
        amt_paid = st.number_input("Amount Paid Today", 0.0)
        
        if st.button("Finalize & Save Bill"):
            old_b = c_data['balance']
            st.session_state.customer_db[sel_c]['balance'] = (b_total + old_b) - amt_paid
            
            pdf_b = create_pdf(sel_c, c_data['phone'], st.session_state.temp_items, b_total, old_b, amt_paid)
            st.download_button("📥 Download PDF Bill (Watermarked)", pdf_b, f"Bill_{sel_c}.pdf", "application/pdf")
            
            st.session_state.temp_items = []
            st.success("Record Updated!")

# --- Ledger Search & Backup ---
st.divider()
st.header("📒 Ledger Record & Backup")
search_n = st.text_input("Search Name")
l_df = pd.DataFrame.from_dict(st.session_state.customer_db, orient='index').reset_index()
l_df.columns = ["Name", "Phone", "Balance"]
if search_n:
    l_df = l_df[l_df["Name"].str.contains(search_n, case=False)]
st.dataframe(l_df, use_container_width=True)

# Full System Backup
csv_file = l_df.to_csv(index=False).encode('utf-8')
st.download_button("💾 Download Full Backup (CSV)", csv_file, "Zeeshan_Mobile_Backup.csv", "text/csv")
