import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# --- Page Setup ---
st.set_page_config(page_title="Zeeshan Mobile Accessories", layout="wide")

# Database Files
SALES_DB = "sales_history.csv"
LEDGER_DB = "customer_ledger.csv"

# --- Data Persistence ---
if 'all_sales' not in st.session_state:
    if os.path.exists(SALES_DB):
        st.session_state.all_sales = pd.read_csv(SALES_DB).to_dict('records')
    else:
        st.session_state.all_sales = []

if 'ledger' not in st.session_state:
    if os.path.exists(LEDGER_DB):
        st.session_state.ledger = pd.read_csv(LEDGER_DB).set_index('Name').to_dict('index')
    else:
        st.session_state.ledger = {"Walking Customer": {"phone": "-", "balance": 0.0}}

if 'cart' not in st.session_state:
    st.session_state.cart = []

def save_to_disk():
    pd.DataFrame(st.session_state.all_sales).to_csv(SALES_DB, index=False)
    ledger_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index().rename(columns={'index': 'Name'})
    ledger_df.to_csv(LEDGER_DB, index=False)

# --- PDF with Watermark Function ---
def create_pdf_with_watermark(name, items, bill_total, old_bal, paid, inv_id):
    pdf = FPDF()
    pdf.add_page()
    
    # Adding Watermark
    pdf.set_font('Arial', 'B', 50)
    pdf.set_text_color(240, 240, 240) # Very light gray
    pdf.rotate(45, 100, 100)
    pdf.text(30, 190, "ZEESHAN MOBILE")
    pdf.rotate(0) # Reset rotation
    
    # Content
    pdf.set_text_color(0, 0, 0) # Black
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, f"Bill ID: {inv_id} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"Customer: {name}")
    pdf.ln(10)
    
    # Table
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(80, 8, " Item", 1, 0, 'L', True); pdf.cell(30, 8, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 8, "Price", 1, 0, 'C', True); pdf.cell(40, 8, "Total", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    for i in items:
        pdf.cell(80, 8, f" {i['Item']}", 1); pdf.cell(30, 8, str(i['Qty']), 1, 0, 'C')
        pdf.cell(40, 8, str(i['Price']), 1, 0, 'C'); pdf.cell(40, 8, str(i['Total']), 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    grand_total = bill_total + old_bal
    pdf.cell(150, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(40, 8, f"{bill_total}", 1, 1, 'C')
    pdf.cell(150, 8, "Previous Balance:", 0, 0, 'R'); pdf.cell(40, 8, f"{old_bal}", 1, 1, 'C')
    pdf.cell(150, 8, "Total Amount:", 0, 0, 'R'); pdf.cell(40, 8, f"{grand_total}", 1, 1, 'C')
    pdf.cell(150, 8, "Paid:", 0, 0, 'R'); pdf.cell(40, 8, f"{paid}", 1, 1, 'C')
    pdf.set_text_color(255, 0, 0)
    pdf.cell(150, 8, "Remaining Balance:", 0, 0, 'R'); pdf.cell(40, 8, f"{grand_total - paid}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- UI ---
st.title("📱 Zeeshan Mobile Accessories")

tabs = st.tabs(["🆕 New Bill", "🔍 Search & History", "📊 Monthly Report", "📒 Ledger & Customers"])

with tabs[0]:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Select Customer")
        c_list = list(st.session_state.ledger.keys())
        # Dropdown for existing customers
        selected_c = st.selectbox("Choose Customer", c_list)
        old_bal = st.session_state.ledger[selected_c]['balance']
        st.warning(f"Previous Balance: Rs. {old_bal}")

    with c2:
        st.subheader("Item Entry")
        it_name = st.text_input("Item Name")
        colq, colp = st.columns(2)
        it_qty = colq.number_input("Qty", min_value=1, value=1)
        it_prc = colp.number_input("Price", min_value=0, value=0)
        if st.button("Add Item"):
            if it_name:
                st.session_state.cart.append({"Item": it_name, "Qty": it_qty, "Price": it_prc, "Total": it_qty * it_prc})

    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        bill_total = df_cart['Total'].sum()
        paid = st.number_input("Kitne Paise Diye?", min_value=0, value=0)
        
        if st.button("✅ Bill Final Karein"):
            inv_id = f"ZM-{datetime.now().strftime('%H%M%S')}"
            for item in st.session_state.cart:
                rec = item.copy()
                rec.update({"BillID": inv_id, "Customer": selected_c, "Date": datetime.now().strftime("%Y-%m-%d")})
                st.session_state.all_sales.append(rec)
            
            # Ledger calculation
            new_bal = (bill_total + old_bal) - paid
            st.session_state.ledger[selected_c]['balance'] = new_bal
            save_to_disk()
            
            # PDF Generation
            pdf_data = create_pdf_with_watermark(selected_c, st.session_state.cart, bill_total, old_bal, paid, inv_id)
            st.download_button("📥 Download Bill PDF", pdf_data, f"Bill_{selected_c}.pdf", "application/pdf")
            
            st.session_state.cart = []
            st.success("Record Saved!")

with tabs[3]:
    st.subheader("Manage Customers")
    # Section to add new customer
    with st.expander("➕ Add New Customer"):
        new_cust_name = st.text_input("Enter New Name")
        if st.button("Save New Customer"):
            if new_cust_name and new_cust_name not in st.session_state.ledger:
                st.session_state.ledger[new_cust_name] = {"phone": "-", "balance": 0.0}
                save_to_disk()
                st.success(f"{new_cust_name} added!")
                st.rerun()
    
    st.divider()
    st.subheader("Customer Ledger")
    led_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index()
    led_df.columns = ["Customer Name", "Phone", "Balance"]
    st.table(led_df)

with tabs[1]:
    st.subheader("Search Records")
    if st.session_state.all_sales:
        df_history = pd.DataFrame(st.session_state.all_sales)
        search = st.text_input("Search by Name or ID")
        st.dataframe(df_history[df_history['Customer'].str.contains(search, case=False) | df_history['BillID'].str.contains(search, case=False)])

with tabs[2]:
    st.subheader("Monthly Report")
    if st.session_state.all_sales:
        df_rep = pd.DataFrame(st.session_state.all_sales)
        df_rep['Month'] = pd.to_datetime(df_rep['Date']).dt.strftime('%B %Y')
        sel_month = st.selectbox("Select Month", df_rep['Month'].unique())
        m_data = df_rep[df_rep['Month'] == sel_month]
        st.table(m_data.groupby('Item').agg({'Qty': 'sum', 'Total': 'sum'}).reset_index())
