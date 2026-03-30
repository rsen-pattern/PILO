"""Page 2: Data Ingestion — 5-layer data loading with AI research and external scraping."""

import pandas as pd
import streamlit as st
from core.theme import inject_pattern_css, pattern_page_header, pattern_sidebar
from core.feed_processor import load_feed, display_feed_preview, build_column_mapping_ui, apply_column_mapping
from core.doc_ingestor import extract_text
from core.scraper import scrape_amazon_asins, scrape_brand_url
from config.demo_data import DEMO_PRODUCTS, DEMO_RESEARCH

inject_pattern_css()
pattern_sidebar()
pattern_page_header("Data Ingestion", "Upload product data from multiple sources")

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 1 — Primary Product Feed
# ═══════════════════════════════════════════════════════════════════════════
st.header("Layer 1: Primary Product Feed")
st.caption("Upload your product feed (.csv, .xlsx, .xls) or load demo data.")

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Load KONG Demo Data (16 products)", type="secondary"):
        demo_df = pd.DataFrame(DEMO_PRODUCTS)
        st.session_state["feed_df"] = demo_df
        st.session_state["feed_format"] = "standard"
        st.session_state["feed_metadata"] = {
            "format": "standard", "filename": "demo_data.csv",
            "rows": len(demo_df), "columns": len(demo_df.columns),
        }
        # Pre-load demo research
        st.session_state["research_results"] = DEMO_RESEARCH
        st.success(f"Loaded {len(DEMO_PRODUCTS)} KONG products with pre-computed research.")
        st.rerun()

with col1:
    uploaded = st.file_uploader(
        "Upload Product Feed", type=["csv", "xlsx", "xls"],
        key="feed_upload",
    )

if uploaded:
    try:
        df, fmt, metadata = load_feed(uploaded)
        st.session_state["feed_df"] = df
        st.session_state["feed_format"] = fmt
        st.session_state["feed_metadata"] = metadata
        st.success(f"Loaded {len(df)} products ({fmt})")
    except Exception as e:
        st.error(f"Error loading file: {e}")

feed_df = st.session_state.get("feed_df")
if feed_df is not None:
    display_feed_preview(feed_df, st.session_state.get("feed_format"))

    with st.expander("Column Mapping", expanded=False):
        mapping = build_column_mapping_ui(feed_df)
        if st.button("Apply Mapping"):
            mapped_df = apply_column_mapping(feed_df, mapping)
            st.session_state["feed_df"] = mapped_df
            st.session_state["column_mapping"] = mapping
            st.success("Column mapping applied.")
            st.rerun()

    # Completeness
    from core.utils import calculate_completeness
    completeness = calculate_completeness(feed_df)
    st.metric("Attribute Completeness", f"{completeness:.0f}%")
    st.progress(completeness / 100)

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 2 — Client Document Ingestion
# ═══════════════════════════════════════════════════════════════════════════
st.header("Layer 2: Client Documents")
st.caption("Upload brand guidelines, spec sheets, brochures (PDF, DOCX, TXT).")

doc_files = st.file_uploader(
    "Upload Documents", type=["pdf", "docx", "txt"],
    accept_multiple_files=True, key="doc_upload",
)

