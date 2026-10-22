import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple

# =========================================================
# 1. APP CONFIGURATION & TARIFF DATABASE
# =========================================================
# Set your free ScraperAPI key here if you have one (or leave as-is):
SCRAPER_API_KEY = "34f6af46dd2237d85972a508370b8ae3"

# Currency & Logistics Constants (Nepal Customs Standard)
EXCHANGE_RATE_INR_TO_NPR = 1.62   # Official peg (1.60) + ~1.25% banking/card fee
FREIGHT_PER_KG_NPR = 550.0        # Courier express air/surface per kg
INSURANCE_RATE = 0.01             # 1% standard cargo insurance
CLEARANCE_FEE_NPR = 350.0         # Border handling and customs documentation fee

# Official Nepal Customs Tariff Schedule (HS Codes)
HS_DATABASE: Dict[str, Dict] = {
    "8471.30": {
        "description": "Laptops & Portable Computers",
        "customs": 0.01,  # 1%
        "excise": 0.00,
        "vat": 0.13,
        "category": "Computers"
    },
    "8517.13": {
        "description": "Smartphones / Mobile Handsets",
        "customs": 0.05,  # 5%
        "excise": 0.00,
        "vat": 0.13,
        "category": "Mobiles"
    },
    "8518.30": {
        "description": "Headphones / Earphones / TWS Earbuds",
        "customs": 0.15,  # 15%
        "excise": 0.00,
        "vat": 0.13,
        "category": "Audio"
    },
    "9102.12": {
        "description": "Smartwatches & Wristwatches",
        "customs": 0.15,  # 15%
        "excise": 0.00,
        "vat": 0.13,
        "category": "Wearables"
    },
    "6109.10": {
        "description": "Clothing / T-shirts / Knitted Garments",
        "customs": 0.20,  # 20%
        "excise": 0.00,
        "vat": 0.13,
        "category": "Apparel"
    },
    "6404.11": {
        "description": "Footwear / Sports Shoes / Sneakers",
        "customs": 0.20,  # 20%
        "excise": 0.00,
        "vat": 0.13,
        "category": "Footwear"
    },
    "3304.99": {
        "description": "Cosmetics / Skincare / Creams / Serums",
        "customs": 0.15,  # 15%
        "excise": 0.05,  # 5% Excise
        "vat": 0.13,
        "category": "Beauty"
    },
    "4901.99": {
        "description": "Printed Books & Educational Literature",
        "customs": 0.00,  # 0%
        "excise": 0.00,
        "vat": 0.00,      # Exempt from VAT
        "category": "Books"
    },
    "8528.72": {
        "description": "Televisions & Display Monitors",
        "customs": 0.20,  # 20%
        "excise": 0.05,  # 5% Excise
        "vat": 0.13,
        "category": "Electronics"
    },
    "9999.99": {
        "description": "General Merchandise / Miscellaneous",
        "customs": 0.15,  # 15% Standard
        "excise": 0.00,
        "vat": 0.13,
        "category": "General"
    }
}

# =========================================================
# 2. LOGIC FUNCTIONS
# =========================================================
def auto_detect_hs_code(title: str) -> str:
    """Classifies the product title to the closest Nepal Customs HS Code."""
    t = title.lower()
    if any(k in t for k in ["laptop", "macbook", "thinkpad", "notebook", "chromebook"]):
        return "8471.30"
    if any(k in t for k in ["iphone", "smartphone", "galaxy", "redmi", "oneplus", "phone"]):
        return "8517.13"
    if any(k in t for k in ["headphone", "earphone", "airpods", "buds", "earbuds"]):
        return "8518.30"
    if any(k in t for k in ["smartwatch", "watch", "smart band"]):
        return "9102.12"
    if any(k in t for k in ["shirt", "t-shirt", "pant", "hoodie", "dress", "jacket", "jeans"]):
        return "6109.10"
    if any(k in t for k in ["shoe", "sneaker", "sandal", "boots", "crocs"]):
        return "6404.11"
    if any(k in t for k in ["serum", "lotion", "cream", "lipstick", "perfume", "shampoo"]):
        return "3304.99"
    if any(k in t for k in ["book", "novel", "paperback"]):
        return "4901.99"
    if any(k in t for k in ["tv", "television", "monitor"]):
        return "8528.72"
    return "9999.99"


def scrape_indian_url(url: str) -> Tuple[str, float]:
    """Attempts to scrape title and INR price using ScraperAPI or direct fetch."""
    title = ""
    price = 0.0

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

        resp = requests.get(target_url, headers=headers, timeout=20)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")

            # Amazon Title & Price
            t_tag = soup.find("span", {"id": "productTitle"})
            if t_tag:
                title = t_tag.get_text(strip=True)

            p_tag = soup.find("span", {"class": "a-price-whole"})
            if p_tag:
                clean_p = re.sub(r"[^\d.]", "", p_tag.get_text())
                if clean_p:
                    price = float(clean_p)

            # Flipkart Title & Price
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
# 3. STREAMLIT INTERFACE
# =========================================================
st.set_page_config(page_title="Indo-Nepal Import Cost Agent", page_icon="🇳🇵", layout="wide")

st.title("🇳🇵 Indo-Nepal E-Commerce Landed Cost Calculator")
st.markdown("Calculate the complete cost of importing products from **Amazon India, Flipkart & Myntra** to Nepal with **Customs Duties, Transportation, and 13% VAT**.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Product & Shipping Details")
    input_method = st.radio("Choose Input Mode:", ["Paste Product Link", "Enter Details Manually"], horizontal=True)

    curr_title = "Puma Men's Running Shoes"
    curr_price = 3499.0
    curr_weight = 1.2

    if input_method == "Paste Product Link":
        url_input = st.text_input("Paste Indian Product URL:", placeholder="https://www.amazon.in/dp/B0CX214GBN")
        if url_input:
            with st.spinner("Fetching product details..."):
                scraped_title, scraped_price = scrape_indian_url(url_input)
                if scraped_title:
                    curr_title = scraped_title
                if scraped_price > 0:
                    curr_price = scraped_price
                
                if scraped_title and scraped_price > 0:
                    st.success("✅ Extracted product details successfully!")
                else:
    st.info("ℹ️ Enter the name and price below to calculate.")
