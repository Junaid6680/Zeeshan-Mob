import streamlit as st
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import os

# Page Settings
st.set_page_config(page_title="Zeeshan Mobile", layout="wide")

# Database Files (For Backup)
SALES_FILE = "sales_record.csv"

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
    st.session_state.db = {} 
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'history' not in st.session_state:
    if os.path.exists(SALES_FILE):
        st.session_state.history = pd.read_csv(SALES_FILE).to_dict('records')
    else:
        st.session_state.history = []

st.title("📱 Zeeshan Mobile Accessories")
st.write("Contact: 03296971255")

# Tabs (Added 2 extra tabs for Search and Monthly Report)
tab1, tab2, tab3, tab4 = st.tabs(["🆕 New Bill", "🔍 Search & History", "📊 Monthly Report", "📒 Ledger & Backup"])

with tab1:
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        name = st.text_input("Customer Name")
    with c_col2:
        old_bal = st.session_state.db.get(name, 0.0)
        st.warning(f"Previous Balance: Rs. {old_bal}")

    st.divider()

    i_col1, i_col2, i_col3 = st.columns([3,1,1])
    item = i_col1.text_input("Item Name")
    qty = i_col2.number_input("Qty", min_value=1)
    price = i_col3.number_input("Price", min_value=0)

    if st.button("Add Item"):
        st.session_state.cart.append({"Item": item, "Qty": qty, "Price": price, "Total": qty*price, "Date": datetime.now().strftime('%Y-%m-%d')})

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
            inv_id = f"ZM-{datetime.now().strftime('%H%M%S')}"
            # 1. Update Ledger
            st.session_state.db[name] = rem_bal
            
            # 2. Update History (For Monthly Report & Search)
            for cart_item in st.session_state.cart:
                new_entry = cart_item.copy()
                new_entry.update({"Customer": name, "BillID": inv_id})
                st.session_state.history.append(new_entry)
            
            # Save to CSV for Backup
            pd.DataFrame(st.session_state.history).to_csv(SALES_FILE, index=False)
            
            # PDF logic
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
            pdf.set_font("Arial", '', 12)
            pdf.cell(190, 10, f"Customer: {name} | Bill ID: {inv_id} | Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
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

# Feature 1: Search Tab
with tab2:
    st.header("🔍 Search Past Bills")
    if st.session_state.history:
        search_df = pd.DataFrame(st.session_state.history)
        search_val = st.text_input("Enter Customer Name or Bill ID")
        if search_val:
            filtered_df = search_df[search_df['Customer'].str.contains(search_val, case=False) | search_df['BillID'].str.contains(search_val, case=False)]
            st.dataframe(filtered_df)
        else:
            st.dataframe(search_df.tail(10)) # Show last 10 entries
    else:
        st.info("No sales history yet.")

# Feature 2: Monthly Report Tab
with tab3:
    st.header("📊 Monthly Sale Report")
    if st.session_state.history:
        report_df = pd.DataFrame(st.session_state.history)
        report_df['Month'] = pd.to_datetime(report_df['Date']).dt.strftime('%B %Y')
        selected_month = st.selectbox("Select Month", report_df['Month'].unique())
        
        monthly_data = report_df[report_df['Month'] == selected_month]
        item_summary = monthly_data.groupby('Item').agg({'Qty': 'sum', 'Total': 'sum'}).reset_index()
        st.table(item_summary)
        st.metric("Total Monthly Revenue", f"Rs. {item_summary['Total'].sum()}")

# Feature 3: Ledger & Backup Tab
with tab4:
    st.header("📒 Customer Balances")
    if st.session_state.db:
        st.json(st.session_state.db)
        
        st.divider()
        st.subheader("📥 Download Backup")
        # Backup CSV
        csv_backup = pd.DataFrame(st.session_state.history).to_csv(index=False).encode('utf-8')
        st.download_button("Download All Sales Record (CSV)", csv_backup, "zeeshan_mobile_backup.csv", "text/csv")
    else:
        st.write("No records found.")
