import streamlit as st
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple
from urllib.parse import urlparse, unquote

# =========================================================
# 1. TARIFF SCHEDULE & SETTINGS
# =========================================================
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
        "description": "Headphones / Earbuds / Speakers",
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
        "description": "Western Apparel / T-shirts / Hoodies / Jeans",
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
        "description": "Footwear / Sports Shoes / Sandals / Heels",
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
# 2. ACCURATE PRICE & TITLE EXTRACTOR
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
    elif "tatacliq" in domain:
        return "Tata CLiQ"
    elif "croma" in domain:
        return "Croma"
    return "Indian E-Commerce"


def extract_fallback_title(url: str) -> str:
    """Extracts clean product names from URL path if page blocks scraping."""
    try:
        parsed = urlparse(unquote(url))
        amz = re.search(r"/([^/?]+)/dp/", parsed.path, re.I)
        if amz:
            slug = amz.group(1).replace("-", " ")
            return " ".join([w.capitalize() for w in slug.split() if w.lower() not in ["gp", "product"]])

        fk = re.search(r"/([^/?]+)/p(?:/|$)", parsed.path, re.I)
        if fk:
            slug = fk.group(1).replace("-", " ")
            return " ".join([w.capitalize() for w in slug.split() if not w.isdigit()])
    except Exception:
        pass
    return ""


def parse_json_ld(soup: BeautifulSoup) -> Tuple[str, float]:
    """Extracts exact product price and title from Schema.org JSON-LD (Zero EMI error)."""
    title = ""
    price = 0.0
    try:
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for s in scripts:
            if not s.string:
                continue
            try:
                data = json.loads(s.string)
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if item.get("@type") == "Product" or "Product" in str(item.get("@type")):
                        if not title and item.get("name"):
                            title = str(item.get("name")).strip()
                        offers = item.get("offers")
                        if isinstance(offers, list) and len(offers) > 0:
                            offers = offers[0]
                        if isinstance(offers, dict):
                            p = offers.get("price") or offers.get("lowPrice")
                            if p:
                                price = float(str(p).replace(",", ""))
                                break
                if price > 0:
                    break
            except Exception:
                continue
    except Exception:
        pass
    return title, price


