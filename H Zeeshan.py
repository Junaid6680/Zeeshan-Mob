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
        # Default Customer
        st.session_state.ledger = {"Walking Customer": {"balance": 0.0}}

if 'cart' not in st.session_state:
    st.session_state.cart = []

def save_data():
    pd.DataFrame(st.session_state.all_sales).to_csv(SALES_DB, index=False)
    ledger_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index().rename(columns={'index': 'Name'})
    ledger_df.to_csv(LEDGER_DB, index=False)

# --- Header Section ---
st.title("📱 Zeeshan Mobile Accessories")
st.subheader("📞 Contact: 03296971255")
st.divider()

# --- Watermark Logic for PDF ---
def get_bill_pdf(name, items, b_total, o_bal, paid, inv_id):
    pdf = FPDF()
    pdf.add_page()
    
    # Simple Watermark
    pdf.set_font("Arial", 'B', 45)
    pdf.set_text_color(245, 245, 245)
    pdf.text(35, 150, "ZEESHAN MOBILE")
    
    # Bill Content
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(190, 5, f"Contact: 03296971255 | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Customer: {name} | Bill ID: {inv_id}", ln=True)
    
    # Table Header
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(90, 8, " Item Name", 1, 0, 'L', True)
    pdf.cell(30, 8, "Qty", 1, 0, 'C', True)
    pdf.cell(30, 8, "Price", 1, 0, 'C', True)
    pdf.cell(40, 8, "Total", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    for i in items:
        pdf.cell(90, 8, f" {i['Item']}", 1)
        pdf.cell(30, 8, str(i['Qty']), 1, 0, 'C')
        pdf.cell(30, 8, str(i['Price']), 1, 0, 'C')
        pdf.cell(40, 8, str(i['Total']), 1, 1, 'C')
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    grand = b_total + o_bal
    pdf.cell(150, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(40, 8, f"{b_total}", 1, 1, 'C')
    pdf.cell(150, 8, "Old Balance:", 0, 0, 'R'); pdf.cell(40, 8, f"{o_bal}", 1, 1, 'C')
    pdf.cell(150, 8, "Total Payable:", 0, 0, 'R'); pdf.cell(40, 8, f"{grand}", 1, 1, 'C')
    pdf.cell(150, 8, "Amount Paid:", 0, 0, 'R'); pdf.cell(40, 8, f"{paid}", 1, 1, 'C')
    pdf.set_text_color(255, 0, 0)
    pdf.cell(150, 8, "New Balance:", 0, 0, 'R'); pdf.cell(40, 8, f"{grand - paid}", 1, 1, 'C')
    
    return pdf.output()

# --- Navigation Tabs ---
tabs = st.tabs(["🛒 Make Bill", "👥 Customers & Ledger", "📊 Monthly Sales", "🔎 Search History"])

# --- TAB 1: BILLING ---
with tabs[0]:
    col1, col2 = st.columns([1, 2])
    with col1:
        st.write("### Step 1: Choose Customer")
        # Ensure latest list is loaded
        c_names = list(st.session_state.ledger.keys())
        selected_c = st.selectbox("Customer Name", c_names)
        old_b = st.session_state.ledger[selected_c]['balance']
        st.warning(f"Purana Udhaar: Rs. {old_b}")

    with col2:
        st.write("### Step 2: Add Items")
        item_n = st.text_input("Item Name")
        q_col, p_col = st.columns(2)
        item_q = q_col.number_input("Qty", min_value=1, value=1)
        item_p = p_col.number_input("Price", min_value=0, value=0)
        if st.button("Add Item to List"):
            if item_n:
                st.session_state.cart.append({"Item": item_n, "Qty": item_q, "Price": item_p, "Total": item_q * item_p})
                st.rerun()

    if st.session_state.cart:
        st.divider()
        st.table(pd.DataFrame(st.session_state.cart))
        bill_total = sum(i['Total'] for i in st.session_state.cart)
        st.write(f"#### Bill Total: Rs. {bill_total}")
        
        amt_paid = st.number_input("Amount Paid", min_value=0, value=0)
        
        if st.button("Finalize Bill & Save"):
            inv_id = f"INV-{datetime.now().strftime('%H%M%S')}"
            # Save to history
            for item in st.session_state.cart:
                d = item.copy()
                d.update({"BillID": inv_id, "Customer": selected_c, "Date": datetime.now().strftime("%Y-%m-%d")})
                st.session_state.all_sales.append(d)
            
            # Update Ledger
            new_balance = (bill_total + old_b) - amt_paid
            st.session_state.ledger[selected_c]['balance'] = float(new_balance)
            save_data()
            
            # PDF Generation
            pdf_file = get_bill_pdf(selected_c, st.session_state.cart, bill_total, old_b, amt_paid, inv_id)
            st.download_button("📥 Download PDF Bill", pdf_file, f"Bill_{selected_c}.pdf", "application/pdf")
            
            st.session_state.cart = []
            st.success("Data Saved Successfully!")

# --- TAB 2: CUSTOMERS (Add New Customer yahan se hoga) ---
with tabs[1]:
    st.subheader("Manage Customers")
    with st.form("new_customer"):
        new_name = st.text_input("Type New Customer Name")
        if st.form_submit_button("Save Customer"):
            if new_name and new_name not in st.session_state.ledger:
                st.session_state.ledger[new_name] = {"balance": 0.0}
                save_data()
                st.success(f"{new_name} added to list!")
                st.rerun()
            else:
                st.error("Invalid Name or Customer already exists!")

    st.divider()
    st.subheader("Full Ledger Record")
    l_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index()
    l_df.columns = ["Name", "Balance (Udhaar)"]
    st.dataframe(l_df, use_container_width=True)

# --- TAB 3: REPORT ---
with tabs[2]:
    if st.session_state.all_sales:
        rdf = pd.DataFrame(st.session_state.all_sales)
        rdf['Month'] = pd.to_datetime(rdf['Date']).dt.strftime('%B %Y')
        sel_m = st.selectbox("Select Month", rdf['Month'].unique())
        m_data = rdf[rdf['Month'] == sel_m]
        st.table(m_data.groupby('Item').agg({'Qty': 'sum', 'Total': 'sum'}).reset_index())

# --- TAB 4: SEARCH ---
with tabs[3]:
    if st.session_state.all_sales:
        sdf = pd.DataFrame(st.session_state.all_sales)
        srch = st.text_input("Search Customer Name")
        st.dataframe(sdf[sdf['Customer'].str.contains(srch, case=False)])
