import pandas as pd
import streamlit as st

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Full Kitting Dashboard", layout="wide")
st.title("📊 Full Kitting Dashboard")

# Manual refresh button
if st.button("🔄 Refresh PO List"):
    st.cache_data.clear()

# -------------------------------------------------
# GOOGLE SHEET CSV LINKS
# -------------------------------------------------
BASIC_DETAILS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSD682hMJJFbZ2jC_5h2yV07YBj4-sQGoyztdGZcjFFkOVTEnUR-OdWP0ukbDgJfF0lKGap7Vw4_-Td/pub?gid=0&single=true&output=csv"
RAW_MATERIALS_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSD682hMJJFbZ2jC_5h2yV07YBj4-sQGoyztdGZcjFFkOVTEnUR-OdWP0ukbDgJfF0lKGap7Vw4_-Td/pub?gid=246149847&single=true&output=csv"

# -------------------------------------------------
# LOAD DATA (AUTO REFRESH EVERY 60s)
# -------------------------------------------------
@st.cache_data(ttl=60)
def load_data():
    basic_df = pd.read_csv(BASIC_DETAILS_URL)
    raw_df = pd.read_csv(RAW_MATERIALS_URL)
    return basic_df, raw_df

basic, raw = load_data()

# -------------------------------------------------
# CLEAN COLUMN NAMES
# -------------------------------------------------
basic.columns = basic.columns.str.strip().str.upper().str.replace(" ", "_")
raw.columns = raw.columns.str.strip().str.upper().str.replace(" ", "_")

# -------------------------------------------------
# AUTO-DETECT COLUMNS
# -------------------------------------------------
def find_col(df, keywords):
    for col in df.columns:
        for key in keywords:
            if key in col:
                return col
    return None

PO_COL = find_col(basic, ["PO"])
COMPANY_COL = find_col(basic, ["COMPANY"])
PRODUCT_COL = find_col(basic, ["PRODUCT"])
PO_DATE_COL = find_col(basic, ["PO_DATE", "PO"])
DDD_COL = find_col(basic, ["DDD", "DELIVERY"])
FK_COL = find_col(basic, ["FULL", "KITTING"])

RAW_PO_COL = find_col(raw, ["PO"])

# -------------------------------------------------
# VALIDATION
# -------------------------------------------------
required = [PO_COL, COMPANY_COL, PRODUCT_COL, DDD_COL, FK_COL]
if any(col is None for col in required):
    st.error("❌ Required columns missing in Basic_Details sheet")
    st.stop()

# -------------------------------------------------
# PO DROPDOWN (NO FILTERING)
# -------------------------------------------------
basic["PO_PRODUCT"] = (
    basic[PO_COL].astype(str).str.strip() + "  —  " +
    basic[PRODUCT_COL].astype(str).str.strip()
)

po_selection = st.selectbox(
    "🔎 Select PO Number",
    options=[""] + basic["PO_PRODUCT"].tolist()
)

po_no = po_selection.split("—")[0].strip() if po_selection else ""

# -------------------------------------------------
# DASHBOARD LOGIC (UNCHANGED)
# -------------------------------------------------
if po_no:
    basic_po = basic[basic[PO_COL].astype(str).str.strip() == po_no]
    raw_po = raw[raw[RAW_PO_COL].astype(str).str.strip() == po_no]

    if basic_po.empty:
        st.error("❌ PO NOT FOUND")
        st.stop()

    row = basic_po.iloc[0]

    # -------------------------------------------------
    # READ VALUES FROM BASIC_DETAILS
    # -------------------------------------------------
    company = row[COMPANY_COL]
    product = row[PRODUCT_COL]

    po_date = pd.to_datetime(row[PO_DATE_COL], errors="coerce")
    po_date_display = po_date.strftime("%d-%m-%Y") if not pd.isna(po_date) else "NA"

    ddd = pd.to_datetime(row[DDD_COL], errors="coerce")
    ddd_display = ddd.strftime("%d-%m-%Y") if not pd.isna(ddd) else "NA"

    # -------------------------------------------------
    # FULL KITTING STATUS
    # -------------------------------------------------
    fk_raw = str(row[FK_COL]).strip().upper()
    full_kitting_status = "✅ DONE" if fk_raw in ["DONE", "COMPLETED", "YES", "✅ DONE", "1"] else "⏳ PENDING"

    # -------------------------------------------------
    # DASHBOARD CARDS
    # -------------------------------------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("Company Name", company)
    col2.metric("Product", product)
    col3.metric("PO Number", po_no)

    col4, col5, col6 = st.columns(3)
    col4.metric("PO Date", po_date_display)
    col5.metric("Delivery Due Date (DDD)", ddd_display)
    col6.metric("Full Kitting Status", full_kitting_status)

    # -------------------------------------------------
    # RAW MATERIAL VIEW
    # -------------------------------------------------
    st.subheader("📦 Raw Materials (PO-wise)")
    st.dataframe(raw_po, use_container_width=True)
