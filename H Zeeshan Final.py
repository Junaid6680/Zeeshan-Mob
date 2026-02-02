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

# --- PDF Function (Aapke Number ke saath) ---
def create_pdf(cust_name, phone, items, bill_total, old_bal, paid_amt, is_only_payment=False):
    pdf = FPDF()
    pdf.add_page()
    
    # Shop Header
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(0, 51, 102) # Dark Blue Color
    pdf.cell(190, 12, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, "Contact: 03296971255", ln=True, align='C') # Aapka Number
    pdf.ln(10)
    
    # Bill Details
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 8, f"Customer: {cust_name}")
    pdf.cell(95, 8, f"Date: {pd.Timestamp.now().strftime('%d-%b-%Y')}", ln=True, align='R')
    pdf.cell(95, 8, f"Phone: {phone}")
    pdf.ln(8)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Line divider
    pdf.ln(5)
    
    if not is_only_payment:
        # Table Header
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(85, 10, " Item Description", 1, 0, 'L', True)
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

    # Calculations
    new_bal = (bill_total + old_bal) - paid_amt
    pdf.set_font("Arial", 'B', 11)
    
    if not is_only_payment:
        pdf.cell(150, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(40, 8, f"Rs. {bill_total}", 1, 1, 'C')
    
    pdf.cell(150, 8, "Previous Udhaar:", 0, 0, 'R'); pdf.cell(40, 8, f"Rs. {old_bal}", 1, 1, 'C')
    
    pdf.set_fill_color(220, 255, 220) # Light green for payment
    pdf.cell(150, 8, "Amount Received:", 0, 0, 'R'); pdf.cell(40, 8, f"Rs. {paid_amt}", 1, 1, 'C', True)
    
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(200, 0, 0) # Red for balance
    pdf.cell(150, 10, "Total Remaining Balance:", 0, 0, 'R'); pdf.cell(40, 10, f"Rs. {new_bal}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("📱 Zeeshan Mobile Accessories")
st.write("📍 **Contact: 03296971255**")

col_main, col_sidebar = st.columns([2, 1])

with col_sidebar:
    st.header("👤 Customer Info")
    customer_list = sorted(list(st.session_state.customer_db.keys()))
    selected_cust = st.selectbox("Select Customer", customer_list)
    cust_data = st.session_state.customer_db[selected_cust]
    
    # Separate Backup for each customer
    cust_report = pd.DataFrame([{"Name": selected_cust, "Phone": cust_data['phone'], "Current Balance": cust_data['balance']}])
    st.download_button(f"📥 Download {selected_cust} Ledger", cust_report.to_csv(index=False).encode('utf-8'), f"{selected_cust}_Ledger.csv", "text/csv")
    
    st.info(f"💰 **Balance: Rs. {cust_data['balance']}**")
    
    st.divider()
    st.subheader("💸 Cash Only (No Bill)")
    pay_only = st.number_input("Received Amount", min_value=0.0, key="quick_pay")
    if st.button("Receive & Get Receipt"):
        if pay_only > 0:
            old_b = cust_data['balance']
            st.session_state.customer_db[selected_cust]['balance'] -= pay_only
            pdf_p = create_pdf(selected_cust, cust_data['phone'], [], 0, old_b, pay_only, is_only_payment=True)
            st.download_button("📥 Download Receipt", pdf_p, f"Receipt_{selected_cust}.pdf", "application/pdf")
            st.rerun()

with col_main:
    st.header("📦 New Bill")
    c1, c2, c3 = st.columns([3, 1, 1])
    it_n = c1.text_input("Item Name")
    it_q = c2.number_input("Qty", 1)
    it_p = c3.number_input("Price", 0)
    
    if st.button("➕ Add Item"):
        if it_n:
            st.session_state.temp_items.append({"Item": it_n, "Qty": it_q, "Price": it_p, "Total": it_q * it_p})
    
    if st.session_state.temp_items:
        df = pd.DataFrame(st.session_state.temp_items)
        st.table(df)
        total = df['Total'].sum()
        st.metric("Bill Total", f"Rs. {total}")
        paid = st.number_input("Amount Paid", 0.0)
        
        if st.button("✅ Save & Print Bill"):
            old_b = cust_data['balance']
            st.session_state.customer_db[selected_cust]['balance'] = (total + old_b) - paid
            pdf_b = create_pdf(selected_cust, cust_data['phone'], st.session_state.temp_items, total, old_b, paid)
            st.download_button("📥 Download Bill PDF", pdf_b, f"Bill_{selected_cust}.pdf", "application/pdf")
            st.session_state.temp_items = []
            st.success("Bill Generated!")

# --- Manage Customers Tab ---
st.divider()
with st.expander("➕ Add New Customer to System"):
    n_in = st.text_input("New Name")
    p_in = st.text_input("Phone")
    b_in = st.number_input("Opening Balance", 0.0)
    if st.button("Register Customer"):
        if n_in:
            st.session_state.customer_db[n_in] = {"phone": p_in, "balance": b_in}
            st.rerun()

# --- Search & Ledger ---
st.header("📒 Search Ledger")
search = st.text_input("🔍 Type Name to Search", "")
ledger_df = pd.DataFrame.from_dict(st.session_state.customer_db, orient='index').reset_index()
ledger_df.columns = ["Name", "Phone", "Current Balance"]
if search:
    ledger_df = ledger_df[ledger_df["Name"].str.contains(search, case=False)]
st.dataframe(ledger_df, use_container_width=True)
