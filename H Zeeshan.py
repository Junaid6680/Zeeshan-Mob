import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- Page Setup ---
st.set_page_config(page_title="Zeeshan Mobile", layout="wide")

# Database Files
SALES_DB = "sales_history.csv"
LEDGER_DB = "customer_ledger.csv"

# --- Data Persistence ---
if 'all_sales' not in st.session_state:
    st.session_state.all_sales = pd.read_csv(SALES_DB).to_dict('records') if os.path.exists(SALES_DB) else []

if 'ledger' not in st.session_state:
    if os.path.exists(LEDGER_DB):
        st.session_state.ledger = pd.read_csv(LEDGER_DB).set_index('Name').to_dict('index')
    else:
        st.session_state.ledger = {"Walking Customer": {"balance": 0.0}}

if 'cart' not in st.session_state:
    st.session_state.cart = []

def save_data():
    pd.DataFrame(st.session_state.all_sales).to_csv(SALES_DB, index=False)
    ledger_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index().rename(columns={'index': 'Name'})
    ledger_df.to_csv(LEDGER_DB, index=False)

# --- PDF Function with Watermark & Number ---
def get_bill_pdf(name, items, b_total, o_bal, paid, inv_id):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Watermark
    pdf.set_font("Arial", 'B', 40)
    pdf.set_text_color(240, 240, 240)
    pdf.text(35, 150, "ZEESHAN MOBILE")
    
    # 2. Header with Number
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 7, "Contact: 03296971255", ln=True, align='C')
    pdf.cell(190, 5, f"Bill ID: {inv_id} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    # 3. Customer Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Customer: {name}", ln=True)
    
    # 4. Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 8, " Item", 1, 0, 'L', True); pdf.cell(25, 8, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 8, "Price", 1, 0, 'C', True); pdf.cell(45, 8, "Total", 1, 1, 'C', True)
    
    # 5. Items
    pdf.set_font("Arial", '', 10)
    for i in items:
        pdf.cell(80, 8, f" {i['Item']}", 1); pdf.cell(25, 8, str(i['Qty']), 1, 0, 'C')
        pdf.cell(40, 8, str(i['Price']), 1, 0, 'C'); pdf.cell(45, 8, str(i['Total']), 1, 1, 'C')
    
    # 6. Totals
    pdf.ln(5); pdf.set_font("Arial", 'B', 11)
    grand = b_total + o_bal
    pdf.cell(145, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(45, 8, f"{b_total}", 1, 1, 'C')
    pdf.cell(145, 8, "Previous Udhaar:", 0, 0, 'R'); pdf.cell(45, 8, f"{o_bal}", 1, 1, 'C')
    pdf.cell(145, 8, "Grand Total:", 0, 0, 'R'); pdf.cell(45, 8, f"{grand}", 1, 1, 'C')
    pdf.cell(145, 8, "Paid Amount:", 0, 0, 'R'); pdf.cell(45, 8, f"{paid}", 1, 1, 'C')
    pdf.set_text_color(200, 0, 0)
    pdf.cell(145, 8, "New Balance:", 0, 0, 'R'); pdf.cell(45, 8, f"{grand - paid}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- Main App ---
st.title("📱 Zeeshan Mobile Accessories")
st.write("### 📞 Contact: 03296971255")

tab1, tab2 = st.tabs(["🛒 Billing", "👥 Customer Management"])

with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        # Load Latest Customer List
        customer_list = list(st.session_state.ledger.keys())
        selected_customer = st.selectbox("Select Customer Name", customer_list)
        old_balance = st.session_state.ledger[selected_customer]['balance']
        st.info(f"Purana Udhaar: Rs. {old_balance}")

    with c2:
        it_name = st.text_input("Item Name")
        col_q, col_p = st.columns(2)
        it_qty = col_q.number_input("Qty", 1)
        it_prc = col_p.number_input("Price", 0)
        if st.button("➕ Add Item"):
            if it_name:
                st.session_state.cart.append({"Item": it_name, "Qty": it_qty, "Price": it_prc, "Total": it_qty*it_prc})
                st.rerun()

    if st.session_state.cart:
        st.table(pd.DataFrame(st.session_state.cart))
        total_bill = sum(item['Total'] for item in st.session_state.cart)
        st.write(f"### Current Bill: Rs. {total_bill}")
        
        cash_paid = st.number_input("Paid Amount", 0)
        
        if st.button("✅ Save & Generate Bill"):
            bill_id = f"Z-{datetime.now().strftime('%H%M%S')}"
            for item in st.session_state.cart:
                rec = item.copy()
                rec.update({"BillID": bill_id, "Customer": selected_customer, "Date": datetime.now().strftime("%Y-%m-%d")})
                st.session_state.all_sales.append(rec)
            
            # Update Ledger
            new_bal = (total_bill + old_balance) - cash_paid
            st.session_state.ledger[selected_customer]['balance'] = float(new_bal)
            save_data()
            
            # Generate PDF
            pdf_out = get_bill_pdf(selected_customer, st.session_state.cart, total_bill, old_balance, cash_paid, bill_id)
            st.download_button("📥 Download PDF Bill", pdf_out, f"Bill_{selected_customer}.pdf", "application/pdf")
            
            st.session_state.cart = []
            st.success("Saved Successfully!")

with tab2:
    st.subheader("Add New Customer")
    with st.form("add_cust"):
        name_input = st.text_input("Enter Full Name")
        if st.form_submit_button("Save Customer"):
            if name_input and name_input not in st.session_state.ledger:
                st.session_state.ledger[name_input] = {"balance": 0.0}
                save_data()
                st.success(f"{name_input} added!")
                st.rerun()
    
    st.divider()
    st.subheader("Customer Ledger Record")
    st.dataframe(pd.DataFrame.from_dict(st.session_state.ledger, orient='index'))
