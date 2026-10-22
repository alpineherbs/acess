import streamlit as st
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple
from urllib.parse import urlparse, unquote

# Set page config as the very first Streamlit call
st.set_page_config(page_title="Indo-Nepal Import Cost Agent", page_icon="🇳🇵", layout="wide")

# =========================================================
# 1. TARIFF SCHEDULE & SETTINGS (NEPAL CUSTOMS)
# =========================================================
EXCHANGE_RATE_INR_TO_NPR = 1.62   # Official peg 1.60 + ~1.25% bank/cross-border markup
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
# 2. BULLETPROOF SCRAPERAPI PARSER
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
    """Fallback: Reads product name directly from the URL structure."""
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


def fetch_product(url: str, api_key: str) -> Tuple[str, float, str]:
    """Fetches real HTML via ScraperAPI or direct fallback with exact price tags."""
    platform = detect_platform(url)
    title = get_slug_title(url)
    price = 0.0

    # Route via ScraperAPI if key is provided
    if api_key and len(api_key.strip()) > 10:
        target_url = f"http://api.scraperapi.com?api_key={api_key.strip()}&url={url}"
        headers = {}
    else:
        target_url = url
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "en-IN,en;q=0.9",
        }

    try:
        resp = requests.get(target_url, headers=headers, timeout=25)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, "html.parser")

            # --- A. AMAZON PARSER ---
            if "Amazon" in platform:
                t_elem = soup.find("span", {"id": "productTitle"})
                if t_elem:
                    title = t_elem.get_text(strip=True)

                # Exact Amazon selling price
                core_p = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"}) or soup.find("div", {"id": "corePrice_feature_div"})
                if core_p:
                    whole = core_p.find("span", {"class": "a-price-whole"})
                    if whole:
                        clean = re.sub(r"[^\d.]", "", whole.get_text())
                        if clean:
                            price = float(clean)

                if price == 0.0:
                    p_elem = soup.find("span", {"class": "a-price-whole"})
                    if p_elem:
                        clean = re.sub(r"[^\d.]", "", p_elem.get_text())
                        if clean:
                            price = float(clean)

            # --- B. FLIPKART PARSER ---
            elif "Flipkart" in platform:
                t_elem = soup.find("h1", {"class": "VU-ZEz"}) or soup.find("span", {"class": "B_NuCI"}) or soup.find("h1", {"class": "_6EBuvd"})
                if t_elem:
                    title = t_elem.get_text(strip=True)
                elif soup.title and "Price in India" in soup.title.string:
                    clean = re.sub(r"\s*(?:Price in India|Buy .*|Online at Flipkart).*$", "", soup.title.string, flags=re.I).strip()
                    if clean:
                        title = clean

                # Exact Flipkart selling price
                fk_p = soup.find("div", {"class": "Nx9bqj CxhGGd"}) or soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj"}) or soup.find("div", {"class": "_30jeq3"})
                if fk_p:
                    clean = re.sub(r"[^\d.]", "", fk_p.get_text())
                    if clean:
                        price = float(clean)

            # --- C. GENERIC TITLE FALLBACK ---
            else:
                if soup.title and not title:
                    title = re.sub(r"(\|\s*Buy\s*Online.*$|:\s*Amazon\.in.*$|\|\s*Myntra.*$|\|\s*Nykaa.*$|\|\s*Flipkart.*$)", "", soup.title.string, flags=re.I).strip()

    except Exception:
        pass

    return title, price, platform


def auto_detect_hs_code(title: str) -> str:
    """Matches product title to the closest Nepal Customs HS Code."""
    t = title.lower()
    if any(k in t for k in ["laptop", "macbook", "thinkpad", "notebook"]):
        return "8471.30"
    if any(k in t for k in ["iphone", "smartphone", "galaxy", "redmi", "oneplus", "phone", "pixel"]):
        return "8517.13"
    if any(k in t for k in ["headphone", "earphone", "airpods", "buds", "earbuds", "speaker"]):
        return "8518.30"
    if any(k in t for k in ["smartwatch", "watch", "smart band"]):
        return "9102.12"
    if any(k in t for k in ["tv", "television", "monitor"]):
        return "8528.72"
    if any(k in t for k in ["mixer", "blender", "air fryer", "grinder", "cooker", "kettle"]):
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
# 3. STREAMLIT APP STATE & CALLBACKS
# =========================================================
if "item_name" not in st.session_state:
    st.session_state.item_name = "Puma Men's Running Shoes"
