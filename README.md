# eBay AI Price Estimator & Market Analyzer

**Automated eBay market analysis tool that combines official APIs, web scraping, and LLM-based filtering to determine the optimal selling price for any item.**

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![eBay API](https://img.shields.io/badge/API-eBay_Browse-red.svg)
![SerpApi](https://img.shields.io/badge/Scraper-SerpApi-green.svg)
![Groq](https://img.shields.io/badge/AI-Groq_Llama3-orange.svg)

## 📖 Overview

This tool automates the process of flipping items or valuing inventory. Instead of manually checking "Sold" listings and guessing a price, this script:

1.  **Fetches Active Listings** using the official **eBay Browse API** (real-time competition).
2.  **Fetches Sold Listings** using **SerpApi** (bypassing the deprecated Finding API to get historical sales).
3.  **Filters Garbage Data** using **Groq (Llama 3)**. The AI analyzes item titles to remove "broken", "parts only", "box only", or irrelevant accessories that skew the average price.
4.  **Calculates Pricing** using a statistical engine (`numpy`) to determine a "Fast Flip" price versus a "Max Profit" price.
5.  **Generates a Report** with sell probability, market health (Buyers vs Sellers market), and exact price targets.

## 📊 Sample Output

```text
/Users/.../python /Users/mp3skater/.../ebayPrice/src/main.py

🔎 Searching market data for: Xbox Series X Controller...
   Found 100 active and 59 sold raw items.

========================================
💰 PRICE REPORT: Xbox Series X Controller
========================================
🎯 Target TOTAL Price: €33.99
   (Subtract your shipping cost from this number)
🎲 Sell Probability:   99%
📊 Market Health:      🔥 Hot (Sellers Market)
Active Competitors:    25 (Lowest Total: €24.99)
Recent Sales:          59 (Median Total: €40.0)
========================================
```

---

## 🛠️ Prerequisites

### 1. API Keys (Required)
You need API keys from three services to run this full stack:

*   **eBay Developer Program:** For fetching active listings. [Get Key](https://developer.ebay.com/)
*   **SerpApi:** For scraping "Sold" listings (Free tier available). [Get Key](https://serpapi.com/)
*   **Groq Cloud:** For the LLM smart filtering (Free beta available). [Get Key](https://console.groq.com/)

### 2. Python Dependencies
Install the required libraries:

```bash
pip install requests python-dotenv serpapi groq numpy
```

---

## ⚙️ Setup & Configuration

### 1. Environment Variables
Create a `.env` file in the root directory of the project. Add your keys:

```ini
# .env file
# eBay API Credentials (App ID / Client ID)
CLIENT_ID=your_ebay_app_id
CLIENT_SECRET=your_ebay_cert_id

# SerpApi (For Sold Listings)
SERPAPI_KEY=your_serpapi_private_key

# Groq (For AI Filtering)
GROQ_API_KEY=your_groq_api_key
```

### 2. Marketplace Configuration
The default market is set to Italy (`IT`). To change this, edit `src/main.py`:

```python
MARKETPLACE = "US" # Options: US, IT, DE, GB, CA, AU
```

---

## 🚀 Usage

1.  Open `src/main.py`.
2.  Change the `query` variable to the item you want to value:

```python
query = "Sony WH-1000XM5 Headphones"
```

3.  Run the script:

```bash
python src/main.py
```

### How it works internally:

*   **`core/ebay_client.py`**: A hybrid client. It uses `requests` and OAuth2 for eBay's official Browse API (Active items) and the `serpapi` library to scrape Google/eBay results for "Sold" items.
*   **`core/llm_filter.py`**: Sends the raw list of items to Groq (Llama-3-70b). The LLM acts as a semantic filter, returning a JSON list of valid Item IDs, discarding replicas or broken items.
*   **`core/pricing_engine.py`**:
    *   **Sell Through Rate (STR):** Calculates `Sold / Active` ratio.
    *   **Fast Flip Strategy:** Targets the lowest 20th percentile of sold prices or undercuts the lowest active competitor.
    *   **Max Profit Strategy:** Targets the median sold price, capped by the 3rd cheapest active competitor.

---

## ⚠️ Troubleshooting

**`SerpApi Error: module 'serpapi' has no attribute 'GoogleSearch'`**
*   You installed the new library but used old code. This project uses the modern `serpapi.Client`. Ensure you are running the latest code in `src/core/ebay_client.py`.

**`Groq Error: API Key missing`**
*   Ensure your `.env` file is named exactly `.env` (not `.env.txt`) and is in the same folder as your script or project root.

**`Found 0 active and 0 sold items`**
*   Check your `MARKETPLACE` setting. Searching for Italian keywords on `EBAY_US` (or vice versa) returns zero results.

---

## ⚖️ Disclaimer

This tool is for **educational and research purposes only**. eBay prices fluctuate wildly based on condition, photos, and seller reputation. The "Target Price" is a statistical recommendation, not a guarantee of sale.

This project is not affiliated with eBay Inc.

The License is the [MIT License](LICENSE)
