import streamlit as st
import pandas as pd
import math
from io import BytesIO

# --- PAGE SETUP ---
st.set_page_config(
    page_title="ALPINE HERBS | Client 360° Master Dashboard",
    page_icon="🌿",
    layout="wide"
)

# PUT YOUR ACTIVE SHEET ID HERE
SHEET_ID = "1cpPYFS9EkajB5tGfMnReIJ71cmB5djz6oaMvvEoqs6A"

# --- BRANDING & STYLING ---
st.markdown("""<style>
#MainMenu, footer { visibility: hidden; }
.block-container { 
    padding-top: 1.8rem !important; 
    padding-bottom: 2.5rem !important; 
    max-width: 1560px; 
}
.main-header {
    background: linear-gradient(135deg, #0D2818 0%, #164E33 100%);
    padding: 16px 22px;
    border-radius: 8px;
    color: white;
    margin-bottom: 1.2rem;
    box-shadow: 0 4px 12px rgba(13, 40, 24, 0.08);
}
.client-hero {
    background: #F4FAF6;
    border: 1px solid #B0D4BE;
    border-left: 5px solid #164E33;
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 1.2rem;
}
.kpi-card {
    background: #FFFFFF;
    border: 1px solid #C8DCCF;
    border-top: 3.5px solid #164E33;
    border-radius: 8px;
    padding: 12px 14px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.02);
}
.kpi-title { 
    font-size: 0.75rem; 
    font-weight: 700; 
    color: #4A6354; 
    text-transform: uppercase; 
    margin-bottom: 3px; 
}
.kpi-value { 
    font-size: 1.35rem; 
    font-weight: 800; 
    color: #0D2818; 
}
.kpi-sub { 
    font-size: 0.72rem; 
    color: #738C7D; 
    margin-top: 2px; 
}
</style>""", unsafe_allow_html=True)

