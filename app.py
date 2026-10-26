import streamlit as st
import pandas as pd

SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

# Dedicated CSV export URLs for each sheet tab
SALES_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sales"
EXPENSES_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Expenses"
ADVANCES_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Staff%20Advances"

@st.cache_data(ttl=1)
def load_sales_data():
    return pd.read_csv(SALES_CSV_URL)

@st.cache_data(ttl=1)
def load_expenses_data():
    return pd.read_csv(EXPENSES_CSV_URL)

@st.cache_data(ttl=1)
def load_advances_data():
    return pd.read_csv(ADVANCES_CSV_URL)
