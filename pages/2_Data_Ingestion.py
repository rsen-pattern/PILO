"""Page 2: Data Ingestion — Upload feed and supplementary data sources."""

import pandas as pd
import streamlit as st

from config.demo_data import DEMO_PRODUCTS
from core.doc_ingestor import extract_text
from core.feed_processor import (
    apply_column_mapping,
    build_column_mapping_ui,
    display_feed_preview,
    load_feed,
)
from core.scraper import batch_scrape_asins
from core.utils import calculate_completeness

st.set_page_config(page_title="PILO — Data Ingestion", page_icon="\U0001f4e5", layout="wide")
st.title("Data Ingestion")
st.caption("Upload your product feed and supplementary data to build PILO's enrichment layers.")

# ============================================================
# Layer 1: Primary Product Feed
# ============================================================
with st.expander("Layer 1: Primary Product Feed (Required)", expanded=True):
    st.subheader("Upload Product Feed")

    col1, col2 = st.columns([3, 1])
    with col1:
        uploaded_feed = st.file_uploader(
            "Upload CSV or Excel file",
            type=["csv", "xlsx", "xls"],
            key="feed_uploader",
        )
    with col2:
        st.markdown("**Or use demo data:**")
        load_demo = st.button("Load Demo Data", type="secondary")

    # Handle demo data
    if load_demo:
        df = pd.DataFrame(DEMO_PRODUCTS)
        st.session_state["feed_df"] = df
        st.session_state["column_mapping"] = {col: col for col in df.columns}
        st.success(f"Demo data loaded: {len(df)} KONG products")
        st.rerun()

    # Handle file upload
    if uploaded_feed is not None:
        try:
            raw_df = load_feed(uploaded_feed)
            st.success(f"File loaded: {uploaded_feed.name}")
            display_feed_preview(raw_df)

            st.divider()
            mapping = build_column_mapping_ui(raw_df)

            if st.button("Apply Mapping & Save Feed"):
                if "sku" not in mapping:
                    st.error("SKU / ASIN mapping is required.")
                else:
                    mapped_df = apply_column_mapping(raw_df, mapping)
                    st.session_state["feed_df"] = mapped_df
                    st.session_state["column_mapping"] = mapping
                    st.success("Feed mapped and saved!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error loading file: {e}")

    # Show current feed if loaded
    if st.session_state.get("feed_df") is not None:
        df = st.session_state["feed_df"]
        st.divider()
        st.subheader("Current Feed")
        st.dataframe(df.head(10), use_container_width=True)

        completeness = calculate_completeness(df)
        st.progress(completeness / 100)
        st.metric("Attribute Completeness", f"{completeness}%")

# ============================================================
# Layer 2: Web Scraping (Optional)
# ============================================================
with st.expander("Layer 2: Web Scraping (Optional)"):
    settings = st.session_state.get("settings", {})

    if not settings.get("scraping_enabled"):
        st.info(
            "Web scraping is not enabled. You can enable it in Settings and add your ScrapingBee API key, "
            "or skip this step."
        )
    elif not settings.get("scrapingbee_api_key"):
        st.warning("ScrapingBee API key not configured. You can add it in Settings, or skip this step.")
    else:
        scrape_option = st.radio(
            "Scraping Mode",
            ["Amazon Cross-Region Scraping", "Brand Website Scraping"],
        )

        if scrape_option == "Amazon Cross-Region Scraping":
            # Auto-detect ASINs from feed
            default_asins = ""
            if st.session_state.get("feed_df") is not None and "asin" in st.session_state["feed_df"].columns:
                asins_list = st.session_state["feed_df"]["asin"].dropna().unique().tolist()
                default_asins = "\n".join(str(a) for a in asins_list)

            asins_text = st.text_area(
                "ASINs (one per line)",
                value=default_asins,
                height=150,
            )

            regions = st.multiselect(
                "Regions to scrape",
                ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.com.au"],
                default=["amazon.com"],
            )

            if st.button("Scrape", type="primary"):
                asins = [a.strip() for a in asins_text.strip().split("\n") if a.strip()]
                if not asins:
                    st.error("Please enter at least one ASIN.")
                else:
                    with st.status("Scraping Amazon product pages..."):
                        progress = st.progress(0)
                        scraped_df = batch_scrape_asins(
                            settings["scrapingbee_api_key"],
                            asins,
                            regions,
                            progress_callback=lambda p: progress.progress(p),
                        )
                        st.session_state["scraped_df"] = scraped_df

                    if not scraped_df.empty:
                        st.success(f"Scraped {len(scraped_df)} records from {len(regions)} region(s)")
                        st.dataframe(scraped_df.head(), use_container_width=True)
                    else:
                        st.warning("No data was retrieved from scraping.")

        else:
            urls_text = st.text_area(
                "Brand website URLs (one per line)",
                height=150,
                placeholder="https://www.kongcompany.com/products/classic-kong",
            )

            if st.button("Scrape URLs", type="primary"):
                from core.scraper import scrape_brand_url

                urls = [u.strip() for u in urls_text.strip().split("\n") if u.strip()]
                if not urls:
                    st.error("Please enter at least one URL.")
                else:
                    brand_texts = []
                    with st.status(f"Scraping {len(urls)} URLs..."):
                        for url in urls:
                            text = scrape_brand_url(settings["scrapingbee_api_key"], url)
                            if text:
                                brand_texts.append({"url": url, "text": text})
                                st.caption(f"Scraped: {url} ({len(text)} chars)")

                    if brand_texts:
                        # Store as supplementary docs
                        for bt in brand_texts:
                            st.session_state["ingested_docs"].append({
                                "filename": bt["url"],
                                "type": "Brand Website",
                                "applicable_skus": ["All"],
                                "text": bt["text"],
                            })
                        st.success(f"Scraped {len(brand_texts)} URLs and added to document store.")

