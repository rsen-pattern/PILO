# PILO — Pattern Intelligence Listing Optimisation

AI-powered product content engine that generates optimised titles, bullet points, descriptions, and supplemental attributes for marketplace listings at scale.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Configuration

Set your API keys via environment variables or Streamlit secrets:

```bash
export ANTHROPIC_API_KEY="your-key-here"
export SCRAPINGBEE_API_KEY="your-key-here"  # optional
```

Or configure them in the Settings page of the app.

## Workflow

1. **Settings** — Configure brand, category, marketplace, and API keys
2. **Data Ingestion** — Upload product feed + supplementary data (or use "Load Demo Data")
3. **Enrichment** — Review merged/enriched data from all sources
4. **Content Generation** — Run Claude AI to generate optimised content
5. **QA Review** — Human review and edit generated content
6. **Export** — Download marketplace-formatted files (Amazon, Walmart, Woolworths, Google Shopping)

## Demo

Click "Load Demo Data" on the Data Ingestion page to load 5 sample KONG pet products with sparse attributes (~28% completeness) and see the full workflow in action.

## Tech Stack

- Python 3.10+ / Streamlit
- Anthropic Claude API (content generation)
- ScrapingBee (optional web scraping)
- pandas / openpyxl / xlsxwriter (data processing & export)
- PyPDF2 / python-docx (document ingestion)
