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

# --- Data Loading ---
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

# --- PDF Function (Fixed Error) ---
def create_pdf(name, items, b_total, o_bal, paid, inv_id):
    pdf = FPDF()
    pdf.add_page()
    
    # Watermark
    pdf.set_font("Arial", 'B', 45)
    pdf.set_text_color(240, 240, 240)
    pdf.text(35, 150, "ZEESHAN MOBILE")
    
    # Header
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=1, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(190, 7, "Contact: 03296971255", ln=1, align='C')
    pdf.cell(190, 7, f"Bill ID: {inv_id} | Date: {datetime.now().strftime('%d-%m-%Y')}", ln=1, align='C')
    pdf.ln(10)
    
    # Customer Name
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, f"Customer: {name}", ln=1)
    
    # Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(85, 8, " Item Name", 1, 0, 'L', True)
    pdf.cell(20, 8, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 8, "Price", 1, 0, 'C', True)
    pdf.cell(45, 8, "Total", 1, 1, 'C', True)
    
    # Table Content
    pdf.set_font("Arial", '', 11)
    for i in items:
        pdf.cell(85, 8, f" {i['Item']}", 1)
        pdf.cell(20, 8, str(i['Qty']), 1, 0, 'C')
        pdf.cell(40, 8, str(i['Price']), 1, 0, 'C')
        pdf.cell(45, 8, str(i['Total']), 1, 1, 'C')
    
    # Calculations
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    grand_total = b_total + o_bal
    pdf.cell(145, 8, "Current Bill Total:", 0, 0, 'R'); pdf.cell(45, 8, f"{b_total}", 1, 1, 'C')
    pdf.cell(145, 8, "Old Balance:", 0, 0, 'R'); pdf.cell(45, 8, f"{o_bal}", 1, 1, 'C')
    pdf.cell(145, 8, "Grand Total:", 0, 0, 'R'); pdf.cell(45, 8, f"{grand_total}", 1, 1, 'C')
    pdf.cell(145, 8, "Amount Paid:", 0, 0, 'R'); pdf.cell(45, 8, f"{paid}", 1, 1, 'C')
    
    pdf.set_text_color(200, 0, 0)
    pdf.cell(145, 8, "Remaining Balance:", 0, 0, 'R'); pdf.cell(45, 8, f"{grand_total - paid}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- Main App ---
st.title("📱 Zeeshan Mobile Accessories")
st.write(f"📞 **Contact:** 03296971255")

# Tabs
tab1, tab2, tab3 = st.tabs(["🆕 New Bill", "📒 Customers & Ledger", "🔍 Sales History"])

# --- TAB 1: BILLING ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Customer Info")
        c_names = list(st.session_state.ledger.keys())
        selected_c = st.selectbox("Select Customer", c_names)
        old_bal = st.session_state.ledger[selected_c]['balance']
        st.info(f"Purana Udhaar: Rs. {old_bal}")
        
    with c2:
        st.subheader("Add Items")
        it_name = st.text_input("Item Name")
        q_col, p_col = st.columns(2)
        it_qty = q_col.number_input("Quantity", min_value=1, value=1)
        it_prc = p_col.number_input("Price", min_value=0, value=0)
        if st.button("➕ Add to List"):
            if it_name:
                st.session_state.cart.append({"Item": it_name, "Qty": it_qty, "Price": it_prc, "Total": it_qty * it_prc})
                st.rerun()

    if st.session_state.cart:
        st.divider()
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        
        bill_total = df_cart['Total'].sum()
        st.write(f"### Current Bill: Rs. {bill_total}")
        
        amt_paid = st.number_input("Amount Paid Now", min_value=0, value=0)
        
        if st.button("💾 Save & Generate Bill"):
            inv_id = f"Z-{datetime.now().strftime('%H%M%S')}"
            
            # Save History
            for item in st.session_state.cart:
                entry = item.copy()
                entry.update({"BillID": inv_id, "Customer": selected_c, "Date": datetime.now().strftime("%Y-%m-%d")})
                st.session_state.all_sales.append(entry)
            
            # Update Ledger
            new_bal = (bill_total + old_bal) - amt_paid
            st.session_state.ledger[selected_c]['balance'] = float(new_bal)
            save_data()
            
            # Generate PDF data
            pdf_data = create_pdf(selected_c, st.session_state.cart, bill_total, old_bal, amt_paid, inv_id)
            st.download_button("📥 Download PDF Bill", data=pdf_data, file_name=f"Bill_{selected_c}.pdf", mime="application/pdf")
            
            st.session_state.cart = []
            st.success("Record Saved Successfully!")

# --- TAB 2: CUSTOMER MANAGEMENT ---
with tab2:
    st.subheader("Add New Customer")
    with st.form("new_customer_form"):
        new_name = st.text_input("Customer Name")
        if st.form_submit_button("Save Customer"):
            if new_name and new_name not in st.session_state.ledger:
                st.session_state.ledger[new_name] = {"balance": 0.0}
                save_data()
                st.success(f"{new_name} has been added!")
                st.rerun()
            else:
                st.error("Name invalid or already exists.")

    st.divider()
    st.subheader("Current Udhaar Record")
    ledger_df = pd.DataFrame.from_dict(st.session_state.ledger, orient='index').reset_index()
    ledger_df.columns = ["Name", "Balance (Udhaar)"]
    st.dataframe(ledger_df, use_container_width=True)

# --- TAB 3: SEARCH ---
with tab3:
    st.subheader("Search Sales History")
    if st.session_state.all_sales:
        history_df = pd.DataFrame(st.session_state.all_sales)
        search = st.text_input("Type Name to Search")
        if search:
            st.dataframe(history_df[history_df['Customer'].str.contains(search, case=False)])
        else:
            st.dataframe(history_df)
