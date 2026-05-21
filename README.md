# PILO — Pattern Intelligence Listing Optimisation

AI-powered product content engine that generates optimised titles, bullet
points, descriptions, keywords, supplemental attributes, and special features
for marketplace listings at scale.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration

Set API keys via Streamlit secrets (`.streamlit/secrets.toml`) or environment
variables:

```
BIFROST_API_KEY=your-key-here
SCRAPINGBEE_API_KEY=your-key-here  # optional, only needed for web scraping
```

## Workflow

1. **Control Centre** — Configure marketplace, brand, AI model, output format
2. **Data Ingestion** — Upload feed + documents + cross-retail data + AI research
3. **Enrichment** — Merge all data layers with source provenance tracking
4. **Content Generation** — Run 7-step prompt chain per SKU × marketplace
5. **QA Review** — Human review, inline editing, approve/reject with audit trail
6. **Export** — Marketplace-formatted files, comparison output, PXM JSON, ZIP
7. **Cost Dashboard** — Token usage and cost breakdown by step and marketplace

## Supported Marketplaces

Amazon AU, Amazon US, Amazon UK, Walmart US, Woolworths AU, eBay AU,
Google Shopping / UCP

## Demo Mode

Click "Load KONG Demo Data" on the Data Ingestion page to load 16 sample
pet products with pre-computed AI research and ~25% attribute completeness.

## Known Behaviours

- **Supported feed formats**: `.csv`, `.xlsx`, `.xls`, and `.xlsm`
  (macro-enabled). For `.xlsm` files, VBA macros are ignored and only the
  cell data is read — output exports remain `.xlsx`/`.csv`.

- **Web scraping**: ScrapingBee columns (`scraped_title`, `scraped_bullet_N`
  etc) are automatically normalised to standard field names during enrichment.

- **Confidence threshold**: AI research below the threshold is still used in
  generation but is flagged in prompts so the model deprioritises it.
  It does not exclude the research entirely.

- **Batch size**: The UI caps generation at 50 SKUs per run. For larger
  catalogues use the Resume Previous Run feature — complete runs in
  batches and resume if interrupted.

- **Cache files**: Generation progress is saved to `.pilo_cache/*.jsonl`
  (gitignored). These files contain product data — do not share them.

- **Temperature**: All generation runs at 0.1 regardless of the temperature
  slider. The slider is reserved for future research steps.

## Tech Stack

Python 3.10+ / Streamlit / Anthropic Claude via Bifrost /
ScrapingBee (optional) / pandas / openpyxl / xlsxwriter /
PyPDF2 / python-docx / BeautifulSoup

## Team

Alison Ong, Jefferson Chen, Rahul Sengupta — Pattern eCommerce
