import streamlit as st
import pandas as pd
from fpdf import FPDF

# --- Page Config ---
st.set_page_config(page_title="Zeeshan Mobile POS", layout="wide")

# --- Background Watermark Style ---
st.markdown("""
    <style>
    .watermark {
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-45deg);
        opacity: 0.05; font-size: 70px; color: gray;
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

# --- PDF Function (With Watermark & Your Contact) ---
def create_pdf(cust_name, phone, items, bill_total, old_bal, paid_amt):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. PDF Watermark
    pdf.set_font("Arial", 'B', 50)
    pdf.set_text_color(240, 240, 240)
    pdf.text(35, 150, "ZEESHAN MOBILE")
    
    # Header
    pdf.set_text_color(0, 51, 102)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(190, 10, "ZEESHAN MOBILE ACCESSORIES", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(190, 7, "Contact: 03296971255", ln=True, align='C')
    pdf.ln(10)
    
    # Info
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(95, 8, f"Customer: {cust_name}")
    pdf.cell(95, 8, f"Date: {pd.Timestamp.now().strftime('%d-%b-%Y')}", ln=True, align='R')
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(80, 10, " Item Description", 1, 0, 'L', True)
    pdf.cell(25, 10, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 10, "Price", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    # Table Rows
    pdf.set_font("Arial", '', 10)
    for item in items:
        pdf.cell(80, 10, f" {item['Item']}", 1)
        pdf.cell(25, 10, str(item['Qty']), 1, 0, 'C')
        pdf.cell(40, 10, str(item['Price']), 1, 0, 'C')
        pdf.cell(40, 10, str(item['Total']), 1, 1, 'C')
    
    # Totals
    new_bal = (bill_total + old_bal) - paid_amt
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(150, 8, "Current Bill:", 0, 0, 'R'); pdf.cell(40, 8, f"{bill_total}", 1, 1, 'C')
    pdf.cell(150, 8, "Old Udhaar:", 0, 0, 'R'); pdf.cell(40, 8, f"{old_bal}", 1, 1, 'C')
    pdf.cell(150, 8, "Amount Paid:", 0, 0, 'R'); pdf.cell(40, 8, f"{paid_amt}", 1, 1, 'C')
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(200, 0, 0)
    pdf.cell(150, 10, "Remaining Balance:", 0, 0, 'R'); pdf.cell(40, 10, f"{new_bal}", 1, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- MAIN UI ---
st.title("📱 Zeeshan Mobile Accessories")
st.write("Contact: **03296971255**")

# --- 1. Customer Section ---
st.header("👤 Customer Management")
col_c1, col_c2 = st.columns(2)

with col_c1:
    customer_list = sorted(list(st.session_state.customer_db.keys()))
    selected_cust = st.selectbox("Select Customer for Billing", customer_list)
    cust_data = st.session_state.customer_db[selected_cust]
    st.write(f"📌 **Current Udhaar: Rs. {cust_data['balance']}**")

with col_c2:
    with st.expander("➕ Add New Customer"):
        new_n = st.text_input("Customer Name")
        new_p = st.text_input("Phone Number")
        new_b = st.number_input("Opening Udhaar", 0.0)
        if st.button("Save New Customer"):
            if new_n:
                st.session_state.customer_db[new_n] = {"phone": new_p, "balance": new_b}
                st.rerun()

st.divider()

# --- 2. Billing Section ---
st.header("📦 New Bill & Returns")
st.info("Tip: Item wapsi ke liye Qty ko minus (-1) likhein.")

col_i1, col_i2, col_i3 = st.columns([3,1,1])
item_name = col_i1.text_input("Item Name")
item_qty = col_i2.number_input("Qty", step=1, value=1)
item_price = col_i3.number_input("Price", 0)

if st.button("➕ Add Item to List"):
    if item_name:
        st.session_state.temp_items.append({"Item": item_name, "Qty": item_qty, "Price": item_price, "Total": item_qty * item_price})

if st.session_state.temp_items:
    df = pd.DataFrame(st.session_state.temp_items)
    st.table(df)
    bill_total = df['Total'].sum()
    st.subheader(f"Total Bill: Rs. {bill_total}")
    
    paid_now = st.number_input("Amount Paid Now", 0.0)
    
    if st.button("✅ Save & Generate Bill PDF"):
        old_bal = cust_data['balance']
        st.session_state.customer_db[selected_cust]['balance'] = (bill_total + old_bal) - paid_now
        
        pdf_out = create_pdf(selected_cust, cust_data['phone'], st.session_state.temp_items, bill_total, old_bal, paid_now)
        st.download_button("📥 Click Here to Download/Print Bill", pdf_out, f"Bill_{selected_cust}.pdf", "application/pdf")
        
        st.session_state.temp_items = []
        st.success("Record saved successfully!")

st.divider()

# --- 3. Ledger & Backup ---
st.header("📒 Ledger & Backup")
search = st.text_input("🔍 Search Customer")
ledger_df = pd.DataFrame.from_dict(st.session_state.customer_db, orient='index').reset_index()
ledger_df.columns = ["Name", "Phone", "Balance"]
if search:
    ledger_df = ledger_df[ledger_df["Name"].str.contains(search, case=False)]
st.dataframe(ledger_df, use_container_width=True)

csv_data = ledger_df.to_csv(index=False).encode('utf-8')
st.download_button("💾 Download All Data Backup (CSV)", csv_data, "Zeeshan_Mobile_Backup.csv", "text/csv")