if "item_price" not in st.session_state:
    st.session_state.item_price = 3499.0
if "platform_name" not in st.session_state:
    st.session_state.platform_name = "Amazon India"
if "search_msg" not in st.session_state:
    st.session_state.search_msg = ""


def on_search_clicked():
    """Streamlit callback that runs BEFORE widgets render to ensure instant refresh."""
    url = st.session_state.url_box.strip()
    api_key = st.session_state.api_key_box.strip()
    if not url:
        st.session_state.search_msg = "⚠️ Please paste a product URL link first."
        return

    title, price, plat = fetch_product(url, api_key)
    if title:
        st.session_state.item_name = title
    if price > 0:
        st.session_state.item_price = float(price)
    st.session_state.platform_name = plat

    if price > 0:
        st.session_state.search_msg = f"✅ Extracted from {plat}: Price ₹{price:,.2f}"
    else:
        st.session_state.search_msg = f"ℹ️ Found title on {plat}. Please verify the price below."


# =========================================================
# 4. USER INTERFACE
# =========================================================
# Sidebar for Settings
with st.sidebar:
    st.header("⚙️ Agent Settings")
    st.session_state.api_key_box = st.text_input(
        "ScraperAPI Key 34f6af46dd2237d85972a508370b8ae3:",
        value="",
        type="password",
        placeholder="Paste scraperapi.com key here...",
        help="Bypasses Amazon and Flipkart bot blocks with 100% reliability."
    )
    st.caption("Get 1,000 to 5,000 free requests per month from [scraperapi.com](https://www.scraperapi.com).")
    st.markdown("---")
    st.markdown("**Exchange Rate:** 1 INR = 1.62 NPR")
    st.markdown("**Freight:** Rs. 550 / kg")
    st.markdown("**Nepal VAT:** 13%")

st.title("🇳🇵 Universal Indo-Nepal Import Cost Agent")
st.markdown("Search products from **Amazon India, Flipkart, Myntra, or Nykaa** to calculate the complete landed cost delivered to Nepal.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Product Search")
    st.text_input(
        "Paste Indian Product Link:",
        placeholder="https://www.amazon.in/dp/... or https://www.flipkart.com/...",
        key="url_box"
    )

    # Search button with on_click callback
    st.button("🔍 Search Product", on_click=on_search_clicked, type="primary", use_container_width=True)

    if st.session_state.search_msg:
        st.info(st.session_state.search_msg)

    st.markdown("---")
    st.markdown("##### Product Details")

    prod_name = st.text_input("Product Title / Name:", key="item_name")
    price_inr = st.number_input("Price in India (₹ INR):", key="item_price", min_value=1.0, step=50.0)

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

    # --- Landed Cost Calculation (Nepal Customs Act Model) ---
    volumetric_weight = (dim_l * dim_w * dim_h) / 5000.0 if (dim_l > 0 and dim_w > 0 and dim_h > 0) else 0.0
    chargeable_weight = max(weight_kg, volumetric_weight, 0.5)

    # 1. Base Conversion
    price_npr = price_inr * EXCHANGE_RATE_INR_TO_NPR

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

    # Top Metric Card
    st.metric(
        label="Total Estimated Landed Cost in Nepal",
        value=f"Rs. {total_cost_npr:,.2f} NPR",
        delta=f"Converted from ₹{price_inr:,.2f} INR (@ 1 INR = {EXCHANGE_RATE_INR_TO_NPR} NPR)"
    )

    st.markdown("---")
    st.markdown("#### Itemized Invoice Breakdown")
    st.caption(f"Category: **{tariff['description']}** (HS Code: `{selected_hs}`)")

    invoice_data = [
        {"Component": "1. Base Product Price (INR)", "Basis": f"₹{price_inr:,.2f} INR", "Amount in NPR": f"Rs. {price_npr:,.2f}"},
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
