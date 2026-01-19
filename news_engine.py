import requests
import yfinance as yf
from datetime import datetime, timedelta
import streamlit as st

# =================================================
# CONFIGURATION
# =================================================
try:
    FINNHUB_API_KEY = st.secrets.get("FINNHUB_API_KEY", "")
    NEWSAPI_KEY = st.secrets.get("NEWSAPI_KEY", "")
    ALPHAVANTAGE_KEY = st.secrets.get("ALPHAVANTAGE_KEY", "")
    print(f"✅ API Keys - Finnhub: {'Yes' if FINNHUB_API_KEY else 'No'}, NewsAPI: {'Yes' if NEWSAPI_KEY else 'No'}")
except Exception as e:
    print(f"⚠️ Could not load secrets: {e}")
    FINNHUB_API_KEY = ""
    NEWSAPI_KEY = ""
    ALPHAVANTAGE_KEY = ""

# =================================================
# RELIABLE NEWS SOURCES
# =================================================

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
                # Try alternative fields
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
                    "summary": item.get("summary", "")[:200]  # First 200 chars
                })
        
        print(f"Yahoo: Processed {len(result)} valid articles")
        return result
        
    except Exception as e:
        print(f"Yahoo error for {ticker}: {e}")
    return []


def fetch_finnhub_news(ticker, days=7):
    """Fetch news from Finnhub"""
    if not FINNHUB_API_KEY:
        return []
    
    try:
        # For HK stocks, try both with and without .HK
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


def fetch_newsapi_news(ticker, company_name=None, days=7):
    """Fetch news from NewsAPI with Chinese language support"""
    if not NEWSAPI_KEY:
        return []
    
    try:
        # Build search query
        search_terms = []
        
        # Add company name if available
        if company_name:
            search_terms.append(company_name)
        
        # Add ticker variations
        base_ticker = ticker.replace(".HK", "").replace(".SS", "").replace(".SZ", "")
        search_terms.append(base_ticker)
        
        # For HK stocks, add common Chinese terms
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
                    # Determine region based on content
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


def fetch_alphavantage_news(ticker):
    """Fetch news sentiment from Alpha Vantage"""
    if not ALPHAVANTAGE_KEY:
        return []
    
    try:
        # Clean ticker for Alpha Vantage
        clean_ticker = ticker.replace(".HK", "")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "NEWS_SENTIMENT",
            "tickers": clean_ticker,
            "apikey": ALPHAVANTAGE_KEY,
            "limit": 10
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "feed" in data:
                result = []
                for item in data["feed"][:10]:
                    title = item.get("title", "")
                    if title and len(title) > 5:
                        try:
                            pub_date = datetime.strptime(item.get("time_published", "20240101T000000"), "%Y%m%dT%H%M%S")
                        except:
                            pub_date = datetime.now()
                        
                        result.append({
                            "title": title,
                            "link": item.get("url", "#"),
                            "source": item.get("source", "Alpha Vantage"),
                            "published": pub_date,
                            "keywords": [t["ticker"] for t in item.get("ticker_sentiment", [])],
                            "region": "Global",
                            "summary": item.get("summary", "")[:200]
                        })
                
                print(f"Alpha Vantage: Found {len(result)} articles for {ticker}")
                return result
                
    except Exception as e:
        print(f"Alpha Vantage error for {ticker}: {e}")
    return []


def fetch_google_news_rss(company_name, ticker):
    """Fetch from Google News RSS (works without API)"""
    try:
        # Google News RSS search
        search_query = company_name if company_name else ticker.replace(".HK", "")
        url = f"https://news.google.com/rss/search?q={search_query}&hl=en-US&gl=US&ceid=US:en"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
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
                    
                    # Parse date
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


