import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import re
import pandas as pd

# --- Import the news engine ---
from news_engine import (
    get_all_news_cached, 
    get_ticker_news, 
    get_market_headlines_cached
)

# =================================================
# PAGE CONFIG & SESSION STATE
# =================================================
st.set_page_config(
    page_title="Asia-Pacific Market Intelligence", 
    layout="wide",
    page_icon="📈"
)

if "added_tickers" not in st.session_state:
    st.session_state["added_tickers"] = []

if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "dashboard"

# =================================================
# POPULAR WATCHLIST & MAPPING
# =================================================
popular_watchlist = {
    # Hong Kong Blue Chips
    "0005.HK": "汇丰控股 HSBC Holdings",
    "0700.HK": "腾讯控股 Tencent",
    "9988.HK": "阿里巴巴 Alibaba",
    "3690.HK": "美团 Meituan",
    "0941.HK": "中国移动 China Mobile",
    "1398.HK": "工商银行 ICBC",
    "0388.HK": "港交所 HKEX",
    "2318.HK": "中国平安 Ping An",
    
    # US Tech (for comparison)
    "AAPL": "Apple",
    "TSLA": "Tesla",
    "NVDA": "NVIDIA",
    "MSFT": "Microsoft",
    "GOOGL": "Google"
}

def get_display_name(ticker):
    """Get friendly display name for ticker"""
    if ticker in popular_watchlist:
        return popular_watchlist[ticker]
    try:
        info = yf.Ticker(ticker).info
        short_name = info.get('shortName', ticker)
        long_name = info.get('longName', '')
        return f"{short_name} ({ticker})"
    except:
        return ticker

# =================================================
# SIDEBAR: SEARCH & CONTROLS
# =================================================
st.sidebar.header("🔍 Market Search")

# View mode toggle buttons
st.sidebar.divider()
col1, col2 = st.sidebar.columns(2)

with col1:
    if st.button("📊 Dashboard", use_container_width=True, type="primary" if st.session_state["view_mode"] == "dashboard" else "secondary"):
        st.session_state["view_mode"] = "dashboard"
        st.rerun()

with col2:
    if st.button("📰 Headlines", use_container_width=True, type="primary" if st.session_state["view_mode"] == "headlines" else "secondary"):
        st.session_state["view_mode"] = "headlines"
        st.rerun()

st.sidebar.divider()

search_query = st.sidebar.text_input(
    "Search Company or Ticker", 
    placeholder="e.g. 腾讯, HSBC, 0700, NVDA"
)

if search_query:
    try:
        search = yf.Search(search_query, max_results=8)
        if search.quotes:
            search_options = {
                f"{q.get('shortname', 'Unknown')} ({q['symbol']})": q['symbol'] 
                for q in search.quotes
            }
            selected_from_search = st.sidebar.selectbox(
                "Select from results:", 
                options=list(search_options.keys())
            )
            
            if st.sidebar.button("➕ Add to Dashboard"):
                ticker_to_add = search_options[selected_from_search]
                if ticker_to_add not in st.session_state["added_tickers"]:
                    st.session_state["added_tickers"].append(ticker_to_add)
                    st.success(f"Added {ticker_to_add}!")
                    st.rerun()
        else:
            st.sidebar.warning("No matches found. Try different keywords.")
    except Exception as e:
        st.sidebar.error(f"Search error: {str(e)}")

st.sidebar.divider()

# Popular stocks selection
st.sidebar.subheader("⭐ Popular Stocks")
popular_selection = st.sidebar.multiselect(
    "Quick add popular stocks:",
    options=list(popular_watchlist.keys()),
    default=[],
    format_func=lambda x: popular_watchlist.get(x, x)
)

# Combine selections
final_tickers = list(set(popular_selection + st.session_state["added_tickers"]))

# Chart controls
st.sidebar.divider()
st.sidebar.subheader("📊 Chart Settings")
days = st.sidebar.slider("Chart History (Days)", 30, 365, 90)
normalize = st.sidebar.checkbox("Normalize comparison (%)", True)
show_volume = st.sidebar.checkbox("Show trading volume", False)

# Clear button
if st.sidebar.button("🗑️ Clear Custom Selections"):
    st.session_state["added_tickers"] = []
    st.rerun()

# Display current watchlist
if final_tickers:
    st.sidebar.divider()
    st.sidebar.subheader("📋 Current Watchlist")
    for t in final_tickers:
        col1, col2 = st.sidebar.columns([4, 1])
        col1.caption(get_display_name(t))
        if col2.button("✖", key=f"remove_{t}"):
            if t in st.session_state["added_tickers"]:
                st.session_state["added_tickers"].remove(t)
            st.rerun()
