import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing import Dict, Tuple

# =========================================================
# CONFIGURATION
# =========================================================
# Paste your ScraperAPI key between the quotes below:
SCRAPER_API_KEY = "34f6af46dd2237d85972a508370b8ae3"

# Currency & Logistics Constants
EXCHANGE_RATE_INR_TO_NPR = 1.62   # Official peg (1.60) + ~1.25% bank/card markup
FREIGHT_PER_KG_NPR = 550.0        # Average India to Kathmandu freight per kg
INSURANCE_RATE = 0.01             # 1% standard transit insurance
CLEARANCE_FEE_NPR = 350.0         # Local customs clearance & documentation fee

# =========================================================
# NEPAL CUSTOMS TARIFF SCHEDULE (HS CODES)
# =========================================================
HS_DATABASE: Dict[str, Dict] = {
    "8471.30": {
        "description": "Laptops & Portable Computers",
        "customs": 0.01,
        "excise": 0.00,
        "vat": 0.13,
        "category": "Computers"
    },
    "8517.13": {
        "description": "Smartphones / Mobile Handsets",
        "customs": 0.05,
        "excise": 0.00,
        "vat": 0.13,
        "category": "Mobiles"
    },
    "8518.30": {
        "description": "Headphones / Earphones / TWS Earbuds",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13,
        "category": "Audio"
    },
    "9102.12": {
        "description": "Smartwatches & Wristwatches",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13,
        "category": "Wearables"
    },
    "6109.10": {
        "description": "Clothing / T-shirts / Garments",
        "customs": 0.20,
        "excise": 0.00,
        "vat": 0.13,
        "category": "Apparel"
    },
    "6404.11": {
        "description": "Footwear / Sports Shoes / Sneakers",
        "customs": 0.20,
        "excise": 0.00,
        "vat": 0.13,
        "category": "Footwear"
    },
    "3304.99": {
        "description": "Cosmetics / Skincare / Creams",
        "customs": 0.15,
        "excise": 0.05,
        "vat": 0.13,
        "category": "Beauty"
    },
    "4901.99": {
        "description": "Printed Books & Educational Literature",
        "customs": 0.00,
        "excise": 0.00,
        "vat": 0.00,
        "category": "Books"
    },
    "8528.72": {
        "description": "Televisions & Display Monitors",
        "customs": 0.20,
        "excise": 0.05,
        "vat": 0.13,
        "category": "Electronics"
    },
    "9999.99": {
        "description": "General Merchandise / Miscellaneous",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13,
        "category": "General"
    }
}

# =========================================================
# HELPER FUNCTIONS
# =========================================================
class CostResult(BaseModel):
    product_name: str
    hs_code: str
    hs_description: str
    price_inr: float
    price_npr: float
    chargeable_weight_kg: float
    freight_npr: float
    insurance_npr: float
    cif_npr: float
    customs_duty_npr: float
    excise_duty_npr: float
    vat_npr: float
    handling_fee_npr: float
    final_cost_npr: float


def auto_detect_hs_code(title: str) -> str:
    """Classifies the product title to the closest Nepal Customs HS Code."""
    t = title.lower()
    if any(k in t for k in ["laptop", "macbook", "thinkpad", "notebook"]):
        return "8471.30"
    if any(k in t for k in ["iphone", "smartphone", "galaxy", "redmi", "oneplus", "phone"]):
        return "8517.13"
    if any(k in t for k in ["headphone", "earphone", "airpods", "buds", "earbuds"]):
        return "8518.30"
    if any(k in t for k in ["smartwatch", "watch", "smart band"]):
        return "9102.12"
    if any(k in t for k in ["shirt", "t-shirt", "pant", "hoodie", "dress", "jacket"]):
        return "6109.10"
    if any(k in t for k in ["shoe", "sneaker", "sandal", "boots"]):
        return "6404.11"
    if any(k in t for k in ["serum", "lotion", "cream", "lipstick", "perfume"]):
        return "3304.99"
    if any(k in t for k in ["book", "novel", "paperback"]):
        return "4901.99"
    if any(k in t for k in ["tv", "television", "monitor"]):
        return "8528.72"
    return "9999.99"


