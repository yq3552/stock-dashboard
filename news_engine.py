import requests
import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st
from bs4 import BeautifulSoup
import re

# =================================================
# CONFIGURATION
# =================================================
try:
    import streamlit as st
    FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "")
    NEWSAPI_KEY = st.secrets.get("NEWSAPI_KEY", "")
    ALPHAVANTAGE_KEY = st.secrets.get("ALPHAVANTAGE_KEY", "")
except:
    FINNHUB_API_KEY = ""
    NEWSAPI_KEY = ""
    ALPHAVANTAGE_KEY = ""

print(f"API Keys loaded - Finnhub: {'✓' if FINNHUB_API_KEY else '✗'}, NewsAPI: {'✓' if NEWSAPI_KEY else '✗'}")

# =================================================
# INDUSTRY CLASSIFICATION
# =================================================

def classify_industry(title, content=""):
    """
    Classify news article into industry categories
    Based on keywords in title and content
    """
    text = (title + " " + content).lower()
    
    industries = []
    
    # Tech keywords
    tech_keywords = [
        'tech', 'ai', 'artificial intelligence', 'chip', 'semiconductor', 'software',
        'cloud', 'data', 'cyber', 'app', 'digital', 'internet', 'smartphone',
        '科技', '人工智能', '芯片', '软件', '云计算', '数据', '互联网', '智能手机'
    ]
    
    # Finance keywords
    finance_keywords = [
        'bank', 'finance', 'loan', 'credit', 'insurance', 'investment', 'fund',
        'wealth', 'asset', 'trading', 'exchange', 'fintech',
        '银行', '金融', '贷款', '信贷', '保险', '投资', '基金', '资产', '交易'
    ]
    
    # Healthcare keywords
    healthcare_keywords = [
        'health', 'medical', 'pharma', 'drug', 'biotech', 'hospital', 'clinical',
        'vaccine', 'treatment', 'patient', 'diagnostic',
        '医疗', '制药', '生物', '疫苗', '治疗', '诊断', '健康'
    ]
    
    # Energy keywords
    energy_keywords = [
        'energy', 'oil', 'gas', 'renewable', 'solar', 'wind', 'power', 'electric',
        'battery', 'coal', 'petroleum', 'fuel',
        '能源', '石油', '天然气', '太阳能', '风能', '电力', '电池', '煤炭'
    ]
    
    # Consumer keywords
    consumer_keywords = [
        'retail', 'consumer', 'shopping', 'ecommerce', 'store', 'brand', 'fashion',
        'food', 'beverage', 'restaurant', 'hotel', 'travel', 'tourism',
        '零售', '消费', '购物', '电商', '品牌', '时尚', '食品', '餐饮', '酒店', '旅游'
    ]
    
    # Real Estate keywords
    realestate_keywords = [
        'property', 'real estate', 'housing', 'construction', 'developer',
        'mortgage', 'rental', 'residential', 'commercial',
        '房地产', '物业', '住房', '建筑', '开发商', '按揭', '租赁'
    ]
    
    # Manufacturing keywords
    manufacturing_keywords = [
        'manufacturing', 'industrial', 'factory', 'production', 'automotive',
        'machinery', 'equipment', 'supply chain',
        '制造', '工业', '工厂', '生产', '汽车', '机械', '设备', '供应链'
    ]
    
    # Telecom keywords
    telecom_keywords = [
        'telecom', '5g', '4g', 'network', 'mobile', 'wireless', 'broadband',
        'communication', 'carrier',
        '电信', '移动', '网络', '通信', '运营商'
    ]
    
    # Check each category
    if any(kw in text for kw in tech_keywords):
        industries.append("Tech")
    
    if any(kw in text for kw in finance_keywords):
        industries.append("Finance")
    
    if any(kw in text for kw in healthcare_keywords):
        industries.append("Healthcare")
    
    if any(kw in text for kw in energy_keywords):
        industries.append("Energy")
    
    if any(kw in text for kw in consumer_keywords):
        industries.append("Consumer")
    
    if any(kw in text for kw in realestate_keywords):
        industries.append("Real Estate")
    
    if any(kw in text for kw in manufacturing_keywords):
        industries.append("Manufacturing")
    
    if any(kw in text for kw in telecom_keywords):
        industries.append("Telecom")
    
    # If no industry detected, mark as General
    if not industries:
        industries.append("General")
    
    return industries