# ============================================================
# Layer 3: Client Document Ingestion (Optional)
# ============================================================
with st.expander("Layer 3: Client Document Ingestion (Optional)"):
    uploaded_docs = st.file_uploader(
        "Upload documents (PDF, DOCX, TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        key="doc_uploader",
    )

    if uploaded_docs:
        for doc_file in uploaded_docs:
            # Check if already ingested
            existing_names = [d["filename"] for d in st.session_state.get("ingested_docs", [])]
            if doc_file.name in existing_names:
                continue

            try:
                text = extract_text(doc_file)
                st.subheader(doc_file.name)
                st.text_area(
                    "Preview",
                    value=text[:500] + ("..." if len(text) > 500 else ""),
                    height=100,
                    disabled=True,
                    key=f"preview_{doc_file.name}",
                )

                col1, col2 = st.columns(2)
                with col1:
                    doc_type = st.selectbox(
                        "Document Type",
                        [
                            "Product Brochure",
                            "Spec Sheet",
                            "Catalogue",
                            "Safety Data Sheet",
                            "Brand Guidelines",
                            "Other",
                        ],
                        key=f"type_{doc_file.name}",
                    )
                with col2:
                    sku_scope = st.radio(
                        "Applicable SKUs",
                        ["All SKUs", "Specific SKUs"],
                        key=f"scope_{doc_file.name}",
                    )

                applicable_skus = ["All"]
                if sku_scope == "Specific SKUs" and st.session_state.get("feed_df") is not None:
                    sku_list = st.session_state["feed_df"]["sku"].tolist() if "sku" in st.session_state["feed_df"].columns else []
                    applicable_skus = st.multiselect(
                        "Select SKUs",
                        sku_list,
                        key=f"skus_{doc_file.name}",
                    )

                if st.button(f"Add {doc_file.name}", key=f"add_{doc_file.name}"):
                    st.session_state["ingested_docs"].append({
                        "filename": doc_file.name,
                        "type": doc_type,
                        "applicable_skus": applicable_skus,
                        "text": text,
                    })
                    st.success(f"Added {doc_file.name}")
                    st.rerun()

            except Exception as e:
                st.error(f"Error processing {doc_file.name}: {e}")

    # Show ingested docs
    if st.session_state.get("ingested_docs"):
        st.subheader("Ingested Documents")
        for i, doc in enumerate(st.session_state["ingested_docs"]):
            st.caption(f"**{doc['filename']}** — {doc['type']} — Applies to: {', '.join(doc['applicable_skus'])} — {len(doc['text'])} chars")

# ============================================================
# Layer 4: Cross-Retail Data Sources (Optional)
# ============================================================
with st.expander("Layer 4: Cross-Retail Data Sources (Optional)"):
    st.caption("Upload data from other retail channels (SKUVantage, SKULibrary, or other PIM exports)")

    uploaded_crossretail = st.file_uploader(
        "Upload CSV or Excel file",
        type=["csv", "xlsx"],
        key="crossretail_uploader",
    )

    if uploaded_crossretail is not None:
        try:
            cr_df = load_feed(uploaded_crossretail)
            st.success(f"Loaded: {len(cr_df)} rows, {len(cr_df.columns)} columns")
            st.dataframe(cr_df.head(), use_container_width=True)

            # Map SKU column
            cr_sku_col = st.selectbox(
                "Map SKU/identifier column",
                cr_df.columns.tolist(),
                key="cr_sku_col",
            )

            if st.button("Save Cross-Retail Data"):
                cr_df = cr_df.rename(columns={cr_sku_col: "sku"})
                st.session_state["crossretail_df"] = cr_df

                # Count new attribute columns
                feed_cols = set()
                if st.session_state.get("feed_df") is not None:
                    feed_cols = set(st.session_state["feed_df"].columns)
                new_cols = set(cr_df.columns) - feed_cols - {"sku"}
                st.success(f"{len(new_cols)} new attribute columns found from cross-retail source")
                st.rerun()

        except Exception as e:
            st.error(f"Error loading file: {e}")

# ============================================================
# Summary
# ============================================================
st.divider()
st.subheader("Data Ingestion Summary")

feed_status = "not loaded"
if st.session_state.get("feed_df") is not None:
    df = st.session_state["feed_df"]
    completeness = calculate_completeness(df)
    feed_status = f"{len(df)} SKUs loaded, {completeness}% attribute completeness"
    st.markdown(f"**Primary feed:** {feed_status}")
else:
    st.markdown("**Primary feed:** Not loaded")

scraped_df = st.session_state.get("scraped_df")
if scraped_df is not None and not scraped_df.empty:
    st.markdown(f"**Web scraping:** {len(scraped_df)} records scraped")
else:
    st.markdown("**Web scraping:** Not used")

docs = st.session_state.get("ingested_docs", [])
if docs:
    type_counts = {}
    for d in docs:
        t = d["type"]
        type_counts[t] = type_counts.get(t, 0) + 1
    type_str = ", ".join(f"{v} {k.lower()}(s)" for k, v in type_counts.items())
    st.markdown(f"**Client documents:** {len(docs)} files ingested ({type_str})")
else:
    st.markdown("**Client documents:** None")

cr_df = st.session_state.get("crossretail_df")
if cr_df is not None and not cr_df.empty:
    feed_cols = set(st.session_state.get("feed_df", pd.DataFrame()).columns)
    new_cols = set(cr_df.columns) - feed_cols - {"sku"}
    st.markdown(f"**Cross-retail data:** {len(new_cols)} new attributes from cross-retail source")
else:
    st.markdown("**Cross-retail data:** Not used")