else:
    st.sidebar.divider()
    st.sidebar.info("💡 No stocks selected yet. Choose from popular stocks above or search for any company!")

# =================================================
# MAIN DASHBOARD
# =================================================
st.title("🌏 Asia-Pacific Market Intelligence Dashboard")
st.caption("Real-time data for Hong Kong, China, and Global Markets")

# =================================================
# HEADLINES VIEW MODE
# =================================================
if st.session_state["view_mode"] == "headlines":
    # Custom CSS for professional headlines
    st.markdown("""
    <style>
    .headline-container {
        padding: 1rem;
        border-left: 3px solid #1f77b4;
        margin-bottom: 1rem;
        background-color: rgba(28, 131, 225, 0.05);
    }
    .headline-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .headline-meta {
        font-size: 0.85rem;
        color: #666;
    }
    .headline-summary {
        font-size: 0.9rem;
        color: #333;
        margin-top: 0.5rem;
        font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.subheader("📰 Market Headlines")
    st.caption("Latest news from Hong Kong, China, and Global Markets (Updates every 15 minutes)")
    
    with st.spinner("Loading market headlines..."):
        headlines = get_market_headlines_cached()
    
    if headlines:
        # Show headline stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Articles", len(headlines))
        with col2:
            hk_count = len([h for h in headlines if "Hong Kong" in h['region']])
            st.metric("🇭🇰 Hong Kong", hk_count)
        with col3:
            cn_count = len([h for h in headlines if "China" in h['region']])
            st.metric("🇨🇳 China", cn_count)
        with col4:
            global_count = len([h for h in headlines if "Global" in h['region']])
            st.metric("🌍 Global", global_count)
        
        st.divider()
        
        # Filter options for headlines
        col1, col2 = st.columns([3, 1])
        with col1:
            headline_filter = st.radio(
                "Filter by region:",
                ["All", "Hong Kong Market", "China Market", "Global Market"],
                horizontal=True,
                key="headline_filter_main"
            )
        with col2:
            show_count = st.selectbox("Show articles:", [10, 20, 30, 50], index=1)
        
        filtered_headlines = headlines if headline_filter == "All" else [h for h in headlines if headline_filter in h['region']]
        
        st.divider()
        
        # Display headlines in a professional, compact format
        for idx, headline in enumerate(filtered_headlines[:show_count]):
            # Professional card layout
            st.markdown(f"""
            <div class="headline-container">
                <div class="headline-title">
                    <a href="{headline['link']}" target="_blank" style="text-decoration: none; color: inherit;">
                        #{idx + 1} • {headline['title']}
                    </a>
                </div>
                <div class="headline-meta">
                    📰 {headline['source']} &nbsp;•&nbsp; 🌍 {headline['region']} &nbsp;•&nbsp; 🕐 {headline['published'].strftime('%Y-%m-%d %H:%M')}
                </div>
                {f'<div class="headline-summary">{headline.get("summary", "")}</div>' if headline.get('summary') else ''}
            </div>
            """, unsafe_allow_html=True)
        
        # Show total
        if len(filtered_headlines) > show_count:
            st.info(f"📊 Showing {show_count} of {len(filtered_headlines)} headlines. Increase the count to see more.")
    
    else:
        st.warning("⚠️ No headlines available at the moment. Please check back later.")
    
    # Stop here - don't show dashboard
    st.stop()

# =================================================
# DASHBOARD VIEW MODE (Default)
# =================================================

if not final_tickers:
    st.info("👈 **Select stocks from the sidebar to begin tracking**")
    
    st.markdown("---")
    
    # Show helpful examples in a nice layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 🇭🇰 Hong Kong Stocks")
        st.markdown("""
        - **0700.HK** - 腾讯 Tencent
        - **9988.HK** - 阿里巴巴 Alibaba
        - **0005.HK** - 汇丰 HSBC
        - **3690.HK** - 美团 Meituan
        - **0941.HK** - 中国移动 China Mobile
        """)
    
    with col2:
        st.markdown("#### 🇺🇸 US Stocks")
        st.markdown("""
        - **NVDA** - NVIDIA
        - **AAPL** - Apple
        - **TSLA** - Tesla
        - **MSFT** - Microsoft
        - **GOOGL** - Google
        """)
    
    with col3:
        st.markdown("#### 💡 How to Use")
        st.markdown("""
        **📰 Market Headlines**
        Check the sidebar for latest news
        
        **🔍 Search Stocks**
        Use the search box for any company
        
        **⭐ Quick Add**
        Select from popular stocks dropdown
        
        **📊 Track Performance**
        Charts and news appear here
        """)
    
    # Quick start buttons
    st.markdown("---")
    st.markdown("### 🚀 Quick Start Templates")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🇭🇰 HK Tech Giants"):
            st.session_state["added_tickers"] = ["0700.HK", "9988.HK", "3690.HK"]
            st.rerun()
    
    with col2:
        if st.button("🇺🇸 US Tech Leaders"):
            st.session_state["added_tickers"] = ["NVDA", "AAPL", "MSFT"]
            st.rerun()
    
    with col3:
        if st.button("🏦 HK Banking"):
            st.session_state["added_tickers"] = ["0005.HK", "1398.HK", "2318.HK"]
            st.rerun()
    
    with col4:
        if st.button("🌏 Asia Mix"):
            st.session_state["added_tickers"] = ["0700.HK", "9988.HK", "NVDA"]
            st.rerun()
    
    st.stop()

# =================================================
# PART 1: MARKET OVERVIEW CARDS
# =================================================
st.subheader("💹 Market Overview")

cols = st.columns(min(len(final_tickers), 4))
for idx, ticker in enumerate(final_tickers):
    with cols[idx % 4]:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="2d")
            
            if not hist.empty and len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                prev_price = hist['Close'].iloc[-2]
                change = current_price - prev_price
                change_pct = (change / prev_price) * 100
                
                color = "🟢" if change >= 0 else "🔴"
                st.metric(
                    label=get_display_name(ticker),
                    value=f"${current_price:.2f}",
                    delta=f"{change_pct:.2f}%"
                )
            else:
                st.metric(
                    label=get_display_name(ticker),
                    value="Data unavailable"
                )
        except Exception as e:
            st.metric(label=ticker, value="Error loading")

# =================================================
# PART 2: INTERACTIVE CHARTS
# =================================================
st.divider()
st.subheader("📈 Performance Chart")

# Download data
with st.spinner("Loading market data..."):
    data = yf.download(final_tickers, period=f"{days}d", group_by='ticker', progress=False)

if len(final_tickers) == 1:
    # Single stock: Candlestick chart
    t = final_tickers[0]
    df = data if not hasattr(data.columns, 'levels') else data[t]
    
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"],
        high=df["High"],
        low=df["Low"],
        close=df["Close"],
        name=get_display_name(t)
    ))
    
    if show_volume and "Volume" in df.columns:
        fig.add_trace(go.Bar(
            x=df.index,
            y=df["Volume"],
            name="Volume",
            yaxis="y2",
            marker_color='rgba(128,128,128,0.3)'
        ))
    
    fig.update_layout(
        template="plotly_dark",
        title=f"{get_display_name(t)} - Price Movement",
        xaxis_rangeslider_visible=False,
        yaxis2=dict(overlaying='y', side='right') if show_volume else None,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
else:
    # Multiple stocks: Line comparison
    fig = go.Figure()
    
    for t in final_tickers:
        try:
            if hasattr(data.columns, 'levels'):
                s = data[t]["Close"].dropna()
            else:
                s = data["Close"].dropna()
            
            if len(s) > 0:
                y = (s / s.iloc[0]) * 100 if normalize else s
                fig.add_trace(go.Scatter(
                    x=s.index, 
                    y=y, 
                    name=get_display_name(t),
                    mode='lines'
                ))
        except Exception as e:
            print(f"Error plotting {t}: {e}")
            continue
    
    y_title = "Relative Performance (%)" if normalize else "Price"
    fig.update_layout(
        template="plotly_dark",
        hovermode="x unified",
        title="Multi-Stock Comparison",
        yaxis_title=y_title,
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)

# =================================================
# PART 3: NEWS INTELLIGENCE FEED (Stock-Specific)
# =================================================
st.divider()
st.subheader("📊 News Intelligence")
st.caption("Stock-specific news from your watchlist")

with st.spinner("Fetching latest news..."):
    news_items = get_all_news_cached(final_tickers)

if not news_items:
    st.warning("⚠️ No news available. Check your API configuration in news_engine.py")
else:
    # News sentiment analysis
    full_text = " ".join([a['title'] for a in news_items])
    
    # Chinese character analysis
    cn_chars = "".join(re.findall(r'[\u4e00-\u9fff]', full_text))
    top_cn = "".join([w for w, _ in Counter(cn_chars).most_common(15)])
    
    # English keyword analysis
    en_words = re.findall(r'\b[A-Za-z]{4,}\b', full_text.lower())
    top_en = [w for w, _ in Counter(en_words).most_common(8) if w not in ['the', 'and', 'for', 'with']]
    
    # Display summary
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total News Articles", len(news_items))
        st.write(f"**🇨🇳 Top Chinese Keywords:** {top_cn if top_cn else 'N/A'}")
    with col2:
        sources = Counter([a['source'] for a in news_items])
        st.metric("News Sources", len(sources))
        st.write(f"**🇬🇧 Top English Keywords:** {', '.join(top_en) if top_en else 'N/A'}")
    
    # Filter options
    st.divider()
    filter_col1, filter_col2 = st.columns([2, 1])
    with filter_col1:
        region_filter = st.multiselect(
            "Filter by region:",
            options=list(set([a['region'] for a in news_items])),
            default=list(set([a['region'] for a in news_items]))
        )
    with filter_col2:
        max_news = st.slider("Show articles:", 5, 50, 20)
    
    # Display news
    filtered_news = [a for a in news_items if a['region'] in region_filter][:max_news]
    
    for article in filtered_news:
        with st.expander(f"{article['title']}", expanded=False):
            col1, col2, col3 = st.columns(3)
            col1.caption(f"📰 {article['source']}")
            col2.caption(f"🌍 {article['region']}")
            col3.caption(f"🕐 {article['published'].strftime('%Y-%m-%d %H:%M')}")
            
            if article["keywords"]:
                st.write("**Keywords:**", ", ".join(article["keywords"]))
            st.markdown(f"[📖 Read full article]({article['link']})")

# =================================================
# PART 4: STOCK ANALYSIS SUMMARY
# =================================================
st.divider()
st.subheader("📊 Individual Stock Analysis")

for ticker in final_tickers:
    with st.expander(f"📈 {get_display_name(ticker)}", expanded=False):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Price trend
            df = yf.download(ticker, period="60d", progress=False)
            if not df.empty and "Close" in df.columns:
                close = df["Close"]
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                close = close.dropna()
                
                if len(close) >= 2:
                    start_price = float(close.iloc[0])
                    end_price = float(close.iloc[-1])
                    pct_change = (end_price - start_price) / start_price * 100
                    
                    trend_emoji = "📈" if pct_change > 0 else "📉" if pct_change < 0 else "➡️"
                    trend_text = "Upward" if pct_change > 0 else "Downward" if pct_change < 0 else "Flat"
                    
                    st.write(f"{trend_emoji} **60-Day Trend:** {trend_text} ({pct_change:+.2f}%)")
                    
                    # Simple mini chart
                    mini_fig = go.Figure()
                    mini_fig.add_trace(go.Scatter(
                        x=close.index,
                        y=close.values,
                        fill='tozeroy',
                        line=dict(color='cyan', width=2)
                    ))
                    mini_fig.update_layout(
                        template="plotly_dark",
                        height=200,
                        margin=dict(l=0, r=0, t=0, b=0),
                        showlegend=False,
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
                    )
                    st.plotly_chart(mini_fig, use_container_width=True)
        
        with col2:
            # Company info
            try:
                info = yf.Ticker(ticker).info
                st.write("**Company Info:**")
                st.caption(f"Sector: {info.get('sector', 'N/A')}")
                st.caption(f"Industry: {info.get('industry', 'N/A')}")
                st.caption(f"Market Cap: {info.get('marketCap', 'N/A')}")
            except:
                st.caption("Company info unavailable")
        
        # Related news
        ticker_news = get_ticker_news(ticker, news_items)
        if ticker_news:
            st.write("**📰 Recent Headlines:**")
            for article in ticker_news[:3]:
                st.markdown(f"- [{article['title']}]({article['link']}) *({article['source']})*")
        else:
            st.caption("No recent news available")

# =================================================
# FOOTER & DISCLAIMER
# =================================================
st.divider()
st.caption(
    "⚠️ **Disclaimer:** This dashboard is for informational purposes only. "
    "News sourced from Yahoo Finance, Finnhub, NewsAPI, and other providers. "
    "Market data may be delayed. Always conduct your own research before making investment decisions."
)
st.caption("💡 **Tip:** Configure API keys in `news_engine.py` for enhanced news coverage.")