# =================================================
# HEADLINE NEWS (Market-Wide News)
# =================================================

def fetch_market_headlines():
    """
    Fetch general market headlines (not stock-specific)
    Returns top financial news for Hong Kong, China, and Global markets
    """
    print("\n📰 Fetching market headlines...")
    all_headlines = []
    
    # 1. Wall Street CN - General Chinese market news
    try:
        url = "https://api-prod.wallstreetcn.com/apiv1/content/articles"
        params = {
            'limit': 15,
            'channel': 'global-markets'
        }
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for item in data.get('data', {}).get('items', [])[:8]:
                title = item.get('title', '')
                if title and len(title) > 5:
                    all_headlines.append({
                        "title": title,
                        "link": f"https://wallstreetcn.com/articles/{item.get('id', '')}",
                        "source": "华尔街见闻",
                        "published": datetime.fromtimestamp(item.get('display_time', 0)) if item.get('display_time') else datetime.now(),
                        "keywords": [],
                        "region": "China Market",
                        "summary": item.get('summary', '')[:200],
                        "industries": classify_industry(title, item.get('summary', ''))
                    })
            print(f"✅ Wall Street CN Headlines: {len([h for h in all_headlines if h['source'] == '华尔街见闻'])}")
    except Exception as e:
        print(f"❌ Wall Street CN headlines error: {e}")
    
    # 2. Google News - Hong Kong Business Headlines
    try:
        url = "https://news.google.com/rss/search?q=Hong+Kong+business+OR+港股&hl=zh-CN&gl=HK&ceid=HK:zh-Hans"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:8]
            
            for item in items:
                title_elem = item.find('title')
                if title_elem:
                    title = title_elem.get_text()
                    link = item.find('link').get_text() if item.find('link') else "#"
                    
                    try:
                        date_str = item.find('pubDate').get_text() if item.find('pubDate') else ""
                        pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        pub_date = datetime.now()
                    
                    if title and len(title) > 5:
                        all_headlines.append({
                            "title": title,
                            "link": link,
                            "source": "Google 新闻",
                            "published": pub_date,
                            "keywords": [],
                            "region": "Hong Kong Market",
                            "summary": "",
                            "industries": classify_industry(title)
                        })
            print(f"✅ Google HK Headlines: {len([h for h in all_headlines if h['source'] == 'Google 新闻'])}")
    except Exception as e:
        print(f"❌ Google HK headlines error: {e}")
    
    # 3. Google News - Global Markets
    try:
        url = "https://news.google.com/rss/search?q=stock+market+OR+nasdaq+OR+dow+jones&hl=en-US&gl=US&ceid=US:en"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:8]
            
            for item in items:
                title_elem = item.find('title')
                if title_elem:
                    title = title_elem.get_text()
                    link = item.find('link').get_text() if item.find('link') else "#"
                    
                    try:
                        date_str = item.find('pubDate').get_text() if item.find('pubDate') else ""
                        pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        pub_date = datetime.now()
                    
                    if title and len(title) > 5:
                        all_headlines.append({
                            "title": title,
                            "link": link,
                            "source": "Google News",
                            "published": pub_date,
                            "keywords": [],
                            "region": "Global Market",
                            "summary": "",
                            "industries": classify_industry(title)
                        })
            print(f"✅ Google Global Headlines: {len([h for h in all_headlines if h['source'] == 'Google News'])}")
    except Exception as e:
        print(f"❌ Google Global headlines error: {e}")
    
    # Deduplicate
    seen_titles = set()
    unique_headlines = []
    
    for item in all_headlines:
        title_key = item["title"].lower()[:60]
        if title_key not in seen_titles and len(item["title"]) > 5:
            seen_titles.add(title_key)
            unique_headlines.append(item)
    
    # Sort by date
    unique_headlines.sort(key=lambda x: x["published"], reverse=True)
    
    print(f"📊 Total unique headlines: {len(unique_headlines)}")
    return unique_headlines[:30]


