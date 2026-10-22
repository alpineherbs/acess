import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple

# =========================================================
# 1. TARIFF SCHEDULE & SETTINGS
# =========================================================
# Optional: Paste your free ScraperAPI key inside the quotes if you have one:
SCRAPER_API_KEY = "34f6af46dd2237d85972a508370b8ae3"

# Nepal Customs Standard Rates
EXCHANGE_RATE_INR_TO_NPR = 1.62   # Official peg 1.60 + ~1.25% bank/cross-border markup
FREIGHT_PER_KG_NPR = 550.0        # Courier rate per kg (India to Kathmandu)
INSURANCE_RATE = 0.01             # 1% standard cargo insurance
CLEARANCE_FEE_NPR = 350.0         # Customs broker & documentation fee

# Official Nepal Customs Tariff Schedule (HS Codes)
HS_DATABASE: Dict[str, Dict] = {
    "8471.30": {
        "description": "Laptops & Portable Computers",
        "customs": 0.01,
        "excise": 0.00,
        "vat": 0.13
    },
    "8517.13": {
        "description": "Smartphones / Mobile Handsets",
        "customs": 0.05,
        "excise": 0.00,
        "vat": 0.13
    },
    "8518.30": {
        "description": "Headphones / Earphones / TWS Earbuds",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13
    },
    "9102.12": {
        "description": "Smartwatches & Wristwatches",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13
    },
    "6109.10": {
        "description": "Clothing / T-shirts / Garments",
        "customs": 0.20,
        "excise": 0.00,
        "vat": 0.13
    },
    "6404.11": {
        "description": "Footwear / Sports Shoes / Sneakers",
        "customs": 0.20,
        "excise": 0.00,
        "vat": 0.13
    },
    "3304.99": {
        "description": "Cosmetics / Skincare / Creams / Serums",
        "customs": 0.15,
        "excise": 0.05,
        "vat": 0.13
    },
    "4901.99": {
        "description": "Printed Books & Educational Literature",
        "customs": 0.00,
        "excise": 0.00,
        "vat": 0.00
    },
    "8528.72": {
        "description": "Televisions & Display Monitors",
        "customs": 0.20,
        "excise": 0.05,
        "vat": 0.13
    },
    "9999.99": {
        "description": "General Merchandise / Miscellaneous",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13
    }
}

# =========================================================
# 2. LOGIC FUNCTIONS
# =========================================================
def auto_detect_hs_code(title: str) -> str:
    """Matches product title to the closest Nepal Customs HS Code."""
    t = title.lower()
    if any(k in t for k in ["laptop", "macbook", "thinkpad", "notebook", "chromebook"]):
        return "8471.30"
    if any(k in t for k in ["iphone", "smartphone", "galaxy", "redmi", "oneplus", "realme", "phone"]):
        return "8517.13"
    if any(k in t for k in ["headphone", "earphone", "airpods", "buds", "earbuds", "headset"]):
        return "8518.30"
    if any(k in t for k in ["smartwatch", "watch", "smart band", "fitness band"]):
        return "9102.12"
    if any(k in t for k in ["shirt", "t-shirt", "pant", "trousers", "hoodie", "dress", "jacket", "jeans"]):
        return "6109.10"
    if any(k in t for k in ["shoe", "sneaker", "sandal", "boots", "crocs", "loafers"]):
        return "6404.11"
    if any(k in t for k in ["serum", "lotion", "cream", "lipstick", "perfume", "shampoo", "sunscreen"]):
        return "3304.99"
    if any(k in t for k in ["book", "novel", "paperback", "hardcover"]):
        return "4901.99"
    if any(k in t for k in ["tv", "television", "monitor"]):
        return "8528.72"
    return "9999.99"


