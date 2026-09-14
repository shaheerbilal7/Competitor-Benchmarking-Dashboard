import matplotlib.pyplot as plt
import pandas as pd
import requests
import seaborn as sns
import streamlit as st
from bs4 import BeautifulSoup

# 1. DATA COLLECTION / SCRAPING FUNCTION
@st.cache_data
def fetch_competitor_data(
    url="https://www.scrapethissite.com/pages/simple/",
):
    """Scrapes competitor or country/market data directly from a target URL.

    Default URL: A web scraping sandbox containing table/card structured data.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/115.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        st.error(f"Failed to fetch data from URL: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")

    # Scrape structured data elements from the web page
    competitors = []
    capital_or_tier = []
    population_or_users = []
    area_or_metric = []

    # Example selector targeted at scrapethissite.com structure
    items = soup.find_all("div", class_="col-md-4 country")

    for item in items:
        name = item.find("h3", class_="country-name")
        capital = item.find("span", class_="country-capital")
        pop = item.find("span", class_="country-population")
        area = item.find("span", class_="country-area")

        competitors.append(name.text.strip() if name else "Unknown")
        capital_or_tier.append(capital.text.strip() if capital else "N/A")

        # Clean numerical values
        raw_pop = pop.text.strip() if pop else "0"
        raw_area = area.text.strip() if area else "0"

        try:
            population_or_users.append(float(raw_pop.replace(",", "")))
        except ValueError:
            population_or_users.append(0.0)

        try:
            area_or_metric.append(float(raw_area.replace(",", "")))
        except ValueError:
            area_or_metric.append(0.0)

    # Construct Pandas DataFrame from scraped lists
    df = pd.DataFrame(
        {
            "Competitor": competitors[:10],  # Top 10 for dashboard clarity
            "Category_Tier": capital_or_tier[:10],
            "User_Base_Thousands": [p / 1000 for p in population_or_users[:10]],
            "Market_Score": [a / 1000 for a in area_or_metric[:10]],
        }
    )

    return df

# 2. STREAMLIT DASHBOARD UI
def main():
    st.set_page_config(
        page_title="Competitor Benchmarking Dashboard", layout="wide"
    )

    st.title("📊 Live Web Scraped Benchmarking Dashboard")
    st.markdown(
        "Data scraped directly from web sources to analyze market standards."
    )

    # Fetch live scraped data
    df = fetch_competitor_data()

    if df.empty:
        st.warning("No data found or scraping failed.")
        return

    # Sidebar Filter
    st.sidebar.header("Filter Options")
    selected_competitors = st.sidebar.multiselect(
        "Select Competitors / Entities",
        options=df["Competitor"].tolist(),
        default=df["Competitor"].tolist(),
    )

    filtered_df = df[df["Competitor"].isin(selected_competitors)]

    # Key Metrics
    st.subheader("Key Benchmarks")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Entities Tracked", len(filtered_df))
    with c2:
        st.metric(
            "Avg User Base (K)", f"{filtered_df['User_Base_Thousands'].mean():.2f}K"
        )
    with c3:
        st.metric(
            "Avg Market Score", f"{filtered_df['Market_Score'].mean():.2f}"
        )

    st.markdown("---")

    # Visualizations
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("User Base Comparison")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.barplot(
            data=filtered_df,
            x="Competitor",
            y="User_Base_Thousands",
            ax=ax,
            palette="Blues_d",
        )
        ax.set_ylabel("User Base (Thousands)")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    with col_right:
        st.subheader("Market Score vs User Base")
        fig, ax = plt.subplots(figsize=(6, 4))
        sns.scatterplot(
            data=filtered_df,
            x="User_Base_Thousands",
            y="Market_Score",
            hue="Competitor",
            s=150,
            ax=ax,
        )
        ax.set_xlabel("User Base (K)")
        ax.set_ylabel("Market Score")
        st.pyplot(fig)

    # Table View
    st.subheader("Scraped Dataset View")
    st.dataframe(filtered_df, use_container_width=True)


if __name__ == "__main__":
    main()