def scrape_indian_url(url: str) -> Tuple[str, float, float]:
    """Fetches product details using ScraperAPI proxy or direct fallback."""
    extracted_title = ""
    extracted_price = 0.0
    extracted_weight = 1.0

    try:
        if SCRAPER_API_KEY and SCRAPER_API_KEY != "YOUR_SCRAPERAPI_KEY":
            target_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
            headers = {}
        else:
            target_url = url
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
            }

        response = requests.get(target_url, headers=headers, timeout=25)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # Amazon Title & Price
            t_tag = soup.find("span", {"id": "productTitle"})
            if t_tag:
                extracted_title = t_tag.get_text(strip=True)

            p_tag = soup.find("span", {"class": "a-price-whole"})
            if p_tag:
                cleaned_price = re.sub(r"[^\d.]", "", p_tag.get_text())
                if cleaned_price:
                    extracted_price = float(cleaned_price)

            # Flipkart Title & Price (Fallback)
            if not extracted_title:
                f_title = soup.find("span", {"class": "B_NuCI"}) or soup.find("h1", {"class": "VU-ZEz"})
                if f_title:
                    extracted_title = f_title.get_text(strip=True)

            if extracted_price == 0.0:
                f_price = soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj CxhGGd"})
                if f_price:
                    cleaned_price = re.sub(r"[^\d.]", "", f_price.get_text())
                    if cleaned_price:
                        extracted_price = float(cleaned_price)
    except Exception:
        pass

    return extracted_title, extracted_price, extracted_weight


def calculate_cost(
    title: str,
    price_inr: float,
    weight_kg: float,
    dimensions: Tuple[float, float, float],
    hs_code: str
) -> CostResult:
    length, width, height = dimensions
    volumetric_weight = (length * width * height) / 5000.0 if (length > 0 and width > 0 and height > 0) else 0.0
    chargeable_weight = max(weight_kg, volumetric_weight, 0.5)

    price_npr = price_inr * EXCHANGE_RATE_INR_TO_NPR
    freight_npr = chargeable_weight * FREIGHT_PER_KG_NPR
    insurance_npr = price_npr * INSURANCE_RATE
    cif_npr = price_npr + freight_npr + insurance_npr

    tariff = HS_DATABASE.get(hs_code, HS_DATABASE["9999.99"])
    customs_duty_npr = cif_npr * tariff["customs"]
    excise_duty_npr = (cif_npr + customs_duty_npr) * tariff["excise"]
    vat_npr = (cif_npr + customs_duty_npr + excise_duty_npr) * tariff["vat"]

    final_cost = cif_npr + customs_duty_npr + excise_duty_npr + vat_npr + CLEARANCE_FEE_NPR

    return CostResult(
        product_name=title,
        hs_code=hs_code,
        hs_description=tariff["description"],
        price_inr=price_inr,
        price_npr=round(price_npr, 2),
        chargeable_weight_kg=round(chargeable_weight, 2),
        freight_npr=round(freight_npr, 2),
        insurance_npr=round(insurance_npr, 2),
        cif_npr=round(cif_npr, 2),
        customs_duty_npr=round(customs_duty_npr, 2),
        excise_duty_npr=round(excise_duty_npr, 2),
        vat_npr=round(vat_npr, 2),
        handling_fee_npr=CLEARANCE_FEE_NPR,
        final_cost_npr=round(final_cost, 2)
    )

# =========================================================
# STREAMLIT UI
# =========================================================
st.set_page_config(page_title="Indo-Nepal Import Cost Agent", page_icon="🇳🇵", layout="wide")

st.title("🇳🇵 Indo-Nepal E-Commerce Import Agent")
st.markdown("Calculate the total landed cost of shopping from Indian platforms (**Amazon.in, Flipkart, Myntra**) with **Nepal Customs HS Codes, Freight, and VAT**.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Product Details")
    mode = st.radio("Input Method:", ["Paste Product Link", "Enter Details Manually"], horizontal=True)

    default_title = "Puma Men's Running Shoes"
    default_price = 3499.0
    default_weight = 1.2
if mode == "Paste Product Link":
        product_url = st.text_input("Paste Indian Product Link:", placeholder="https://www.amazon.in/dp/B0CX214GBN")
        if product_url:
            with st.spinner("Extracting product information via proxy..."):
                s_title, s_price, s_weight = scrape_indian_url(product_url)
                if s_title:
                    default_title = s_title
                if s_price > 0:
                    default_price = s_price

                if s_title and s_price > 0:
                    st.success("✅ Extracted product details successfully!")
                else:
                    st.info("ℹ️ Enter the name and price below if the link could not be automatically parsed.")