def fetch_google_news_chinese(company_name, ticker):
    """Fetch Chinese language news from Google News"""
    try:
        # Search in Chinese - use stock code for HK stocks
        if ".HK" in ticker:
            stock_code = ticker.replace(".HK", "")
            search_query = f"{stock_code} OR {company_name}"
        else:
            search_query = company_name
        
        # Chinese Google News RSS
        url = f"https://news.google.com/rss/search?q={search_query}&hl=zh-CN&gl=HK&ceid=HK:zh-Hans"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
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
                    
                    if title and len(title) > 2:  # Chinese titles can be shorter
                        result.append({
                            "title": title,
                            "link": link,
                            "source": "Google 新闻",
                            "published": pub_date,
                            "keywords": [],
                            "region": "China/HK (中文)",
                            "summary": ""
                        })
            
            print(f"Google News (CN): Found {len(result)} Chinese articles for {ticker}")
            return result
            
    except Exception as e:
        print(f"Google News Chinese error for {ticker}: {e}")
    return []


def fetch_sina_finance_rss(ticker):
    """Fetch from Sina Finance (新浪财经) - Chinese financial news"""
    try:
        # Sina Finance RSS - general finance news
        url = "https://finance.sina.com.cn/roll/index.d.html"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find news items (simplified - Sina's structure changes)
            news_links = soup.find_all('a', href=True, limit=20)
            
            result = []
            stock_code = ticker.replace(".HK", "").lstrip("0")
            
            for link in news_links:
                title = link.get_text(strip=True)
                href = link['href']
                
                # Filter for relevant news
                if (len(title) > 5 and 
                    (stock_code in title or 
                     any(keyword in title for keyword in ['股', '市', '港股', '投资']))):
                    
                    result.append({
                        "title": title,
                        "link": href if href.startswith('http') else f"https://finance.sina.com.cn{href}",
                        "source": "新浪财经",
                        "published": datetime.now(),
                        "keywords": [],
                        "region": "China (中文)",
                        "summary": ""
                    })
                    
                    if len(result) >= 5:
                        break
            
            print(f"Sina Finance: Found {len(result)} Chinese articles")
            return result
            
    except Exception as e:
        print(f"Sina Finance error for {ticker}: {e}")
    return []


def fetch_eastmoney_news(ticker):
    """Fetch from East Money (东方财富) - Popular Chinese finance portal"""
    try:
        stock_code = ticker.replace(".HK", "")
        
        # East Money news API (simplified)
        url = f"https://search-api-web.eastmoney.com/search/jsonp"
        params = {
            'cb': 'jQuery',
            'param': f'{{"uid":"","keyword":"{stock_code}","type":["cmsArticleWebOld"],"client":"web","clientType":"web","clientVersion":"curr"}}',
            'pageindex': 1,
            'pagesize': 10
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://so.eastmoney.com/'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # East Money returns JSONP, would need parsing
            # For now, return placeholder
            print(f"East Money: Attempted fetch for {ticker}")
            return []
            
    except Exception as e:
        print(f"East Money error for {ticker}: {e}")
    return []


def fetch_wallstreetcn_rss():
    """Fetch from Wall Street CN (华尔街见闻) - Chinese financial news"""
    try:
        # Wall Street CN RSS feed
        url = "https://api-prod.wallstreetcn.com/apiv1/content/articles"
        params = {
            'limit': 10,
            'channel': 'global-markets'
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            result = []
            for item in data.get('data', {}).get('items', [])[:10]:
                title = item.get('title', '')
                if title and len(title) > 5:
                    result.append({
                        "title": title,
                        "link": f"https://wallstreetcn.com/articles/{item.get('id', '')}",
                        "source": "华尔街见闻",
                        "published": datetime.fromtimestamp(item.get('display_time', 0)) if item.get('display_time') else datetime.now(),
                        "keywords": [],
                        "region": "China (中文)",
                        "summary": item.get('summary', '')[:200]
                    })
            
            print(f"Wall Street CN: Found {len(result)} Chinese articles")
            return result
            
    except Exception as e:
        print(f"Wall Street CN error: {e}")
    return []


def fetch_zh_yahoo_finance(ticker):
    """Fetch from Yahoo Finance Hong Kong (中文版)"""
    try:
        # Yahoo HK Finance in Chinese
        stock_code = ticker.replace(".HK", "")
        url = f"https://hk.finance.yahoo.com/quote/{stock_code}.HK"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'zh-HK,zh;q=0.9'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for news items (structure varies)
            news_items = soup.find_all('h3', limit=10)
            
            result = []
            for item in news_items:
                title = item.get_text(strip=True)
                link_tag = item.find_parent('a')
                
                if title and len(title) > 5 and link_tag:
                    href = link_tag.get('href', '')
                    full_link = f"https://hk.finance.yahoo.com{href}" if href.startswith('/') else href
                    
                    result.append({
                        "title": title,
                        "link": full_link,
                        "source": "Yahoo財經 (HK)",
                        "published": datetime.now(),
                        "keywords": [],
                        "region": "Hong Kong (中文)",
                        "summary": ""
                    })
            
            print(f"Yahoo HK (CN): Found {len(result)} Chinese articles for {ticker}")
            return result
            
    except Exception as e:
        print(f"Yahoo HK Chinese error for {ticker}: {e}")
    return []


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
                        "summary": item.get('summary', '')[:200]
                    })
            print(f"✅ Wall Street CN Headlines: {len([h for h in all_headlines if h['source'] == '华尔街见闻'])}")
    except Exception as e:
        print(f"❌ Wall Street CN headlines error: {e}")
    
    # 2. Google News - Hong Kong Business Headlines
    try:
        from bs4 import BeautifulSoup
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
                            "summary": ""
                        })
            print(f"✅ Google HK Headlines: {len([h for h in all_headlines if h['source'] == 'Google 新闻'])}")
    except Exception as e:
        print(f"❌ Google HK headlines error: {e}")
    
    # 3. Google News - Global Markets
    try:
        from bs4 import BeautifulSoup
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
                            "summary": ""
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
# MAIN AGGREGATOR
# =================================================