# --- MASTER CLIENT LEDGER (BARA & PARSA WITH OPENING DUES) ---
MASTER_CLIENTS = [
    # BARA DISTRICT
    {"name": "Naresh Medical", "code": "BAR-001", "area": "Kalaiya", "district": "Bara", "phone": "9807267001", "dues": 3100},
    {"name": "Mahir Health Clinic", "code": "BAR-002", "area": "Jeetpur", "district": "Bara", "phone": "9807100296", "dues": 8165},
    {"name": "Dev Medical", "code": "BAR-003", "area": "Kalaiya", "district": "Bara", "phone": "9845227985", "dues": 1500},
    {"name": "Nirajan Pharmacy", "code": "BAR-004", "area": "Bakuliya", "district": "Bara", "phone": "9804242586", "dues": 550},
    {"name": "Hariom Medical", "code": "BAR-005", "area": "Kolvi", "district": "Bara", "phone": "9811229323", "dues": 2300},
    {"name": "S.K.S Pharma", "code": "BAR-006", "area": "Parsauni", "district": "Bara", "phone": "", "dues": 1175},
    {"name": "Aayan First Aid Center", "code": "BAR-007", "area": "Simara", "district": "Bara", "phone": "", "dues": 2060},
    {"name": "Rupa Medical Hall", "code": "BAR-008", "area": "Simara", "district": "Bara", "phone": "", "dues": 5515},
    {"name": "Sanjeevani Clinic", "code": "BAR-009", "area": "Simara", "district": "Bara", "phone": "9845130209", "dues": 2195},
    {"name": "Ale Health Clinic", "code": "BAR-010", "area": "Ganj Bhawanipur", "district": "Bara", "phone": "", "dues": 1645},
    {"name": "Alex Medical Hall", "code": "BAR-011", "area": "Bagrampur", "district": "Bara", "phone": "", "dues": 18000},
    {"name": "Kaliyani Medical Hall", "code": "BAR-012", "area": "Kolvi", "district": "Bara", "phone": "", "dues": 15580},
    {"name": "Shohalal Medical Hall", "code": "BAR-013", "area": "Ganj Bhawanipur", "district": "Bara", "phone": "9814286651", "dues": 7175},
    {"name": "Everest Health Clinic", "code": "BAR-014", "area": "Kalaiya", "district": "Bara", "phone": "", "dues": 2635},
    {"name": "Roman Surgical", "code": "BAR-015", "area": "Khopawa", "district": "Bara", "phone": "9821231370", "dues": 1660},
    {"name": "Nimash Medical", "code": "BAR-016", "area": "Simara", "district": "Bara", "phone": "9845120836", "dues": 4620},
    {"name": "Advance Poli Clinic", "code": "BAR-017", "area": "Raghunathpur", "district": "Bara", "phone": "9809153231", "dues": 4310},
    {"name": "Prithvi Medical Hall", "code": "BAR-018", "area": "Jaitapur", "district": "Bara", "phone": "", "dues": 6745},
    {"name": "Safe Life Hospital", "code": "BAR-019", "area": "Benauli", "district": "Bara", "phone": "", "dues": 740},
    {"name": "Alina Health Clinic", "code": "BAR-020", "area": "Kalaiya", "district": "Bara", "phone": "", "dues": 8250},
    {"name": "Hargendra Pande Medical", "code": "BAR-021", "area": "Rautahar", "district": "Bara", "phone": "", "dues": 500},
    {"name": "Jungbahadur Medical", "code": "BAR-022", "area": "Bagrampur", "district": "Bara", "phone": "", "dues": 200},
    {"name": "Aarabh Pharmacy", "code": "BAR-023", "area": "Nijgadh", "district": "Bara", "phone": "9855019764", "dues": 36725},
    {"name": "Aarabh Pharmacy (Narayani)", "code": "BAR-024", "area": "Nijgadh", "district": "Bara", "phone": "9855019764", "dues": 25915},
    {"name": "Sanniya Medical Hall", "code": "BAR-025", "area": "Jeetpur", "district": "Bara", "phone": "", "dues": 3460},
    {"name": "Bala Ji Medical Hall", "code": "BAR-026", "area": "Aarnawa Chouk", "district": "Bara", "phone": "", "dues": 3195},
    {"name": "Sapna Health Clinic", "code": "BAR-027", "area": "Bariyarpur", "district": "Bara", "phone": "", "dues": 1365},
    {"name": "Gudi Pharmacy", "code": "BAR-028", "area": "Bariyarpur", "district": "Bara", "phone": "", "dues": 0},
    {"name": "OM Shivsakti Pharmacy", "code": "BAR-029", "area": "Kalaiya", "district": "Bara", "phone": "", "dues": 3680},

    # PARSA DISTRICT
    {"name": "Aditi Pharmacy", "code": "PAR-001", "area": "Manwa Bazar", "district": "Parsa", "phone": "", "dues": 500},
    {"name": "Ashok Medical Hall", "code": "PAR-002", "area": "Naukatola", "district": "Parsa", "phone": "", "dues": 12230},
    {"name": "Sudama Surgical", "code": "PAR-003", "area": "Neutan", "district": "Parsa", "phone": "", "dues": 20200},
    {"name": "B.S Health Clinic", "code": "PAR-004", "area": "Paterwa", "district": "Parsa", "phone": "", "dues": 24665},
    {"name": "Pandey Medical Hall", "code": "PAR-005", "area": "Badanihar", "district": "Parsa", "phone": "", "dues": 7065},
    {"name": "Bhawani Medical Hall", "code": "PAR-006", "area": "Bharatwa", "district": "Parsa", "phone": "", "dues": 9950},
    {"name": "Chandip Medical Hall", "code": "PAR-007", "area": "Kathmandu Tol", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Dinamik Pharma", "code": "PAR-008", "area": "Sano Sugauli", "district": "Parsa", "phone": "", "dues": 15815},
    {"name": "Everest Pharmacy", "code": "PAR-009", "area": "Birwa Chouk", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Fatepur Health Clinic", "code": "PAR-010", "area": "Fatepur", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Gadi Mai Medical Hall", "code": "PAR-011", "area": "Pachgawa", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Ganesh Srestha", "code": "PAR-012", "area": "Birgunj", "district": "Parsa", "phone": "", "dues": 63390},
    {"name": "Harnaiya Aashirvad Medical", "code": "PAR-013", "area": "Harnaiya", "district": "Parsa", "phone": "", "dues": 4565},
    {"name": "Madhav Medical Hall", "code": "PAR-014", "area": "Pachgawa", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Nawal Kishor Medical Hall", "code": "PAR-015", "area": "Pachgawa", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Nausad Medical Hall", "code": "PAR-016", "area": "Rangapur", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Kohinoor Medical Hall", "code": "PAR-017", "area": "Milan Chouk", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Sibil Medical Hall", "code": "PAR-018", "area": "Milan Chouk", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Noor Tamana Health Clinic", "code": "PAR-019", "area": "Derbana", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Aftab Medical Hall", "code": "PAR-020", "area": "Derbana", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Pandey Medical Hall (Murli)", "code": "PAR-021", "area": "Murli", "district": "Parsa", "phone": "", "dues": 700},
    {"name": "Puja Medical Hall", "code": "PAR-022", "area": "Fatepur", "district": "Parsa", "phone": "", "dues": 1030},
    {"name": "Raina Health Clinic", "code": "PAR-023", "area": "Veda Tol", "district": "Parsa", "phone": "", "dues": 3672},
    {"name": "Rihansh Medical Hall", "code": "PAR-024", "area": "Birgunj", "district": "Parsa", "phone": "", "dues": 1740},
    {"name": "Roshan Pharmacy", "code": "PAR-025", "area": "Birgunj", "district": "Parsa", "phone": "", "dues": 74290},
    {"name": "Samir Medical Hall", "code": "PAR-026", "area": "Pachgawa", "district": "Parsa", "phone": "", "dues": 0},
    {"name": "Sandip Medical Hall", "code": "PAR-027", "area": "Langada Chouk", "district": "Parsa", "phone": "",