def scrape_ecommerce_url(url: str) -> Tuple[str, float]:
    """Accurately extracts real price without getting tricked by EMI or coupons."""
    title = extract_fallback_title(url)
    price = 0.0

    # Method 1: Direct Fetch with realistic browser headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    html_content = ""
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200 and "Robot Check" not in resp.text:
            html_content = resp.text
    except Exception:
        pass

    # If direct fetch was blocked by anti-bot, fetch through public rendered mirror
    if not html_content or "Robot Check" in html_content:
        try:
            j_resp = requests.get(f"https://r.jina.ai/{url}", headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if j_resp.status_code == 200:
                html_content = j_resp.text
        except Exception:
            pass

    if html_content:
        # 1. Try parsing JSON-LD Schema
        soup = BeautifulSoup(html_content, "html.parser")
        json_title, json_price = parse_json_ld(soup)
        if json_title:
            title = json_title
        if json_price > 0:
            price = json_price

        # 2. Targeted Amazon DOM Selectors
        if price == 0.0 and "amazon" in url.lower():
            # Real selling price container on Amazon
            core_price = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"}) or soup.find("div", {"id": "corePrice_feature_div"})
            if core_price:
                price_whole = core_price.find("span", {"class": "a-price-whole"})
                if price_whole:
                    clean = re.sub(r"[^\d.]", "", price_whole.get_text())
                    if clean:
                        price = float(clean)

            if not title:
                t_elem = soup.find("span", {"id": "productTitle"})
                if t_elem:
                    title = t_elem.get_text(strip=True)

        # 3. Targeted Flipkart DOM Selectors
        if price == 0.0 and "flipkart" in url.lower():
            # Flipkart current desktop selling price classes
            fk_price = soup.find("div", {"class": "Nx9bqj CxhGGd"}) or soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj"})
            if fk_price:
                clean = re.sub(r"[^\d.]", "", fk_price.get_text())
                if clean:
                    price = float(clean)

            if not title:
                fk_title = soup.find("h1", {"class": "VU-ZEz"}) or soup.find("span", {"class": "B_NuCI"})
                if fk_title:
                    title = fk_title.get_text(strip=True)

        # 4. Strict Markdown Fallback (Avoid EMI & Coupons)
        if price == 0.0:
            lines = html_content.splitlines()
            for line in lines:
                lower_l = line.lower()
                # STRICT FILTER: Skip EMI, discounts, coupons, delivery charges
                if any(bad in lower_l for bad in ["emi", "save", "coupon", "discount", "off", "delivery", "cashback", "per month"]):
                    continue
                # Look for genuine price indicators
                if any(curr in line for curr in ["₹", "INR", "Rs."]):
                    matches = re.findall(r"(?:₹|INR|\bRs\.?)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?)", line)
                    if matches:
                        for m in matches:
                            val = float(m.replace(",", ""))
                            if val >= 199.0:  # Valid items
                                price = val
                                break
                    if price > 0.0:
                        break

    return title, price


def auto_detect_hs_code(title: str) -> str:
    """Matches product title to the closest Nepal Customs HS Code."""
    t = title.lower()
    if any(k in t for k in ["laptop", "macbook", "thinkpad", "notebook"]):
        return "8471.30"
    if any(k in t for k in ["iphone", "smartphone", "galaxy", "redmi", "oneplus", "phone"]):
        return "8517.13"
    if any(k in t for k in ["headphone", "earphone", "airpods", "buds", "earbuds", "speaker"]):
        return "8518.30"
    if any(k in t for k in ["smartwatch", "watch", "smart band"]):
        return "9102.12"
    if any(k in t for k in ["tv", "television", "monitor"]):
        return "8528.72"
    if any(k in t for k in ["mixer", "blender", "air fryer", "grinder", "cooker", "kettle", "toaster"]):
        return "8509.40"
    if any(k in t for k in ["saree", "sari", "kurta", "kurti", "lehenga", "anarkali", "ethnic", "dupatta"]):
        return "6204.42"
    if any(k in t for k in ["shirt", "t-shirt", "pant", "trousers", "hoodie", "dress", "jacket", "jeans"]):
        return "6109.10"
    if any(k in t for k in ["shoe", "sneaker", "sandal", "boots", "crocs", "loafers", "heels"]):
        return "6404.11"
    if any(k in t for k in ["serum", "lotion", "cream", "lipstick", "perfume", "shampoo", "sunscreen", "makeup"]):
        return "3304.99"
    if any(k in t for k in ["whey", "protein", "creatine", "vitamin", "bcaa", "supplement"]):
        return "2106.10"
    if any(k in t for k in ["book", "novel", "paperback"]):
        return "4901.99"
    return "9999.99"


# =========================================================
# 3. STREAMLIT USER INTERFACE
# =========================================================
st.set_page_config(page_title="Indo-Nepal Universal Import Agent", page_icon="🇳🇵", layout="wide")

st.title("🇳🇵 Universal Indian E-Commerce Import Agent")
st.markdown("Search products from **Amazon, Flipkart, Myntra, Nykaa, Ajio** and calculate the exact delivered landed cost in Nepal.")

# Initialize persistent session variables
if "prod_title" not in st.session_state:
    st.session_state.prod_title = "Puma Men's Running Shoes"
if "prod_price" not in st.session_state:
    st.session_state.prod_price = 3499.0
if "platform_name" not in st.session_state:
    st.session_state.platform_name = ""

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Product Search")
    url_input = st.text_input(
        "Paste Indian Product URL (Amazon / Flipkart / Myntra):", 
        placeholder="https://www.amazon.in/dp/... or https://www.flipkart.com/..."
    )
    
    search_clicked = st.button("🔍 Search Product", type="primary", use_container_width=True)

    if search_clicked:
        if url_input.strip():
            st.session_state.platform_name = detect_platform(url_input)
            with st.spinner(f"Extracting authentic price from {st.session_state.platform_name}..."):
                extracted_t, extracted_p = scrape_ecommerce_url(url_input)
                
                if extracted_t:
                    st.session_state.prod_title = extracted_t
                if extracted_p > 0:
                    st.session_state.prod_price = extracted_p
                
                if extracted_p > 0:
                    st.success(f"✅ Found product on {st.session_state.platform_name}! Price: ₹{extracted_p:,.2f}")
                else:
                    st.warning("⚠️ Title detected, but please confirm the price in the box below.")
        else:
            st.warning("Please paste a link first.")

    if st.session_state.platform_name:
        st.caption(f"🛍️ Platform: **{st.session_state.platform_name}**")

    st.markdown("---")
    st.markdown("##### Verify & Adjust Product Details")
    
    # Input boxes reflect the real values
    final_title = st.text_input("Product Title / Name:", value=st.session_state.prod_title)
    final_price_inr = st.number_input(
        "Price in India (₹ INR):", 
        min_value=1.0, 
        value=float(st.session_state.prod_price), 
        step=50.0
    )

    col_w, col_l, col_wi, col_h = st.columns(4)
    with col_w:
        weight_kg = st.number_input("Weight (kg):", min_value=0.1, value=1.0, step=0.1)
    with col_l:
        dim_l = st.number_input("Length (cm):", value=25.0, step=5.0)
    with col_wi:
        dim_w = st.number_input("Width (cm):", value=15.0, step=5.0)
    with col_h:
        dim_h = st.number_input("Height (cm):", value=10.0, step=5.0)

    st.subheader("2. Customs Classification")
    detected_hs = auto_detect_hs_code(final_title)
    all_hs = list(HS_DATABASE.keys())
    selected_hs = st.selectbox(
        "Nepal Customs HS Code:",
        options=all_hs,
        index=all_hs.index(detected_hs),
        format_func=lambda x: f"HS {x} — {HS_DATABASE[x]['description']} (Duty: {int(HS_DATABASE[x]['customs']*100)}%)"
    )

with col_right:
    st.subheader("3. Cost & Customs Breakdown")

    # --- Calculation Engine (Nepal Customs Act Model) ---
    volumetric_weight = (dim_l * dim_w * dim_h) / 5000.0 if (dim_l > 0 and dim_w > 0 and dim_h > 0) else 0.0
    chargeable_weight = max(weight_kg, volumetric_weight, 0.5)

    # 1. Base Conversion
    price_npr = final_price_inr * EXCHANGE_RATE_INR_TO_NPR

    # 2. Freight & Cargo Insurance
    freight_npr = chargeable_weight * FREIGHT_PER_KG_NPR
    insurance_npr = price_npr * INSURANCE_RATE

    # 3. Assessable Value (CIF: Cost + Insurance + Freight)
    cif_npr = price_npr + freight_npr + insurance_npr

    # 4. Customs Duties & Taxes
    tariff = HS_DATABASE.get(selected_hs, HS_DATABASE["9999.99"])
    customs_duty_npr = cif_npr * tariff["customs"]
    excise_duty_npr = (cif_npr + customs_duty_npr) * tariff["excise"]
    vat_npr = (cif_npr + customs_duty_npr + excise_duty_npr) * tariff["vat"]

    # 5. Total Landed Cost
    total_cost_npr = cif_npr + customs_duty_npr + excise_duty_npr + vat_npr + CLEARANCE_FEE_NPR

    # Big Summary Metric
    st.metric(
        label="Total Estimated Landed Cost in Nepal",
        value=f"Rs. {total_cost_npr:,.2f} NPR",
        delta=f"Converted from ₹{final_price_inr:,.2f} INR (@ 1 INR = {EXCHANGE_RATE_INR_TO_NPR} NPR)"
    )

    st.markdown("---")
    st.markdown("#### Itemized Invoice Breakdown")
    st.caption(f"Category: **{tariff['description']}** (HS Code: `{selected_hs}`)")

    invoice_data = [
        {"Component": "1. Base Product Price (INR)", "Basis": f"₹{final_price_inr:,.2f} INR", "Amount in NPR": f"Rs. {price_npr:,.2f}"},
        {"Component": f"2. Freight / Transport ({chargeable_weight:.2f} kg)", "Basis": f"Chargeable weight @ Rs. {FREIGHT_PER_KG_NPR:.0f}/kg", "Amount in NPR": f"Rs. {freight_npr:,.2f}"},
        {"Component": "3. Cargo Transit Insurance (1%)", "Basis": "1% of product base price", "Amount in NPR": f"Rs. {insurance_npr:,.2f}"},
        {"Component": "4. Assessable CIF Value", "Basis": "Customs Base = Product + Freight + Insurance", "Amount in NPR": f"Rs. {cif_npr:,.2f}"},
        {"Component": f"5. Nepal Customs Duty ({int(tariff['customs']*100)}%)", "Basis": f"{int(tariff['customs']*100)}% on Assessable CIF Value", "Amount in NPR": f"Rs. {customs_duty_npr:,.2f}"},
        {"Component": f"6. Excise Duty ({int(tariff['excise']*100)}%)", "Basis": f"{int(tariff['excise']*100)}% on (CIF + Customs)", "Amount in NPR": f"Rs. {excise_duty_npr:,.2f}"},
        {"Component": "7. Nepal VAT (13%)", "Basis": "13% on (CIF + Customs + Excise)", "Amount in NPR": f"Rs. {vat_npr:,.2f}"},
        {"Component": "8. Border Clearing & Handling Fee", "Basis": "Fixed document handling fee", "Amount in NPR": f"Rs. {CLEARANCE_FEE_NPR:,.2f}"},
        {"Component": "TOTAL ESTIMATED LANDED COST", "Basis": "Delivered in Nepal with all taxes", "Amount in NPR": f"Rs. {total_cost_npr:,.2f}"}
    ]

    st.table(invoice_data)

    if selected_hs == "8517.13":
        st.warning("📱 **Notice for Mobile Handsets**: Under Nepal Telecommunications Authority (NTA) rules, all imported smartphones must be registered in the **MDMS system** upon arrival.")