@st.cache_data(ttl=900)  # Cache for 15 minutes
def get_market_headlines_cached():
    """Cached version of market headlines - refreshes every 15 minutes"""
    return fetch_market_headlines()


# =================================================
# STOCK-SPECIFIC NEWS SOURCES
# =================================================

def fetch_finnhub_news(ticker, days=7):
    """Fetch news from Finnhub"""
    if not FINNHUB_API_KEY:
        return []
    
    try:
        search_tickers = [ticker]
        if ".HK" in ticker:
            search_tickers.append(ticker.replace(".HK", ""))
        
        all_articles = []
        
        for search_ticker in search_tickers:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            url = "https://finnhub.io/api/v1/company-news"
            params = {
                "symbol": search_ticker,
                "from": start_date.strftime("%Y-%m-%d"),
                "to": end_date.strftime("%Y-%m-%d"),
                "token": FINNHUB_API_KEY
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                for item in data[:10]:
                    headline = item.get("headline", "")
                    if headline and len(headline) > 5:
                        all_articles.append({
                            "title": headline,
                            "link": item.get("url", "#"),
                            "source": item.get("source", "Finnhub"),
                            "published": datetime.fromtimestamp(item.get("datetime", 0)) if item.get("datetime") else datetime.now(),
                            "keywords": item.get("related", "").split(",") if item.get("related") else [],
                            "region": "Hong Kong" if ".HK" in ticker else "Global",
                            "summary": item.get("summary", "")
                        })
        
        print(f"Finnhub: Found {len(all_articles)} articles for {ticker}")
        return all_articles
        
    except Exception as e:
        print(f"Finnhub error for {ticker}: {e}")
    return []


def fetch_yahoo_news(ticker):
    """Fetch news from Yahoo Finance - FIXED VERSION"""
    try:
        stock = yf.Ticker(ticker)
        news = stock.news
        
        if not news:
            print(f"Yahoo: No news for {ticker}")
            return []
        
        print(f"Yahoo: Found {len(news)} articles for {ticker}")
        
        result = []
        for item in news[:15]:
            # Better title extraction
            title = item.get("title", "")
            if not title or title == "No title":
                title = item.get("headline", item.get("summary", "Untitled Article"))
            
            # Better timestamp handling
            timestamp = item.get("providerPublishTime", 0)
            if timestamp and timestamp > 0:
                try:
                    pub_date = datetime.fromtimestamp(timestamp)
                except:
                    pub_date = datetime.now()
            else:
                pub_date = datetime.now()
            
            # Only add if we have a valid title
            if title and len(title) > 5:
                result.append({
                    "title": title,
                    "link": item.get("link", "#"),
                    "source": item.get("publisher", "Yahoo Finance"),
                    "published": pub_date,
                    "keywords": [],
                    "region": "Hong Kong" if ".HK" in ticker else "Global",
                    "summary": item.get("summary", "")[:200]
                })
        
        print(f"Yahoo: Processed {len(result)} valid articles")
        return result
        
    except Exception as e:
        print(f"Yahoo error for {ticker}: {e}")
    return []


def fetch_newsapi_news(ticker, company_name=None, days=7):
    """Fetch news from NewsAPI with Chinese language support"""
    if not NEWSAPI_KEY:
        return []
    
    try:
        search_terms = []
        
        if company_name:
            search_terms.append(company_name)
        
        base_ticker = ticker.replace(".HK", "").replace(".SS", "").replace(".SZ", "")
        search_terms.append(base_ticker)
        
        if ".HK" in ticker:
            search_query = f"({' OR '.join(search_terms)}) AND (Hong Kong OR 香港 OR China OR 中国)"
        else:
            search_query = ' OR '.join(search_terms)
        
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": search_query,
            "language": "en,zh",
            "sortBy": "publishedAt",
            "pageSize": 20,
            "apiKey": NEWSAPI_KEY,
            "from": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            
            result = []
            for item in articles[:15]:
                title = item.get("title", "")
                if title and len(title) > 5:
                    region = "Global"
                    if any(x in title for x in ["Hong Kong", "香港", "HK"]):
                        region = "Hong Kong"
                    elif any(x in title for x in ["China", "中国", "Chinese"]):
                        region = "China"
                    
                    result.append({
                        "title": title,
                        "link": item.get("url", "#"),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "published": datetime.fromisoformat(item.get("publishedAt", "").replace("Z", "+00:00")) if item.get("publishedAt") else datetime.now(),
                        "keywords": [],
                        "region": region,
                        "summary": item.get("description", "")[:200]
                    })
            
            print(f"NewsAPI: Found {len(result)} articles for {ticker}")
            return result
            
    except Exception as e:
        print(f"NewsAPI error for {ticker}: {e}")
    return []


def fetch_google_news_rss(company_name, ticker):
    """Fetch from Google News RSS (works without API)"""
    try:
        search_query = company_name if company_name else ticker.replace(".HK", "")
        url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')[:10]
            
            result = []
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                date_elem = item.find('pubDate')
                
                if title_elem:
                    title = title_elem.get_text()
                    link = link_elem.get_text() if link_elem else "#"
                    
                    try:
                        date_str = date_elem.get_text() if date_elem else ""
                        pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %Z")
                    except:
                        pub_date = datetime.now()
                    
                    if title and len(title) > 5:
                        result.append({
                            "title": title,
                            "link": link,
                            "source": "Google News",
                            "published": pub_date,
                            "keywords": [],
                            "region": "Hong Kong" if ".HK" in ticker else "Global",
                            "summary": ""
                        })
            
            print(f"Google News: Found {len(result)} articles for {ticker}")
            return result
            
    except Exception as e:
        print(f"Google News error for {ticker}: {e}")
    return []


# =================================================
# MAIN AGGREGATOR
# =================================================

@st.cache_data(ttl=1800)
def get_all_news_cached(tickers):
    """
    Aggregate news from all working sources including Chinese sources
    """
    print(f"\n📰 Fetching news for: {tickers}")
    all_news = []
    
    for ticker in tickers:
        print(f"\n--- Processing {ticker} ---")
        
        try:
            stock_info = yf.Ticker(ticker).info
            company_name = stock_info.get("shortName", ticker)
            print(f"Company: {company_name}")
        except:
            company_name = ticker
        
        # Priority 1: Yahoo Finance (English)
        all_news.extend(fetch_yahoo_news(ticker))
        
        # Priority 2: English Sources
        all_news.extend(fetch_google_news_rss(company_name, ticker))
        
        # Priority 3: API Sources (if configured)
        if FINNHUB_API_KEY:
            all_news.extend(fetch_finnhub_news(ticker))
        
        if NEWSAPI_KEY:
            all_news.extend(fetch_newsapi_news(ticker, company_name))
    
    print(f"\n📊 Total articles fetched: {len(all_news)}")
    
    # Deduplicate by title
    seen_titles = set()
    unique_news = []
    
    for item in all_news:
        title = item["title"].lower().strip()
        title_key = title[:60]
        
        if title_key not in seen_titles and len(title) > 2:
            seen_titles.add(title_key)
            unique_news.append(item)
    
    # Sort by date (newest first)
    unique_news.sort(key=lambda x: x["published"], reverse=True)
    
    print(f"📊 Unique articles after dedup: {len(unique_news)}")
    
    return unique_news[:50]


def get_ticker_news(ticker, all_news):
    """Filter news for specific ticker"""
    ticker_base = ticker.replace(".HK", "").replace(".SS", "").replace(".SZ", "")
    
    relevant = []
    for item in all_news:
        title_lower = item.get("title", "").lower()
        link_lower = item.get("link", "").lower()
        
        if (ticker.lower() in link_lower or 
            ticker.lower() in title_lower or
            ticker_base.lower() in title_lower or
            ticker in str(item.get("keywords", []))):
            relevant.append(item)
    
    return relevant
