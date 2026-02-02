import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Zeeshan Mobile POS", layout="wide")

# --- Custom Styling & Watermark ---
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
    }
    .watermark {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        opacity: 0.05;
        font-size: 70px;
        font-weight: bold;
        color: #000;
        z-index: -1;
        pointer-events: none;
    }
    </style>
    <div class="watermark">ZEESHAN MOBILE ACCESSORIES</div>
    """, unsafe_allow_html=True)

# --- Session State (Data Storage) ---
if 'customer_records' not in st.session_state:
    st.session_state.customer_records = {} # {Name: {'phone': '', 'balance': 0.0}}

if 'current_items' not in st.session_state:
    st.session_state.current_items = []

# --- PDF Builder Function ---
def create_professional_bill(name, phone, items, bill_total, old_bal, paid_amt):
    pdf = FPDF()
    pdf.add_page()
    
    # Shop Header
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(0, 51, 102) # Dark Blue
    pdf.cell(190, 12, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, "Contact: 03296971255", ln=True, align='C')
    pdf.ln(10)
    
    # Bill Info Table
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 8, f"Customer: {name}", border='B')
    pdf.cell(95, 8, f"Date: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}", border='B', ln=True, align='R')
    pdf.cell(190, 8, f"Contact: {phone}", border='B', ln=True)
    pdf.ln(5)
    
    # Items Header
    pdf.set_fill_color(0, 51, 102)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(80, 10, " Description", 1, 0, 'L', True)
    pdf.cell(30, 10, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 10, "Rate", 1, 0, 'C', True)
    pdf.cell(40, 10, "Amount", 1, 1, 'C', True)
    
    # Items list
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    for item in items:
        pdf.cell(80, 10, f" {item['Item']}", 1)
        pdf.cell(30, 10, str(item['Qty']), 1, 0, 'C')
        pdf.cell(40, 10, f"{item['Price']:.2f}", 1, 0, 'C')
        pdf.cell(40, 10, f"{item['Total']:.2f}", 1, 1, 'C')
    
    # Calculation Box
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    new_bal = (bill_total + old_bal) - paid_amt
    
    # Summary Rows
    def add_row(label, value, is_bold=False):
        pdf.cell(150, 8, label, 0, 0, 'R')
        pdf.cell(40, 8, f"Rs. {value:.2f}", 1, 1, 'C')

    add_row("Current Bill Total", bill_total)
    add_row("Previous Balance", old_bal)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(150, 8, "NET TOTAL (Payable)", 0, 0, 'R')
    pdf.cell(40, 8, f"Rs. {bill_total + old_bal:.2f}", 1, 1, 'C', True)
    add_row("Amount Paid Today", paid_amt)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(150, 12, "CLOSING BALANCE (Ladger)", 0, 0, 'R')
    pdf.cell(40, 12, f"Rs. {new_bal:.2f}", 1, 1, 'C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(190, 5, "Software Generated Receipt - No Signature Required", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- MAIN APP UI ---
st.title("Zeeshan Mobile Accessories - POS")

tab_bill, tab_ledger = st.tabs(["📄 New Invoice", "📒 Customer Ledger"])

with tab_bill:
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Customer Details")
        cust_action = st.radio("Action", ["Select Existing", "Add New Customer"], horizontal=True)
        
        if cust_action == "Add New Customer":
            n_name = st.text_input("New Name")
            n_phone = st.text_input("New Phone")
            n_bal = st.number_input("Opening Balance", min_value=0.0)
            if st.button("Save Customer"):
                if n_name:
                    st.session_state.customer_records[n_name] = {'phone': n_phone, 'balance': n_bal}
                    st.success("Added!")
                    st.rerun()
        
        all_custs = list(st.session_state.customer_records.keys())
        active_cust = st.selectbox("Search Customer", ["Walking Customer"] + all_custs)
        
        # Get data for active customer
        current_data = st.session_state.customer_records.get(active_cust, {'phone': '-', 'balance': 0.0})
        st.write(f"**Phone:** {current_data['phone']}")
        st.metric("Old Ledger Balance", f"Rs. {current_data['balance']}")

    with c2:
        st.subheader("Items Entry")
        with st.container(border=True):
            ic1, ic2, ic3 = st.columns([3,1,1])
            it_name = ic1.text_input("Item Name")
            it_qty = ic2.number_input("Qty", min_value=1, step=1)
            it_prc = ic3.number_input("Price", min_value=0.0)
            
            if st.button("➕ Add Item", use_container_width=True):
                if it_name:
                    st.session_state.current_items.append({
                        "Item": it_name, "Qty": it_qty, "Price": it_prc, "Total": it_qty * it_prc
                    })

        if st.session_state.current_items:
            df = pd.DataFrame(st.session_state.current_items)
            st.dataframe(df, use_container_width=True)
            
            col_sum1, col_sum2 = st.columns(2)
            bill_total = df['Total'].sum()
            col_sum1.metric("Bill Total", f"Rs. {bill_total}")
            
            pay_amt = col_sum2.number_input("Paid Today", min_value=0.0)
            
            if st.button("🚀 Finalize Bill & Generate PDF", use_container_width=True):
                # Update Ledger
                old_bal = current_data['balance']
                new_bal = (bill_total + old_bal) - pay_amt
                
                if active_cust != "Walking Customer":
                    st.session_state.customer_records[active_cust]['balance'] = new_bal
                
                # Create PDF
                pdf_bytes = create_professional_bill(active_cust, current_data['phone'], st.session_state.current_items, bill_total, old_bal, pay_amt)
                
                st.download_button(
                    label="📥 Click here to Download PDF",
                    data=pdf_bytes,
                    file_name=f"Bill_{active_cust}_{datetime.now().strftime('%d%m%Y')}.pdf",
                    mime="application/pdf"
                )
                
                # Clear items
                st.session_state.current_items = []
                st.success("Record updated successfully!")

with tab_ledger:
    st.subheader("All Customers Balance Sheet")
    if st.session_state.customer_records:
        ledger_data = []
        for name, data in st.session_state.customer_records.items():
            ledger_data.append({"Name": name, "Phone": data['phone'], "Current Balance": data['balance']})
        
        st.table(pd.DataFrame(ledger_data))
    else:
        st.info("No customer records yet.")
