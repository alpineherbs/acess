import streamlit as st
import json
import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, Tuple
from urllib.parse import urlparse, unquote

st.set_page_config(page_title="Indo-Nepal Import Cost Agent", page_icon="🇳🇵", layout="wide")

# =========================================================
# 1. NEPAL CUSTOMS TARIFF SCHEDULE (HS CODES)
# =========================================================
EXCHANGE_RATE_INR_TO_NPR = 1.62   # Official peg 1.60 + ~1.25% banking/card markup
FREIGHT_PER_KG_NPR = 550.0        # Courier express per kg (India to KTM)
INSURANCE_RATE = 0.01             # 1% standard cargo transit insurance
CLEARANCE_FEE_NPR = 350.0         # Border handling and documentation fee

HS_DATABASE: Dict[str, Dict] = {
    "8471.30": {"description": "Laptops & Portable Computers", "customs": 0.01, "excise": 0.00, "vat": 0.13},
    "8517.13": {"description": "Smartphones / Mobile Handsets", "customs": 0.05, "excise": 0.00, "vat": 0.13},
    "8518.30": {"description": "Headphones / Earphones / TWS Earbuds / Speakers", "customs": 0.15, "excise": 0.00, "vat": 0.13},
    "9102.12": {"description": "Smartwatches & Wristwatches", "customs": 0.15, "excise": 0.00, "vat": 0.13},
    "6109.10": {"description": "Western Apparel / T-shirts / Jeans / Hoodies", "customs": 0.20, "excise": 0.00, "vat": 0.13},
    "6204.42": {"description": "Ethnic Wear / Sarees / Kurtas / Lehengas", "customs": 0.15, "excise": 0.00, "vat": 0.13},
    "6404.11": {"description": "Footwear / Sports Shoes / Sneakers / Heels", "customs": 0.20, "excise": 0.00, "vat": 0.13},
    "3304.99": {"description": "Cosmetics / Skincare / Makeup / Perfumes", "customs": 0.15, "excise": 0.05, "vat": 0.13},
    "2106.10": {"description": "Health Supplements / Whey Protein / Vitamins", "customs": 0.15, "excise": 0.00, "vat": 0.13},
    "8509.40": {"description": "Kitchen & Home Appliances (Mixers, Air Fryers)", "customs": 0.15, "excise": 0.00, "vat": 0.13},
    "4901.99": {"description": "Printed Books & Educational Literature", "customs": 0.00, "excise": 0.00, "vat": 0.00},
    "8528.72": {"description": "Televisions & Display Monitors", "customs": 0.20, "excise": 0.05, "vat": 0.13},
    "9999.99": {"description": "General Merchandise / Miscellaneous", "customs": 0.15, "excise": 0.00, "vat": 0.13}
}

# =========================================================
# 2. ACCURATE MULTI-PLATFORM SCRAPER
# =========================================================
def extract_slug_title(url: str) -> str:
    """Extracts fallback product title from the URL path."""
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


def scrape_product(url: str, api_key: str) -> Tuple[str, float, str]:
    """Scrapes Amazon, Flipkart, and others without EMI or coupon errors."""
    domain = urlparse(url).netloc.lower()
    platform = "Indian E-Commerce"
    if "amazon" in domain:
        platform = "Amazon India"
    elif "flipkart" in domain:
        platform = "Flipkart"
    elif "myntra" in domain:
        platform = "Myntra"

    title = extract_slug_title(url)
    price = 0.0
    html = ""

    # Priority 1: ScraperAPI if key provided
    if api_key and len(api_key.strip()) > 10:
        try:
            r = requests.get(f"http://api.scraperapi.com?api_key={api_key.strip()}&url={url}", timeout=25)
            if r.status_code == 200:
                html = r.text
        except Exception:
            pass

    # Priority 2: Direct request with realistic browser headers
    if not html:
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
                "Accept-Language": "en-IN,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            }
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code == 200 and "Robot Check" not in r.text:
                html = r.text
        except Exception:
            pass

    # Priority 3: Fallback proxy
    if not html or "Robot Check" in html:
        try:
            r = requests.get(f"https://r.jina.ai/{url}", headers={"User-Agent": "Mozilla/5.0"}, timeout=12)
            if r.status_code == 200:
                html = r.text
        except Exception:
            pass

    if html:
        soup = BeautifulSoup(html, "html.parser")

        # 1. Parse JSON-LD Schema (Common on Amazon, Flipkart, Myntra)
        try:
            for s in soup.find_all("script", {"type": "application/ld+json"}):
                if not s.string:
                    continue
                try:
                    data = json.loads(s.string)
                    items = data if isinstance(data, list) else [data]
                    for it in items:
                        if it.get("@type") == "Product" or "Product" in str(it.get("@type")):
                            if not title and it.get("name"):
                                title = str(it.get("name")).strip()
                            offers = it.get("offers", {})
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

        # 2. Amazon Specific DOM
        if "Amazon" in platform:
            if not title:
                t_elem = soup.find("span", {"id": "productTitle"})
                if t_elem:
                    title = t_elem.get_text(strip=True)

            if price == 0.0:
                p_elem = soup.find("span", {"class": "a-price-whole"})
                if p_elem:
                    clean = re.sub(r"[^\d.]", "", p_elem.get_text())
                    if clean:
                        price = float(clean)

            if price == 0.0:
                core_p = soup.find("div", {"id": "corePriceDisplay_desktop_feature_div"}) or soup.find("div", {"id": "corePrice_feature_div"})
                if core_p:
                    off_p = core_p.find("span", {"class": "a-offscreen"})
                    if off_p:
                        clean = re.sub(r"[^\d.]", "", off_p.get_text())
                        if clean:
                            price = float(clean)

        # 3. Flipkart Specific DOM
        elif "Flipkart" in platform:
            if not title:
                fk_t = soup.find("h1", {"class": "VU-ZEz"}) or soup.find("span", {"class": "B_NuCI"}) or soup.find("h1", {"class": "_6EBuvd"})
                if fk_t:
                    title = fk_t.get_text(strip=True)
                elif soup.title and "Price in India" in soup.title.string:
                    clean = re.sub(r"\s*(?:Price in India|Buy .*|Online at Flipkart).*$", "", soup.title.string, flags=re.I).strip()
                    if clean:
                        title = clean

            if price == 0.0:
                fk_p = soup.find("div", {"class": "Nx9bqj CxhGGd"}) or soup.find("div", {"class": "_30jeq3 _16Jk6d"}) or soup.find("div", {"class": "Nx9bqj"}) or soup.find("div", {"class": "_30jeq3"})
                if fk_p:
                    clean = re.sub(r"[^\d.]", "", fk_p.get_text())
                    if clean:
                        price = float(clean)

        # 4. Filtered Text Fallback (Ignores EMI, coupons, delivery)
        if price == 0.0:
            lines = html.splitlines()
            for line in lines:
                l_lower = line.lower()
                if any(bad in l_lower for bad in ["emi", "save", "coupon", "discount", "off", "delivery", "cashback", "per month"]):
                    continue
                if any(c in line for c in ["₹", "INR", "Rs."]):
                    matches = re.findall(r"(?:₹|INR|\bRs\.?)\s*([0-9]{1,3}(?:,[0-9]{2,3})*(?:\.[0-9]{2})?)", line)
                    if matches:
                        for m in matches:
                            val = float(m.replace(",", ""))
                            if val >= 199.0:
                                price = val
                                break
                if price > 0.0:
                    break

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
    if any(k in t for k in ["smartwatch", "watch", "smart band", "fitness band"]):
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
    if any(k in t for k in ["serum", "lotion", "cream", "lipstick", "perfume", "shampoo", "sunscreen"]):
        return "3304.99"
    if any(k in t for k in ["whey", "protein", "creatine", "vitamin", "bcaa", "supplement"]):
        return "2106.10"
    if any(k in t for k in ["book", "novel", "paperback"]):
        return "4901.99"
    return "9999.99"