if doc_files:
    ingested = st.session_state.get("ingested_docs", [])
    skus = feed_df["sku"].tolist() if feed_df is not None and "sku" in feed_df.columns else []

    for doc_file in doc_files:
        if any(d["filename"] == doc_file.name for d in ingested):
            continue

        text = extract_text(doc_file)
        if text:
            col1, col2 = st.columns(2)
            with col1:
                doc_type = st.selectbox(
                    f"Type: {doc_file.name}",
                    ["Brochure", "Spec Sheet", "Catalogue", "SDS", "Brand Guidelines"],
                    key=f"doctype_{doc_file.name}",
                )
            with col2:
                scope_options = ["All"] + skus
                scope = st.multiselect(
                    f"Applicable SKUs: {doc_file.name}",
                    scope_options, default=["All"],
                    key=f"docscope_{doc_file.name}",
                )

            ingested.append({
                "filename": doc_file.name,
                "type": doc_type,
                "text": text,
                "applicable_skus": scope,
            })

    st.session_state["ingested_docs"] = ingested
    st.success(f"{len(ingested)} document(s) ingested.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 3 — Cross-Retail / Pattern Tool Data
# ═══════════════════════════════════════════════════════════════════════════
st.header("Layer 3: Cross-Retail & Pattern Tools")

tab_cr, tab_predict, tab_shelf = st.tabs(["Cross-Retail Upload", "Predict Keywords", "Shelf Scores"])

with tab_cr:
    st.caption("Upload SKUVantage, SKULibrary, or similar cross-retail data.")
    cr_file = st.file_uploader("Upload Cross-Retail Data", type=["csv", "xlsx"], key="cr_upload")
    if cr_file:
        try:
            cr_df = pd.read_csv(cr_file) if cr_file.name.endswith(".csv") else pd.read_excel(cr_file)
            st.session_state["crossretail_df"] = cr_df
            st.success(f"Loaded {len(cr_df)} cross-retail rows.")
            st.dataframe(cr_df.head(5), use_container_width=True)
        except Exception as e:
            st.error(f"Error: {e}")

with tab_predict:
    if st.session_state.get("predict_integration"):
        st.caption("Upload keyword export from Pattern's Predict tool.")
        pred_file = st.file_uploader("Upload Predict Export", type=["csv", "xlsx"], key="pred_upload")
        if pred_file:
            from config.pattern_tool_schemas import parse_predict_export
            try:
                pred_df = pd.read_csv(pred_file) if pred_file.name.endswith(".csv") else pd.read_excel(pred_file)
                keywords = parse_predict_export(pred_df)
                st.session_state["predict_keywords_raw"] = keywords
                st.success(f"Imported {len(keywords)} keywords from Predict.")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("Enable Predict integration in Control Centre to use this feature.")

with tab_shelf:
    if st.session_state.get("shelf_integration"):
        st.caption("Upload compliance export from Pattern's Shelf tool.")
        shelf_file = st.file_uploader("Upload Shelf Export", type=["csv", "xlsx"], key="shelf_upload")
        if shelf_file:
            from config.pattern_tool_schemas import parse_shelf_export
            try:
                shelf_df = pd.read_csv(shelf_file) if shelf_file.name.endswith(".csv") else pd.read_excel(shelf_file)
                scores = parse_shelf_export(shelf_df)
                st.session_state["shelf_scores"] = scores
                st.success(f"Imported Shelf scores for {len(scores)} products.")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.info("Enable Shelf integration in Control Centre to use this feature.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 4 — Web Scraping + AI Research
# ═══════════════════════════════════════════════════════════════════════════
st.header("Layer 4: Web Scraping & AI Research")

research_method = st.session_state.get("research_method", "AI Deep Research")

if "Web Scraping" in research_method or research_method == "Both":
    with st.expander("Web Scraping (ScrapingBee)", expanded=False):
        scrape_mode = st.radio(
            "Scraping Mode",
            ["Amazon ASINs from feed", "Brand website URLs", "Custom URLs"],
            key="scrape_mode", horizontal=True,
        )

        if scrape_mode == "Amazon ASINs from feed":
            region = st.selectbox("Amazon Region", ["AU", "US", "UK", "DE"], key="amz_region")
            if st.button("Scrape Amazon Listings", key="scrape_amz"):
                if feed_df is not None and "asin" in feed_df.columns:
                    api_key = st.session_state.get("scrapingbee_api_key", "")
                    if not api_key:
                        st.error("ScrapingBee API key required.")
                    else:
                        asins = feed_df["asin"].dropna().tolist()
                        with st.spinner(f"Scraping {len(asins)} ASINs..."):
                            scraped = scrape_amazon_asins(asins, api_key, region.lower())
                        st.session_state["scraped_df"] = pd.DataFrame(scraped)
                        st.success(f"Scraped {len(scraped)} products.")
                else:
                    st.warning("No ASIN column found in feed.")

        elif scrape_mode == "Brand website URLs":
            urls_text = st.text_area("Paste URLs (one per line)", key="brand_urls")
            if st.button("Scrape Brand URLs", key="scrape_brand"):
                api_key = st.session_state.get("scrapingbee_api_key", "")
                if not api_key:
                    st.error("ScrapingBee API key required.")
                else:
                    urls = [u.strip() for u in urls_text.split("\n") if u.strip()]
                    scraped_data = []
                    progress = st.progress(0)
                    for i, url in enumerate(urls):
                        text = scrape_brand_url(url, api_key)
                        scraped_data.append({"url": url, "text": text[:5000] if text else ""})
                        progress.progress((i + 1) / len(urls))
                    st.session_state["scraped_brand_data"] = scraped_data
                    st.success(f"Scraped {len(scraped_data)} URLs.")

        elif scrape_mode == "Custom URLs":
            urls_text = st.text_area("Paste product page URLs (one per line)", key="custom_urls")
            if st.button("Scrape Custom URLs", key="scrape_custom"):
                api_key = st.session_state.get("scrapingbee_api_key", "")
                if not api_key:
                    st.error("ScrapingBee API key required.")
                else:
                    urls = [u.strip() for u in urls_text.split("\n") if u.strip()]
                    scraped_data = []
                    progress = st.progress(0)
                    for i, url in enumerate(urls):
                        text = scrape_brand_url(url, api_key)
                        scraped_data.append({"url": url, "text": text[:5000] if text else ""})
                        progress.progress((i + 1) / len(urls))
                    st.session_state["scraped_custom_data"] = scraped_data
                    st.success(f"Scraped {len(scraped_data)} URLs.")

if "AI Deep Research" in research_method or research_method == "Both":
    with st.expander("AI Deep Research", expanded=False):
        st.caption("Use AI to research products when web scraping isn't available.")
        conf_thresh = st.session_state.get("confidence_threshold", 0.7)
        st.info(f"Results below {conf_thresh:.0%} confidence will be flagged for review.")

        if feed_df is not None and "sku" in feed_df.columns:
            research_skus = feed_df["sku"].tolist()
            existing_research = st.session_state.get("research_results", {})
            unresearched = [s for s in research_skus if s not in existing_research]

            st.write(f"**{len(existing_research)}** products already researched, "
                     f"**{len(unresearched)}** remaining.")

            if st.button(f"Research {len(unresearched)} Products", key="run_research",
                         disabled=len(unresearched) == 0):
                api_key = st.session_state.get("bifrost_api_key", "")
                if not api_key:
                    st.error("Bifrost API key required.")
                else:
                    from core.ai_researcher import create_research_client, batch_research
                    client, model = create_research_client({
                        "bifrost_api_key": api_key,
                        "bifrost_base_url": st.session_state.get("bifrost_base_url", "https://bifrost.pattern.com"),
                        "model": st.session_state.get("model", "anthropic/claude-sonnet-4-6"),
                    })

                    products = []
                    for s in unresearched:
                        row = feed_df[feed_df["sku"] == s].iloc[0]
                        products.append(row.to_dict())

                    progress = st.progress(0, text="Starting research...")
                    status = st.empty()

                    def callback(sku, idx, total, result):
                        progress.progress(idx / total, text=f"Researching {sku} ({idx}/{total})")
                        badge = "🟢" if result["confidence"] >= 0.8 else "🟡" if result["confidence"] >= 0.5 else "🔴"
                        status.caption(f"{badge} {sku}: confidence {result['confidence']:.2f}")

                    new_results = batch_research(client, model, products, dict(st.session_state), callback)
                    existing_research.update(new_results)
                    st.session_state["research_results"] = existing_research
                    progress.progress(1.0, text="Research complete!")
                    st.success(f"Researched {len(new_results)} products.")

            # Show research summary
            if existing_research:
                summary_cols = st.columns(4)
                high = sum(1 for r in existing_research.values() if r.get("confidence", 0) >= 0.8)
                med = sum(1 for r in existing_research.values() if 0.5 <= r.get("confidence", 0) < 0.8)
                low = sum(1 for r in existing_research.values() if r.get("confidence", 0) < 0.5)
                with summary_cols[0]:
                    st.metric("Total Researched", len(existing_research))
                with summary_cols[1]:
                    st.metric("High Confidence", f"🟢 {high}")
                with summary_cols[2]:
                    st.metric("Medium Confidence", f"🟡 {med}")
                with summary_cols[3]:
                    st.metric("Low Confidence", f"🔴 {low}")
        else:
            st.warning("Load a product feed first to enable AI research.")

st.divider()

# ═══════════════════════════════════════════════════════════════════════════
# LAYER 5 — External Website Scraping
# ═══════════════════════════════════════════════════════════════════════════
st.header("Layer 5: External Website Scraping")
st.caption("Scrape non-client sites (resellers, distributors). Data tagged as lowest trust.")

ext_urls = st.text_area(
    "Paste external URLs (one per line)",
    placeholder="e.g. https://competitor-site.com/product-123",
    key="ext_urls",
)
if st.button("Scrape External Sites", key="scrape_ext"):
    api_key = st.session_state.get("scrapingbee_api_key", "")
    if not api_key:
        st.error("ScrapingBee API key required.")
    elif ext_urls.strip():
        urls = [u.strip() for u in ext_urls.split("\n") if u.strip()]
        scraped = []
        progress = st.progress(0)
        for i, url in enumerate(urls):
            text = scrape_brand_url(url, api_key)
            scraped.append({"url": url, "text": text[:5000] if text else ""})
            progress.progress((i + 1) / len(urls))
        st.session_state["external_scraped_data"] = scraped
        st.success(f"Scraped {len(scraped)} external URLs. Tagged as low-trust source.")

# ── Navigation ──
st.divider()
if feed_df is not None:
    st.success(f"Feed loaded: {len(feed_df)} products. Proceed to Enrichment.")
else:
    st.info("Upload a product feed or load demo data to continue.")
