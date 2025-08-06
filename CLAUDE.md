# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive web scraper and price analysis tool for onderdelenlijn.nl, a Dutch auto parts marketplace. The system consists of three main components that work together to scrape, analyze, and display competitive pricing data for automotive parts.

## Architecture

### Core Components

1. **OnderdelenLijnScraper** (`onderdelenlijn_scraper.py`): The main Selenium-based scraper that handles:
   - ASP.NET Web Forms navigation with JavaScript-based pagination
   - License plate input and category discovery
   - Dynamic product specification extraction using CSS selectors
   - Data flattening (specifications dictionary → individual `spec_` columns)

2. **PriceAnalyzer** (`price_analysis.py`): Market analysis engine providing:
   - Statistical analysis per product category
   - Pricing recommendations (conservative/market-conform/premium)
   - Competitive analysis and supplier comparison
   - Category-based filtering and reporting

3. **Flask Web Dashboard** (`app.py`): Multi-threaded web application featuring:
   - Real-time scraping progress tracking via sessions
   - Interactive category selection and smart search
   - Per-category price analysis with visualization
   - CSV export with flattened specification data

### Data Flow

```
License Plate + Part Name → Category Discovery → Multi-threaded Scraping → 
Specification Extraction → Price Analysis → Interactive Dashboard → CSV Export
```

The scraper extracts comprehensive metadata including product IDs, URLs, specifications (dynamically detected), prices, match quality, supplier info, and technical details, then flattens nested specifications into individual columns for analysis.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Application
```bash
# Start the Flask web dashboard (recommended)
python3 app.py
# Access at http://localhost:5000

# Run standalone scraper
python3 onderdelenlijn_scraper.py

# Example programmatic usage
python3 example_usage.py
```

### Testing Components
```bash
# Test price analysis module
python3 -c "from price_analysis import PriceAnalyzer; print('✅ PriceAnalyzer working')"

# Test scraper initialization
python3 -c "from onderdelenlijn_scraper import OnderdelenLijnScraper; print('✅ Scraper working')"

# Test web app imports
python3 -c "from app import app; print('✅ Flask app working')"
```

### Railway.app Deployment
```bash
# Build and test Docker container locally
docker build -t onderdelenlijn-scraper .
docker run -p 5000:5000 -e PORT=5000 onderdelenlijn-scraper

# Deploy to Railway (after pushing to GitHub)
# 1. Connect GitHub repo to Railway.app
# 2. Railway auto-detects Dockerfile and railway.json
# 3. Deployment happens automatically with gunicorn + Chrome in container
```

## Key Implementation Details

### Selenium Configuration
The scraper uses webdriver-manager for automatic Chrome driver management with specific configurations for ASP.NET Web Forms compatibility, including cookie banner removal and JavaScript-based navigation handling.

### Product Data Structure
Products contain both flat fields (title, price, supplier) and nested `specificaties` dict that gets flattened to `spec_*` columns. The `scrape_product_info()` method dynamically detects specifications using `div.description p span.item` containers with adjacent sibling selectors.

### Session Management
Flask uses threading for concurrent scraping sessions, with `ScrapingSession` objects tracking progress, status, and results. Sessions are identified by unique IDs combining license plate, part name, and timestamp.

### Price Analysis Categories
The `PriceAnalyzer` can filter products by `soort_onderdeel` field and provides category-specific analysis. The `filter_by_category()` method returns new analyzer instances for isolated analysis.

### API Endpoints
- `/api/categories` - Smart category discovery with search term expansion
- `/api/scrape` - Start threaded scraping with selected categories
- `/api/status/<session_id>` - Real-time progress monitoring
- `/api/results/<session_id>` - Formatted product results
- `/api/price-analysis/<session_id>?category=<name>` - Market analysis
- `/api/competitive-analysis/<session_id>?target_price=X&margin=Y&category=Z` - Competition scanning
- `/api/export/<session_id>` - CSV export with flattened specifications

### Error Handling
The scraper handles StaleElementReferenceException during pagination, cookie banner interference, and ASP.NET postback mechanics. Price extraction gracefully handles "Prijs op aanvraag" (price on request) products.

## Development Notes

Always work within the virtual environment when developing. The scraper requires Chrome browser to be installed. For debugging, set `headless=False` in scraper initialization to observe browser behavior.

The price analysis system expects products with `soort_onderdeel`, `prijs_numeriek`, and `specificaties` fields. When adding new analysis features, ensure compatibility with the category filtering system.

The web dashboard uses AJAX for real-time updates and maintains scraping sessions in memory. For production deployment, consider implementing persistent session storage.