# =========================================================
# 3. STREAMLIT APP STATE MANAGEMENT
# =========================================================
if "search_count" not in st.session_state:
    st.session_state.search_count = 0
if "current_title" not in st.session_state:
    st.session_state.current_title = "Puma Men's Running Shoes"
if "current_price" not in st.session_state:
    st.session_state.current_price = 3499.0
if "current_platform" not in st.session_state:
    st.session_state.current_platform = "Amazon India"
if "status_text" not in st.session_state:
    st.session_state.status_text = ""

# Sidebar Settings
with st.sidebar:
    st.header("⚙️ Settings")
    api_key_input = st.text_input(
        "ScraperAPI Key (Optional):",
        value="",
        type="password",
        placeholder="Paste scraperapi.com key...",
        help="Ensures 100% unblocked scraping for Amazon and Flipkart."
    )
    st.markdown("---")
    st.markdown("**Exchange Rate:** 1 INR = 1.62 NPR")
    st.markdown("**Freight:** Rs. 550 / kg")
    st.markdown("**Nepal VAT:** 13%")

st.title("🇳🇵 Indo-Nepal E-Commerce Import Cost Agent")
st.markdown("Search products from **Amazon India, Flipkart, Myntra & Nykaa** to calculate the complete landed cost delivered to Nepal.")

col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Product Search")
    url_val = st.text_input(
        "Paste Indian Product Link:",
        placeholder="https://www.amazon.in/dp/... or https://www.flipkart.com/..."
    )

    search_button = st.button("🔍 Search Product", type="primary", use_container_width=True)

    # When search is clicked, fetch data and INCREMENT search_count to force input boxes to update
    if search_button:
        if url_val.strip():
            with st.spinner("Extracting fresh product details..."):
                t, p, plat = scrape_product(url_val, api_key_input)
                if t:
                    st.session_state.current_title = t
                if p > 0:
                    st.session_state.current_price = float(p)
                st.session_state.current_platform = plat

                if p > 0:
                    st.session_state.status_text = f"✅ Extracted from {plat}! Price: ₹{p:,.2f}"
                else:
                    st.session_state.status_text = f"ℹ️ Title found from {plat}. Please verify the price below."

                # Increment version key so inputs re-render with the new price
                st.session_state.search_count += 1
                st.rerun()
        else:
            st.warning("⚠️ Please paste a link first.")

    if st.session_state.status_text:
        st.info(st.session_state.status_text)

    st.markdown("---")
    st.markdown("##### Product Details")

    # DYNAMIC KEYS: key changes on every search so the widget NEVER gets stuck on old values
    v_key = st.session_state.search_count
    prod_name = st.text_input("Product Title / Name:", value=st.session_state.current_title, key=f"title_{v_key}")
    price_inr = st.number_input("Price in India (₹ INR):", min_value=1.0, value=float(st.session_state.current_price), step=50.0, key=f"price_{v_key}")

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

    # --- Landed Cost Calculation Engine ---
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
