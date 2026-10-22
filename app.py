# Replace YOUR_SCRAPERAPI_KEY with your actual free API key from scraperapi.com
SCRAPER_API_KEY = 

def scrape_indian_url(url: str) -> Tuple[str, float, float]:
    """Fetches product title and price through a proxy that bypasses Amazon/Flipkart bot protection."""
    extracted_title = ""
    extracted_price = 0.0
    extracted_weight = 1.0

    # If you haven't added an API key yet, it attempts a direct fetch with realistic browser headers
    if SCRAPER_API_KEY == "YOUR_SCRAPERAPI_KEY":
        proxy_url = url
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
    else:
        # Routes through proxy to bypass Amazon bot blocks
        proxy_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={url}"
        headers = {}

    try:
        response = requests.get(proxy_url, headers=headers, timeout=25)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            # 1. Amazon Parser
            t_tag = soup.find("span", {"id": "productTitle"})
            if t_tag:
                extracted_title = t_tag.get_text(strip=True)

            p_tag = soup.find("span", {"class": "a-price-whole"})
            if p_tag:
                cleaned_price = re.sub(r"[^\d.]", "", p_tag.get_text())
                if cleaned_price:
                    extracted_price = float(cleaned_price)

            # 2. Flipkart Parser (Fallback)
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

    except Exception as e:
        print(f"Scraping error: {e}")

    return extracted_title, extracted_price, extracted_weight
