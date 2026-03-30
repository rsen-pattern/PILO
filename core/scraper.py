"""ScrapingBee integration and HTML parsing for Amazon product pages."""

import time

import pandas as pd
import requests
import streamlit as st
from bs4 import BeautifulSoup


REGION_CONFIGS = {
    "amazon.com": {"domain": "https://www.amazon.com/dp/", "country_code": "us"},
    "amazon.co.uk": {"domain": "https://www.amazon.co.uk/dp/", "country_code": "gb"},
    "amazon.de": {"domain": "https://www.amazon.de/dp/", "country_code": "de"},
    "amazon.com.au": {"domain": "https://www.amazon.com.au/dp/", "country_code": "au"},
}


def scrape_amazon_product(api_key, asin, region="amazon.com"):
    """Scrape an Amazon product page using ScrapingBee.

    Returns parsed product data dict or None on failure.
    """
    config = REGION_CONFIGS.get(region)
    if not config:
        return None

    url = f"{config['domain']}{asin}"

    try:
        response = requests.get(
            "https://app.scrapingbee.com/api/v1/",
            params={
                "api_key": api_key,
                "url": url,
                "render_js": "true",
                "premium_proxy": "true",
                "country_code": config["country_code"],
            },
            timeout=30,
        )
        response.raise_for_status()
        return parse_amazon_html(response.text, asin, region)
    except Exception as e:
        st.warning(f"Failed to scrape {asin} from {region}: {e}")
        return None


def parse_amazon_html(html, asin, region):
    """Extract product data from Amazon HTML."""
    soup = BeautifulSoup(html, "lxml")
    data = {"asin": asin, "source_region": region}

    # Title
    title_el = soup.find("span", {"id": "productTitle"})
    if title_el:
        data["scraped_title"] = title_el.get_text(strip=True)

    # Bullet points
    bullets_el = soup.find("div", {"id": "feature-bullets"})
    if bullets_el:
        bullets = bullets_el.find_all("span", class_="a-list-item")
        for i, b in enumerate(bullets[:5]):
            text = b.get_text(strip=True)
            if text:
                data[f"scraped_bullet_{i+1}"] = text

    # Description
    desc_el = soup.find("div", {"id": "productDescription"})
    if desc_el:
        data["scraped_description"] = desc_el.get_text(strip=True)

    # Product information table
    info_table = soup.find("table", {"id": "productDetails_techSpec_section_1"})
    if not info_table:
        info_table = soup.find("table", {"id": "productDetails_detailBullets_sections1"})

    if info_table:
        rows = info_table.find_all("tr")
        for row in rows:
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = th.get_text(strip=True).lower().replace(" ", "_")
                val = td.get_text(strip=True)
                data[f"scraped_attr_{key}"] = val

    # Technical details section (alternate format)
    tech_section = soup.find("div", {"id": "detailBullets_feature_div"})
    if tech_section:
        items = tech_section.find_all("span", class_="a-list-item")
        for item in items:
            spans = item.find_all("span")
            if len(spans) >= 2:
                key = spans[0].get_text(strip=True).rstrip(":").lower().replace(" ", "_")
                val = spans[1].get_text(strip=True)
                if key and val:
                    data[f"scraped_attr_{key}"] = val

    return data


def scrape_brand_url(api_key, url):
    """Scrape a brand website URL and extract text content."""
    try:
        response = requests.get(
            "https://app.scrapingbee.com/api/v1/",
            params={
                "api_key": api_key,
                "url": url,
                "render_js": "true",
            },
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        # Remove script/style elements
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        st.warning(f"Failed to scrape {url}: {e}")
        return None


def batch_scrape_asins(api_key, asins, regions, progress_callback=None):
    """Scrape multiple ASINs across multiple regions.

    Returns a DataFrame of scraped data.
    """
    results = []
    total = len(asins) * len(regions)
    done = 0

    for asin in asins:
        asin = asin.strip()
        if not asin:
            continue
        for region in regions:
            data = scrape_amazon_product(api_key, asin, region)
            if data:
                results.append(data)
            done += 1
            if progress_callback:
                progress_callback(done / total)
            time.sleep(1)  # Rate limit

    if results:
        return pd.DataFrame(results)
    return pd.DataFrame()