def scrape_indian_url(url: str) -> Tuple[str, float]:
    """Scrapes product title and INR price safely."""
    title = ""
    price = 0.0

    try:
        if SCRAPER_API_KEY and len(SCRAPER_API_KEY) > 10:
            target_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
            headers = {}
        else:
            target_url = url
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9"
            }

        resp = requests.get(target_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")

            # Amazon Selectors
            t_tag = soup.find("span", {"id": "productTitle"})
            if t_tag:
                title = t_tag.get_text(strip=True)

            p_tag = soup.find("span", {"class": "a-price-whole"})
            if p_tag:
                clean_p = re.sub(r"[^\d.]", "", p_tag.get_text())
                if clean_p:
                    price = float(clean_p)

            # Flipkart Selectors (Fallback)
            if not title:
                f_title = soup.find("span", {"class": "B_NuCI"}) or soup.find("h1", {"class": "VU-ZEz"})
                if f_title:
                    title = f_title.get_text(strip=True)

            if price == 0.0:
                f_price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj CxhGGd"})
                if f_price:
                    clean_p = re.sub(r"[^\d.]", "", f_price.get_text())
                    if clean_p:
                        price = float(clean_p)
    except Exception:
        pass

    return title, price


# =========================================================
# 3. STREAMLIT USER INTERFACE
# =========================================================
st.set_page_config(page_title="Indo-Nepal Import Cost Agent", page_icon="🇳🇵", layout="wide")

st.title("🇳🇵 Indo-Nepal E-Commerce Import Agent")
st.markdown("Calculate the complete landed cost from **Amazon India, Flipkart & Myntra** to Nepal with **Customs Duties, Freight, and 13% VAT**.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Product & Shipping Details")
    mode = st.radio("Input Method:", ["Paste Product Link", "Enter Details Manually"], horizontal=True)

    default_title = "Puma Men's Running Shoes"
    default_price = 3499.0
    default_weight = 1.2

    if mode == "Paste Product Link":
        url_input = st.text_input("Paste Indian Product URL:", placeholder="https://www.amazon.in/dp/B0CX214GBN")
        if url_input:
            with st.spinner("Extracting product information..."):
                scraped_title, scraped_price = scrape_indian_url(url_input)
                if scraped_title:
                    default_title = scraped_title
                if scraped_price > 0:
                    default_price = scraped_price

                if scraped_title and scraped_price > 0:
                    st.success("✅ Extracted product details successfully!")
                else:
                    st.info("ℹ️ Enter the name and price below to calculate.")

    # Form inputs
    prod_name = st.text_input("Product Title / Name:", value=default_title)
    price_inr = st.number_input("Price in India (₹ INR):", min_value=1.0, value=float(default_price), step=100.0)

    col_w, col_l, col_wi, col_h = st.columns(4)
    with col_w:
        weight_kg = st.number_input("Weight (kg):", min_value=0.1, value=float(default_weight), step=0.1)
    with col_l:
        dim_l = st.number_input("Length (cm):", value=25.0, step=5.0)
    with col_wi:
        dim_w = st.number_input("Width (cm):", value=15.0, step=5.0)
    with col_h:
        dim_h = st.number_input("Height (cm):", value=10.0, step=5.0)

    st.subheader("2. Customs Classification")
    detected_hs = auto_detect_hs_code(prod_name)
    all_hs = list(HS_DATABASE.keys())
    selected_hs = st.selectbox(
        "Nepal Customs HS Code:",
        options=all_hs,
        index=all_hs.index(detected_hs),
        format_func=lambda x: f"HS {x} — {HS_DATABASE[x]['description']} (Duty: {int(HS_DATABASE[x]['customs']*100)}%)"
    )

with col_right:
    st.subheader("3. Cost & Customs Breakdown")

    # 1. Chargeable Weight (Actual vs Volumetric)
    volumetric_weight = (dim_l * dim_w * dim_h) / 5000.0 if (dim_l > 0 and dim_w > 0 and dim_h > 0) else 0.0
    chargeable_weight = max(weight_kg, volumetric_weight, 0.5)

    # 2. Base Conversion (INR to NPR)
    price_npr = price_inr * EXCHANGE_RATE_INR_TO_NPR

    # 3. Freight & Cargo Insurance
    freight_npr = chargeable_weight * FREIGHT_PER_KG_NPR
    insurance_npr = price_npr * INSURANCE_RATE

    # 4. Assessable CIF Value (Cost + Insurance + Freight)
    cif_npr = price_npr + freight_npr + insurance_npr

    # 5. Customs Duties & Taxes
    tariff = HS_DATABASE.get(selected_hs, HS_DATABASE["9999.99"])
    customs_duty_npr = cif_npr * tariff["customs"]
    excise_duty_npr = (cif_npr + customs_duty_npr) * tariff["excise"]
    vat_npr = (cif_npr + customs_duty_npr + excise_duty_npr) * tariff["vat"]

    # 6. Total Landed Cost
    total_cost_npr = cif_npr + customs_duty_npr + excise_duty_npr + vat_npr + CLEARANCE_FEE_NPR

    # Highlight Card
    st.metric(
        label="Total Estimated Landed Cost in Nepal",
        value=f"Rs. {total_cost_npr:,.2f} NPR",
        delta=f"Converted from ₹{price_inr:,.0f} INR (@ 1 INR = {EXCHANGE_RATE_INR_TO_NPR} NPR)"
    )

    st.markdown("---")
    st.markdown("#### Itemized Invoice Breakdown")
    st.caption(f"Category: **{tariff['description']}** (HS Code: `{selected_hs}`)")

    invoice_data = [
        {"Component": "1. Base Product Price (INR)", "Calculation Basis": f"₹{price_inr:,.2f} INR", "Amount in NPR": f"Rs. {price_npr:,.2f}"},
        {"Component": f"2. Freight / Transport ({chargeable_weight:.2f} kg)", "Calculation Basis": f"Chargeable weight @ Rs. {FREIGHT_PER_KG_NPR:.0f}/kg", "Amount in NPR": f"Rs. {freight_npr:,.2f}"},
        {"Component": "3. Cargo Transit Insurance (1%)", "Calculation Basis": "1% of product base price", "Amount in NPR": f"Rs. {insurance_npr:,.2f}"},
        {"Component": "4. Assessable CIF Value", "Calculation Basis": "Customs Base = Product + Freight + Insurance", "Amount in NPR": f"Rs. {cif_npr:,.2f}"},
        {"Component": f"5. Nepal Customs Duty ({int(tariff['customs']*100)}%)", "Calculation Basis": f"{int(tariff['customs']*100)}% on Assessable CIF Value", "Amount in NPR": f"Rs. {customs_duty_npr:,.2f}"},
        {"Component": f"6. Excise Duty ({int(tariff['excise']*100)}%)", "Calculation Basis": f"{int(tariff['excise']*100)}% on (CIF + Customs)", "Amount in NPR": f"Rs. {excise_duty_npr:,.2f}"},
        {"Component": "7. Nepal VAT (13%)", "Calculation Basis": "13% on (CIF + Customs + Excise)", "Amount in NPR": f"Rs. {vat_npr:,.2f}"},
        {"Component": "8. Border Clearing & Handling Fee", "Calculation Basis": "Fixed document handling fee", "Amount in NPR": f"Rs. {CLEARANCE_FEE_NPR:,.2f}"},
        {"Component": "TOTAL ESTIMATED LANDED COST", "Calculation Basis": "Delivered in Nepal with all taxes", "Amount in NPR": f"Rs. {total_cost_npr:,.2f}"}
    ]

    st.table(invoice_data)

    if selected_hs == "8517.13":
        st.warning("📱 **Notice for Mobile Handsets**: Under Nepal Telecommunications Authority (NTA) rules, all imported smartphones must be registered in the **MDMS system** upon arrival.")