@st.cache_data(ttl=1800)
def get_all_news_cached(tickers):
    """
    Aggregate news from all working sources including Chinese sources
    Priority: Yahoo > Chinese Sources > Finnhub > NewsAPI > Alpha Vantage > Google News
    """
    print(f"\n📰 Fetching news for: {tickers}")
    all_news = []
    
    for ticker in tickers:
        print(f"\n--- Processing {ticker} ---")
        
        # Get company info
        try:
            stock_info = yf.Ticker(ticker).info
            company_name = stock_info.get("shortName", ticker)
            print(f"Company: {company_name}")
        except:
            company_name = ticker
        
        # PRIORITY 1: Yahoo Finance (English)
        all_news.extend(fetch_yahoo_news(ticker))
        
        # PRIORITY 2: Chinese Sources (for HK/China stocks)
        if ".HK" in ticker or any(x in ticker for x in [".SS", ".SZ"]):
            all_news.extend(fetch_google_news_chinese(company_name, ticker))
            all_news.extend(fetch_zh_yahoo_finance(ticker))
            all_news.extend(fetch_sina_finance_rss(ticker))
            all_news.extend(fetch_wallstreetcn_rss())  # General Chinese finance news
        
        # PRIORITY 3: English Sources
        all_news.extend(fetch_google_news_rss(company_name, ticker))
        
        # PRIORITY 4: API Sources (if configured)
        if FINNHUB_API_KEY:
            all_news.extend(fetch_finnhub_news(ticker))
        
        if NEWSAPI_KEY:
            all_news.extend(fetch_newsapi_news(ticker, company_name))
        
        if ALPHAVANTAGE_KEY:
            all_news.extend(fetch_alphavantage_news(ticker))
    
    print(f"\n📊 Total articles fetched: {len(all_news)}")
    
    # Deduplicate by title
    seen_titles = set()
    unique_news = []
    
    for item in all_news:
        title = item["title"].lower().strip()
        title_key = title[:60]  # First 60 chars
        
        if title_key not in seen_titles and len(title) > 2:  # Allow shorter Chinese titles
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