import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# Page Settings
st.set_page_config(page_title="Zeeshan Mobile", layout="wide")

# Watermark Style
st.markdown("""
    <style>
    .watermark {
        position: fixed;
        top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        opacity: 0.05; font-size: 80px;
        z-index: -1; pointer-events: none;
    }
    </style>
    <div class="watermark">ZEESHAN MOBILE</div>
    """, unsafe_allow_html=True)

# Data Initialization
if 'db' not in st.session_state:
    st.session_state.db = {} # {Name: balance}
if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("📱 Zeeshan Mobile Accessories")
st.write("Contact: 03296971255")

# Tabs
tab1, tab2 = st.tabs(["🆕 New Bill", "📒 Ledger"])

with tab1:
    # Customer Selection
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        name = st.text_input("Customer Name")
    with c_col2:
        old_bal = st.session_state.db.get(name, 0.0)
        st.warning(f"Previous Balance: Rs. {old_bal}")

    st.divider()

    # Item Entry
    i_col1, i_col2, i_col3 = st.columns([3,1,1])
    item = i_col1.text_input("Item Name")
    qty = i_col2.number_input("Qty", min_value=1)
    price = i_col3.number_input("Price", min_value=0)

    if st.button("Add Item"):
        st.session_state.cart.append({"Item": item, "Qty": qty, "Price": price, "Total": qty*price})

    # Show Bill
    if st.session_state.cart:
        df = pd.DataFrame(st.session_state.cart)
        st.table(df)
        
        bill_total = df['Total'].sum()
        grand_total = bill_total + old_bal
        
        st.write(f"### Current Bill: {bill_total}")
        st.write(f"### Grand Total (with Old): {grand_total}")
        
        paid = st.number_input("Paid Amount", min_value=0)
        rem_bal = grand_total - paid

        if st.button("Save & Generate PDF"):
            # Update Ledger
            st.session_state.db[name] = rem_bal
            
            # PDF logic
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(190, 10, f"Customer: {name} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
            pdf.ln(5)
            for i in st.session_state.cart:
                pdf.cell(190, 8, f"{i['Item']} x {i['Qty']} = {i['Total']}", ln=True)
            pdf.ln(5)
            pdf.cell(190, 10, f"Total Bill: {bill_total}", ln=True)
            pdf.cell(190, 10, f"Paid: {paid}", ln=True)
            pdf.cell(190, 10, f"Remaining Ledger: {rem_bal}", ln=True)
            
            pdf_output = pdf.output(dest='S').encode('latin-1')
            st.download_button("📥 Download Bill", pdf_output, f"{name}_bill.pdf", "application/pdf")
            
            st.session_state.cart = [] # Clear cart
            st.success("Record Saved!")

with tab2:
    st.header("Customer Balances")
    if st.session_state.db:
        st.json(st.session_state.db)
    else:
        st.write("No records found.")
