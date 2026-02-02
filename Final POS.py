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
        position: fixed; bottom: 10%; left: 5%;
        transform: rotate(-25deg);
        opacity: 0.05; font-size: 80px; color: gray;
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
    st.session_state.sales_history = pd.DataFrame(columns=["Bill No", "Date", "Customer", "Total", "Paid"])

# --- PDF Function ---
def create_pdf(bill_no, cust_name, phone, items, bill_total, old_bal, paid_amt):
    pdf = FPDF()
    pdf.add_page()
    # Watermark inside PDF (Bottom-Left to Top-Right)
    pdf.set_font("Arial", 'B', 40)
    pdf.set_text_color(245, 245, 245)
    pdf.text(20, 200, "ZEESHAN MOBILE ACCESSORIES")
    
    # Header (Bold Heading)
    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", 'B', 24) 
    pdf.cell(190, 15, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 8, "Contact: 03296971255", ln=True, align='C')
    pdf.ln(5)
    
    # Details
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(95, 8, f"Bill No: {bill_no}") # Bill Number
    pdf.cell(95, 8, f"Date: {pd.Timestamp.now().strftime('%d-%m-%Y')}", ln=True, align='R')
    pdf.cell(95, 8, f"Customer: {cust_name}")
    pdf.ln(10)
    
    # Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 10, " Item Name", 1, 0, 'L', True)
    pdf.cell(25, 10, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 10, "Price", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    # Rows
    pdf.set_font("Arial", '', 10)
    for item in items:
        pdf.cell(80, 10, f" {item['Item']}", 1)
        pdf.cell(25, 10, str(item['Qty']), 1, 0, 'C')
        pdf.cell(40, 10, str(item['Price']), 1, 0, 'C')
        pdf.cell(40, 10, str(item['Total']), 1, 1, 'C')
    
    # Summary
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(150, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(40, 8, f"{bill_total}", 1, 1, 'C')
    pdf.cell(150, 8, "Old Udhaar:", 0, 0, 'R'); pdf.cell(40, 8, f"{old_bal}", 1, 1, 'C')
    pdf.cell(150, 8, "Amount Paid:", 0, 0, 'R'); pdf.cell(40, 8, f"{paid_amt}", 1, 1, 'C')
    pdf.set_text_color(200, 0, 0)
    pdf.cell(150, 10, "New Balance:", 0, 0, 'R'); pdf.cell(40, 10, f"{(bill_total+old_bal)-paid_amt}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- Main App ---
st.markdown("### **ZEESHAN MOBILE ACCESSORIES**") # Bold Heading on Top
st.write("Contact: **03296971255**")

# Tabs for organization
tab_bill, tab_cust, tab_reports = st.tabs(["🛒 New Bill", "👤 Customers & Ledger", "📊 Sales Reports"])

with tab_bill:
    c_list = sorted(list(st.session_state.customer_db.keys()))
    sel_c = st.selectbox("Select Customer", c_list)
    cust_dat = st.session_state.customer_db[sel_c]
    st.info(f"Purana Udhaar: Rs. {cust_dat['balance']}")
    
    # Item entry
    col_a, col_b, col_c = st.columns([3,1,1])
    i_name = col_a.text_input("Item Name")
    i_qty = col_b.number_input("Qty", step=1, value=1)
    i_price = col_c.number_input("Price", 0)
    
    if st.button("Add Item"):
        if i_name:
            st.session_state.temp_items.append({"Item": i_name, "Qty": i_qty, "Price": i_price, "Total": i_qty*i_price})
    
    # Bill Display
    if st.session_state.temp_items:
        df_temp = pd.DataFrame(st.session_state.temp_items)
        st.table(df_temp)
        curr_total = df_temp['Total'].sum()
        st.write(f"**Total Bill: Rs. {curr_total}**")
        
        p_now = st.number_input("Amount Paid Now", 0.0)
        
        if st.button("✅ Save & Generate Bill"):
            b_no = f"ZMA-{int(time.time())}" # Unique Bill ID
            pdf_out = create_pdf(b_no, sel_c, cust_dat['phone'], st.session_state.temp_items, curr_total, cust_dat['balance'], p_now)
            
            # Save to History for Reports
            new_sale = pd.DataFrame([[b_no, pd.Timestamp.now(), sel_c, curr_total, p_now]], 
                                    columns=["Bill No", "Date", "Customer", "Total", "Paid"])
            st.session_state.sales_history = pd.concat([st.session_state.sales_history, new_sale], ignore_index=True)
            
            # Update Ledger
            st.session_state.customer_db[sel_c]['balance'] = (curr_total + cust_dat['balance']) - p_now
            
            st.download_button(f"📥 Download Bill {b_no}", pdf_out, f"Bill_{b_no}.pdf", "application/pdf")
            st.session_state.temp_items = []
            st.rerun()

with tab_cust:
    # Add Customer Section
    with st.expander("➕ Add New Customer"):
        n_name = st.text_input("Customer Name")
        n_phone = st.text_input("Phone Number")
        if st.button("Save Customer"):
            if n_name:
                st.session_state.customer_db[n_name] = {"phone": n_phone, "balance": 0.0}
                st.rerun()
    
    st.divider()
    # Search & Ledger Section
    st.subheader("🔍 Ledger Search")
    s_name = st.text_input("Type Name to Search")
    l_df = pd.DataFrame.from_dict(st.session_state.customer_db, orient='index').reset_index()
    l_df.columns = ["Name", "Phone", "Balance"]
    if s_name:
        l_df = l_df[l_df["Name"].str.contains(s_name, case=False)]
    st.dataframe(l_df, use_container_width=True)
    
    # Backup Button
    csv_backup = l_df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Backup Ledger (CSV)", csv_backup, "Zeeshan_Ledger_Backup.csv", "text/csv")

with tab_reports:
    st.header("📈 Sales Reports")
    hist = st.session_state.sales_history
    if not hist.empty:
        hist['Date'] = pd.to_datetime(hist['Date'])
        tday = pd.Timestamp.now().normalize()
        
        # Calculation for metrics
        d_sale = hist[hist['Date'] >= tday]['Total'].sum()
        w_sale = hist[hist['Date'] >= (tday - pd.Timedelta(days=7))]['Total'].sum()
        m_sale = hist[hist['Date'] >= (tday - pd.Timedelta(days=30))]['Total'].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Today's Sale", f"Rs. {d_sale}")
        m2.metric("Weekly Sale", f"Rs. {w_sale}")
        m3.metric("Monthly Sale", f"Rs. {m_sale}")
        
        st.write("### Transaction History")
        st.dataframe(hist.sort_values(by="Date", ascending=False))
    else:
        st.info("No sales data available yet.")
