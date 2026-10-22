import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple
from urllib.parse import urlparse, unquote

# =========================================================
# 1. TARIFF SCHEDULE & SETTINGS (NEPAL CUSTOMS)
# =========================================================
EXCHANGE_RATE_INR_TO_NPR = 1.62   # Official peg 1.60 + ~1.25% banking/card markup
FREIGHT_PER_KG_NPR = 550.0        # Courier express per kg (India to KTM)
INSURANCE_RATE = 0.01             # 1% standard transit insurance
CLEARANCE_FEE_NPR = 350.0         # Border handling and documentation fee

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
        "description": "Headphones / Earphones / TWS Earbuds / Speakers",
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
        "description": "Western Apparel / T-shirts / Jeans / Hoodies",
        "customs": 0.20,
        "excise": 0.00,
        "vat": 0.13
    },
    "6204.42": {
        "description": "Ethnic Wear / Sarees / Kurtas / Lehengas",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13
    },
    "6404.11": {
        "description": "Footwear / Sports Shoes / Sneakers / Heels",
        "customs": 0.20,
        "excise": 0.00,
        "vat": 0.13
    },
    "3304.99": {
        "description": "Cosmetics / Skincare / Makeup / Perfumes",
        "customs": 0.15,
        "excise": 0.05,
        "vat": 0.13
    },
    "2106.10": {
        "description": "Health Supplements / Whey Protein / Vitamins",
        "customs": 0.15,
        "excise": 0.00,
        "vat": 0.13
    },
    "8509.40": {
        "description": "Kitchen & Home Appliances (Mixers, Air Fryers)",
        "customs": 0.15,
        "excise": 0.00,
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
# 2. DEDICATED SCRAPING ENGINE (AMAZON + FLIPKART + OTHERS)
# =========================================================
def detect_platform(url: str) -> str:
    domain = urlparse(url).netloc.lower()
    if "amazon" in domain:
        return "Amazon India"
    elif "flipkart" in domain:
        return "Flipkart"
    elif "myntra" in domain:
        return "Myntra"
    elif "nykaa" in domain:
        return "Nykaa"
    elif "ajio" in domain:
        return "Ajio"
    return "Indian E-Commerce"


def get_slug_title(url: str) -> str:
    """Extracts clean product name from URL as backup."""
    try:
        path = unquote(urlparse(url).path)
        amz = re.search(r"/([^/?]+)/dp/", path, re.I)
        if amz:
            slug = amz.group(1).replace("-", " ")
            return " ".join([w.capitalize() for w in slug.split() if w.lower() not in ["gp", "product"]])

        fk = re.search(r"/([^/?]+)/p(?:/|$)", path, re.I)
        if fk:
            slug = fk.group(1).replace("-", " ")
            return " ".join([w.capitalize() for w in slug.split() if not w.isdigit()])
    except Exception:
        pass
    return ""


def scrape_product_info(url: str) -> Tuple[str, float, str]:
    """Dedicated scraper for Amazon and Flipkart that avoids EMI/coupons."""
    platform = detect_platform(url)
    title = get_slug_title(url)
    price = 0.0

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-IN,en-GB,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    html = ""
    # 1. Attempt direct request
    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200 and "Robot Check" not in r.text:
            html = r.text
    except Exception:
        pass

    # 2. Fallback to rendered proxy if blocked
    if not html or "Robot Check" in html:
        try:
            proxy_url = f"https://r.jina.ai/{url}"
            pr = requests.get(proxy_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if pr.status_code == 200:
                html = pr.text
        except Exception:
            pass

    if html:
        soup = BeautifulSoup(html, "html.parser")

        # --- A. AMAZON PARSER ---
        if "Amazon" in platform:
            t_tag = soup.find("span", {"id": "productTitle"})
            if t_tag:
                title = t_tag.get_text(strip=True)

            # Amazon exact price tags
            p_tag = soup.find("span", {"class": "a-price-whole"})
            if p_tag:
                raw_p = re.sub(r"[^\d.]", "", p_tag.get_text())
                if raw_p:
                    price = float(raw_p)

            if price == 0.0:
                core_p = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"}) or soup.find("div", {"id": "corePrice_feature_div"})
                if core_p:
                    off_p = core_p.find("span", {"class": "a-offscreen"})
                    if off_p:
                        raw_p = re.sub(r"[^\d.]", "", off_p.get_text())
                        if raw_p:
                            price = float(raw_p)

        # --- B. FLIPKART PARSER ---
        elif "Flipkart" in platform:
            # Flipkart Title
            fk_t = soup.find("h1", {"class": "VU-ZEz"}) or soup.find("span", {"class": "B_NuCI"}) or soup.find("h1", {"class": "_6EBuvd"})
            if fk_t:
                title = fk_t.get_text(strip=True)
            elif soup.title and "Price in India" in soup.title.string:
                clean_t = re.sub(r"\s*(?:Price in India|Buy .*|Online at Flipkart).*$", "", soup.title.string, flags=re.I).strip()
                if clean_t:
                    title = clean_t

            # Flipkart Price
            fk_p = soup.find("div", {"class": "Nx9bqj CxhGGd"}) or soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj"}) or soup.find("div", {"class": "_30jeq3"})
            if fk_p:
                raw_p = re.sub(r"[^\d.]", "", fk_p.get_text())
                if raw_p:
                    price = float(raw_p)

        # --- C. GENERIC PARSER (Mynt
