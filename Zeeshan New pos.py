import streamlit as st
import pandas as pd
from fpdf import FPDF
import os

# --- Page Config ---
st.set_page_config(page_title="Zeeshan Mobile POS", layout="wide")

# --- CSS for Watermark & Style ---
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

# --- Data Persistence (Session State) ---
if 'customer_db' not in st.session_state:
    st.session_state.customer_db = {"Walking Customer": {"phone": "-", "balance": 0.0}}

if 'temp_items' not in st.session_state:
    st.session_state.temp_items = []

# --- PDF Generation Function ---
def create_pdf(cust_name, phone, items, bill_total, old_bal, paid_amt, is_only_payment=False):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 7, "Contact: 03296971255", ln=True, align='C') # Aapka Number
    pdf.ln(10)
    
    # Customer Info
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 8, f"Customer: {cust_name}")
    pdf.cell(95, 8, f"Date: {pd.Timestamp.now().strftime('%d-%b-%Y')}", ln=True, align='R')
    pdf.cell(95, 8, f"Phone: {phone}")
    pdf.ln(10)
    
    if not is_only_payment:
        # Table Header
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(80, 10, "Item Name", 1, 0, 'C', True)
        pdf.cell(30, 10, "Qty", 1, 0, 'C', True)
        pdf.cell(40, 10, "Unit Price", 1, 0, 'C', True)
        pdf.cell(40, 10, "Total", 1, 1, 'C', True)
        # Table Rows
        pdf.set_font("Arial", '', 10)
        for item in items:
            pdf.cell(80, 10, f" {item['Item']}", 1)
            pdf.cell(30, 10, str(item['Qty']), 1, 0, 'C')
            pdf.cell(40, 10, str(item['Price']), 1, 0, 'C')
            pdf.cell(40, 10, str(item['Total']), 1, 1, 'C')
        pdf.ln(5)

    # Summary
    new_bal = (bill_total + old_bal) - paid_amt
    pdf.set_font("Arial", 'B', 10)
    
    if not is_only_payment:
        pdf.cell(150, 8, "Current Bill:", 0, 0, 'R')
        pdf.cell(40, 8, f"Rs. {bill_total}", 1, 1, 'C')
    
    pdf.cell(150, 8, "Previous Balance (Udhaar):", 0, 0, 'R')
    pdf.cell(40, 8, f"Rs. {old_bal}", 1, 1, 'C')
    
    pdf.set_fill_color(200, 255, 200)
    pdf.cell(150, 8, "Amount Received / Paid:", 0, 0, 'R')
    pdf.cell(40, 8, f"Rs. {paid_amt}", 1, 1, 'C', True)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(150, 10, "New Remaining Balance:", 0, 0, 'R')
    pdf.cell(40, 10, f"Rs. {new_bal}", 1, 1, 'C')
    
    if is_only_payment:
        pdf.ln(20)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 10, "Note: This is a payment receipt for ledger clearance only.", ln=True, align='C')

    return pdf.output(dest='S').encode('latin-1')

# --- UI Interface ---
st.title("🛒 Zeeshan Mobile Accessories POS")

col_main, col_sidebar = st.columns([2, 1])

with col_sidebar:
    st.header("👤 Customer & Payment")
    
    # Selection
    customer_list = sorted(list(st.session_state.customer_db.keys()))
    selected_cust = st.selectbox("Select Customer", customer_list)
    cust_data = st.session_state.customer_db[selected_cust]
    
    st.info(f"📌 **Balance: Rs. {cust_data['balance']}**")
    
    st.divider()
    # --- NEW FEATURE: ONLY PAYMENT RECEIVE ---
    st.subheader("💸 Quick Ledger Payment")
    st.write("Sirf paise wasool karne ke liye:")
    pay_only = st.number_input("Received Amount", min_value=0.0, key="pay_only")
    
    if st.button("Confirm Payment (No Bill)"):
        if pay_only > 0:
            old_b = cust_data['balance']
            st.session_state.customer_db[selected_cust]['balance'] -= pay_only
            
            # Receipt for payment only
            pdf_p = create_pdf(selected_cust, cust_data['phone'], [], 0, old_b, pay_only, is_only_payment=True)
            st.download_button("📥 Download Payment Receipt", pdf_p, f"Receipt_{selected_cust}.pdf", "application/pdf")
            st.success(f"Payment Received! New balance: {st.session_state.customer_db[selected_cust]['balance']}")
            st.rerun()

    st.divider()
    with st.expander("Add New Customer"):
        name_in = st.text_input("Full Name")
        phone_in = st.text_input("Phone Number")
        init_bal = st.number_input("Opening Balance", min_value=0.0)
        if st.button("Save"):
            if name_in:
                st.session_state.customer_db[name_in] = {"phone": phone_in, "balance": init_bal}
                st.rerun()

with col_main:
    st.header("📦 Billing Section")
    c1, c2, c3 = st.columns([3, 1, 1])
    item_name = c1.text_input("Item Description")
    item_qty = c2.number_input("Qty", min_value=1, value=1)
    item_price = c3.number_input("Price", min_value=0, value=0)
    
    if st.button("➕ Add Item"):
        if item_name:
            st.session_state.temp_items.append({"Item": item_name, "Qty": item_qty, "Price": item_price, "Total": item_qty * item_price})
    
    if st.session_state.temp_items:
        df = pd.DataFrame(st.session_state.temp_items)
        st.table(df)
        curr_total = df['Total'].sum()
        st.metric("Total Bill", f"Rs. {curr_total}")
        paid_today = st.number_input("Paid with Bill", min_value=0.0)
        
        if st.button("✅ Finalize & Save Bill"):
            old_b = cust_data['balance']
            st.session_state.customer_db[selected_cust]['balance'] = (curr_total + old_b) - paid_today
            pdf_d = create_pdf(selected_cust, cust_data['phone'], st.session_state.temp_items, curr_total, old_b, paid_today)
            st.download_button("📥 Download Bill PDF", pdf_d, f"Bill_{selected_cust}.pdf", "application/pdf")
            st.session_state.temp_items = []
            st.rerun()
    else:
        st.warning("Bill empty.")

# --- Ledger & Search ---
st.divider()
st.header("📒 Ledger Overview")
search = st.text_input("🔍 Search Name", "")
ledger_df = pd.DataFrame.from_dict(st.session_state.customer_db, orient='index').reset_index()
ledger_df.columns = ["Customer", "Phone", "Balance"]
if search:
    ledger_df = ledger_df[ledger_df["Customer"].str.contains(search, case=False)]
st.dataframe(ledger_df, use_container_width=True)

csv = ledger_df.to_csv(index=False).encode('utf-8')
st.download_button("💾 Backup Ledger (CSV)", csv, "Zeeshan_Backup.csv", "text/csv")
