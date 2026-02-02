import streamlit as st
import pandas as pd
from fpdf import FPDF
import time

# --- Page Config ---
st.set_page_config(page_title="Zeeshan Mobile POS", layout="wide")

# --- CSS for Watermark (Bottom-Left to Top-Right) ---
st.markdown("""
    <style>
    .watermark {
        position: fixed; bottom: 10%; left: 10%;
        transform: rotate(-30deg);
        opacity: 0.07; font-size: 80px; color: gray;
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
if 'sales_history' not in st.session_state:
    st.session_state.sales_history = pd.DataFrame(columns=["Bill No", "Date", "Customer", "Total Amount", "Paid"])

# --- PDF Function ---
def create_pdf(bill_no, cust_name, phone, items, bill_total, old_bal, paid_amt):
    pdf = FPDF()
    pdf.add_page()
    # Watermark in PDF
    pdf.set_font("Arial", 'B', 40)
    pdf.set_text_color(240, 240, 240)
    pdf.text(30, 200, "ZEESHAN MOBILE ACCESSORIES")
    
    # Header
    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", 'B', 24) # Bold & Larger Heading
    pdf.cell(190, 12, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, "Contact: 03296971255", ln=True, align='C')
    pdf.ln(5)
    
    # Bill Info
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 8, f"Bill No: {bill_no}") # Bill Number added
    pdf.cell(95, 8, f"Date: {pd.Timestamp.now().strftime('%d-%m-%Y %H:%M')}", ln=True, align='R')
    pdf.cell(95, 8, f"Customer: {cust_name}")
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 10, " Item Description", 1, 0, 'L', True)
    pdf.cell(25, 10, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 10, "Price", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    pdf.set_font("Arial", '', 10)
    for item in items:
        pdf.cell(80, 10, f" {item['Item']}", 1)
        pdf.cell(25, 10, str(item['Qty']), 1, 0, 'C')
        pdf.cell(40, 10, str(item['Price']), 1, 0, 'C')
        pdf.cell(40, 10, str(item['Total']), 1, 1, 'C')
    
    # Calculation
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(150, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(40, 8, f"{bill_total}", 1, 1, 'C')
    pdf.cell(150, 8, "Paid Amount:", 0, 0, 'R'); pdf.cell(40, 8, f"{paid_amt}", 1, 1, 'C')
    pdf.set_text_color(200, 0, 0)
    pdf.cell(150, 10, "Total Balance:", 0, 0, 'R'); pdf.cell(40, 10, f"{(bill_total+old_bal)-paid_amt}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- Main UI ---
st.markdown("# **ZEESHAN MOBILE ACCESSORIES**") # Bold Heading
st.write("Contact: **03296971255**")

tab1, tab2, tab3 = st.tabs(["🛒 Billing", "👤 Customers", "📊 Sales Reports"])

with tab1:
    cust_list = sorted(list(st.session_state.customer_db.keys()))
    sel_cust = st.selectbox("Select Customer", cust_list)
    c_data = st.session_state.customer_db[sel_cust]
    st.info(f"Udhaar: Rs. {c_data['balance']}")
    
    col1, col2, col3 = st.columns([3,1,1])
    it_n = col1.text_input("Item")
    it_q = col2.number_input("Qty", step=1, value=1)
    it_p = col3.number_input("Price", 0)
    
    if st.button("Add Item"):
        if it_n:
            st.session_state.temp_items.append({"Item": it_n, "Qty": it_q, "Price": it_p, "Total": it_q*it_p})
    
    if st.session_state.temp_items:
        df = pd.DataFrame(st.session_state.temp_items)
        st.table(df)
        b_total = df['Total'].sum()
        amt_paid = st.number_input("Amount Paid", 0.0)
        
        if st.button("Finalize Bill"):
            bill_id = f"ZMA-{int(time.time())}" # Unique Bill No
            pdf_b = create_pdf(bill_id, sel_cust, c_data['phone'], st.session_state.temp_items, b_total, c_data['balance'], amt_paid)
            
            # Save to History
            new_sale = pd.DataFrame([[bill_id, pd.Timestamp.now(), sel_cust, b_total, amt_paid]], 
                                    columns=["Bill No", "Date", "Customer", "Total Amount", "Paid"])
            st.session_state.sales_history = pd.concat([st.session_state.sales_history, new_sale], ignore_index=True)
            
            # Update Ledger
            st.session_state.customer_db[sel_cust]['balance'] = (b_total + c_data['balance']) - amt_paid
            
            st.download_button(f"📥 Print Bill {bill_id}", pdf_b, f"Bill_{bill_id}.pdf", "application/pdf")
            st.session_state.temp_items = []
            st.rerun()

with tab2:
    with st.expander("Add New Customer"):
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        if st.button("Save"):
            st.session_state.customer_db[name] = {"phone": phone, "balance": 0.0}
            st.rerun()
    st.dataframe(pd.DataFrame.from_dict(st.session_state.customer_db, orient='index'))

with tab3:
    st.header("📈 Sales Analysis")
    history = st.session_state.sales_history
    if not history.empty:
        history['Date'] = pd.to_datetime(history['Date'])
        
        # Search by Bill No
        search_bill = st.text_input("🔍 Search by Bill Number")
        if search_bill:
            st.dataframe(history[history['Bill No'].str.contains(search_bill, case=False)])
        
        # Reports
        today = pd.Timestamp.now().normalize()
        daily = history[history['Date'] >= today]['Total Amount'].sum()
        weekly = history[history['Date'] >= (today - pd.Timedelta(days=7))]['Total Amount'].sum()
        monthly = history[history['Date'] >= (today - pd.Timedelta(days=30))]['Total Amount'].sum()
        yearly = history[history['Date'] >= (today - pd.Timedelta(days=365))]['Total Amount'].sum()
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Today Sale", f"Rs. {daily}")
        c2.metric("Weekly Sale", f"Rs. {weekly}")
        c3.metric("Monthly Sale", f"Rs. {monthly}")
        c4.metric("Yearly Sale", f"Rs. {yearly}")
        
        st.write("### All Transactions History")
        st.dataframe(history)
    else:
        st.warning("No sales recorded yet.")
