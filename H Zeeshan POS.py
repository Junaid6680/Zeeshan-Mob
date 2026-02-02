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

# --- Load Data ---
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

# --- PDF Generation with Watermark ---
def generate_bill_pdf(name, items, bill_total, old_bal, paid, inv_id):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. Simple Watermark (Text Background)
    pdf.set_font("Arial", 'B', 40)
    pdf.set_text_color(240, 240, 240)
    pdf.text(40, 150, "ZEESHAN MOBILE ACCESSORIES")
    
    # 2. Header
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, f"Bill ID: {inv_id} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    # 3. Customer Info
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Customer: {name}", ln=True)
    pdf.ln(2)
    
    # 4. Items Table
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 8, " Item Description", 1, 0, 'L', True)
    pdf.cell(25, 8, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 8, "Price", 1, 0, 'C', True)
    pdf.cell(45, 8, "Total", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    for i in items:
        pdf.cell(80, 8, f" {i['Item']}", 1)
        pdf.cell(25, 8, str(i['Qty']), 1, 0, 'C')
        pdf.cell(40, 8, str(i['Price']), 1, 0, 'C')
        pdf.cell(45, 8, str(i['Total']), 1, 1, 'C')
    
    # 5. Totals
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    g_total = bill_total + old_bal
    pdf.cell(145, 8, "Current Bill Total:", 0, 0, 'R'); pdf.cell(45, 8, f"Rs. {bill_total}", 1, 1, 'C')
    pdf.cell(145, 8, "Old Balance:", 0, 0, 'R'); pdf.cell(45, 8, f"Rs. {old_bal}", 1, 1, 'C')
    pdf.cell(145, 8, "Grand Total:", 0, 0, 'R'); pdf.cell(45, 8, f"Rs. {g_total}", 1, 1, 'C')
    pdf.cell(145, 8, "Paid Amount:", 0, 0, 'R'); pdf.cell(45, 8, f"Rs. {paid}", 1, 1, 'C')
    
    pdf.set_text_color(200, 0, 0)
    pdf.cell(145, 8, "Remaining Balance:", 0, 0, 'R'); pdf.cell(45, 8, f"Rs. {g_total - paid}", 1, 1, 'C')
    
    return pdf.output()

# --- Main UI ---
st.title("📱 Zeeshan Mobile Accessories")

t1, t2, t3, t4 = st.tabs(["🆕 New Bill", "📒 Customers & Ledger", "🔍 Sales History", "📊 Report"])

# --- TAB 1: BILLING ---
with t1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Billing Details")
        cust_names = list(st.session_state.ledger.keys())
        selected_cust = st.selectbox("Select Customer", cust_names)
        current_old_bal = st.session_state.ledger[selected_cust]['balance']
        st.info(f"Old Balance: Rs. {current_old_bal}")
        
    with c2:
        st.subheader("Add Items")
        it_name = st.text_input("Item Name")
        q_col, p_col = st.columns(2)
        it_qty = q_col.number_input("Quantity", min_value=1, value=1)
        it_prc = p_col.number_input("Price", min_value=0, value=0)
        if st.button("➕ Add Item"):
            if it_name:
                st.session_state.cart.append({"Item": it_name, "Qty": it_qty, "Price": it_prc, "Total": it_qty * it_prc})
                st.rerun()

    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        
        total_of_bill = df_cart['Total'].sum()
        st.write(f"### Bill Total: Rs. {total_of_bill}")
        
        amt_paid = st.number_input("Amount Paid Now", min_value=0, value=0)
        
        if st.button("✅ Save & Generate Bill"):
            bill_id = f"INV-{datetime.now().strftime('%H%M%S')}"
            # Save History
            for item in st.session_state.cart:
                entry = item.copy()
                entry.update({"BillID": bill_id, "Customer": selected_cust, "Date": datetime.now().strftime("%Y-%m-%d")})
                st.session_state.all_sales.append(entry)
            
            # Update Balance
            new_bal = (total_of_bill + current_old_bal) - amt_paid
            st.session_state.ledger[selected_cust]['balance'] = float(new_bal)
            save_data()
            
            # PDF
            bill_pdf = generate_bill_pdf(selected_cust, st.session_state.cart, total_of_bill, current_old_bal, amt_paid, bill_id)
            st.download_button("📥 Download PDF Bill", bill_pdf, f"Bill_{selected_cust}.pdf", "application/pdf")
            
            st.session_state.cart = []
            st.success("Record Saved Successfully!")

# --- TAB 2: CUSTOMERS (New Customer yahan se add hoga) ---
with t2:
    st.subheader("Manage Customers")
    with st.form("Add Customer"):
        new_c_name = st.text_input("New Customer Name")
        if st.form_submit_button("Save New Customer"):
            if new_c_name and new_c_name not in st.session_state.ledger:
                st.session_state.ledger[new_c_name] = {"balance": 0.0}
                save_data()
                st.success(f"Customer '{new_c_name}' added!")
                st.rerun()
            else:
                st.error("Name already exists or empty!")

    st.divider()
    st.subheader("Current Ledger (Udhaar Record)")
    l_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index()
    l_df.columns = ["Name", "Current Balance (Rs.)"]
    st.dataframe(l_df, use_container_width=True)

# --- TAB 3: HISTORY ---
with t3:
    st.subheader("Search Sales Record")
    if st.session_state.all_sales:
        history_df = pd.DataFrame(st.session_state.all_sales)
        search = st.text_input("Search Name or Bill ID")
        st.dataframe(history_df[history_df['Customer'].str.contains(search, case=False) | history_df['BillID'].str.contains(search, case=False)])

# --- TAB 4: REPORT ---
with t4:
    st.subheader("Monthly Sale Report")
    if st.session_state.all_sales:
        report_df = pd.DataFrame(st.session_state.all_sales)
        report_df['Month'] = pd.to_datetime(report_df['Date']).dt.strftime('%B %Y')
        selected_m = st.selectbox("Select Month", report_df['Month'].unique())
        m_data = report_df[report_df['Month'] == selected_m]
        st.table(m_data.groupby('Item').agg({'Qty': 'sum', 'Total': 'sum'}).reset_index())
