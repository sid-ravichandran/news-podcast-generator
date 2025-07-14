import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
from newspaper import Article
import time


# Load environment variables
load_dotenv()


@st.cache_data
def fetch_articles():
    topics = st.session_state.topics
    from_date = st.session_state.from_date

    topics_str = '+'.join(topics)
    url = f"https://newsapi.org/v2/everything?q={topics_str}&from={from_date}&sortBy=popularity&apiKey={os.getenv('NEWS_API_KEY')}"
    response = requests.get(url)
    articles = response.json().get('articles', [])
    return articles


def create_table_of_articles(articles):
    """Create a DataFrame from the list of articles."""

    if not articles:
        return pd.DataFrame()
    
    else:
        data = {
            "Title": [article['title'] for article in articles],
            "Author": [article['author'] for article in articles],
            "Description": [article['description'] for article in articles],
            "Source": [article['source']['name'] for article in articles],
            "Date": [article['publishedAt'] for article in articles],
            "URL": [article['url'] for article in articles]
        }
        df = pd.DataFrame(data)
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
        df['URL'] = df['URL'].astype(str)  # Ensure URL is string

        df['Include'] = True  # Add a column to indicate inclusion
        df['Include'] = df['Include'].astype(bool)  # Ensure the column is boolean

        df = df[['Include', 'Title', 'Author', 'Description', 'Source', 'Date', 'URL']]

        return df
    

def extract_article_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.title, article.text


def summarize_article(title, text, date, source):
    """Summarize an article using OpenAI's GPT-4 model with the latest API format."""
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv('OPENAI_API_KEY'),
    )
    
    prompt = f"""
    You are a podcast scriptwriter. Write a short and engaging summary of the article below in a friendly, conversational tone.
    Mention the date and the source of the article in the summary.
    Make it sound like it's being read on a technology, science and business news podcast. Keep it to 200 words or less. 
    End with a natural-sounding transition to the next article.

    TITLE: {title}
    DATE: {date}
    SOURCE: {source}

    ARTICLE:
    {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a professional podcast scriptwriter specializing in technology news."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=500
    )
    
    return response.choices[0].message.content.strip()


@st.cache_data
def generate_podcast_script(article_urls, article_sources, article_dates):
    """Generate a podcast script from the selected articles."""

    # article_urls = st.session_state.article_urls
    # article_sources = st.session_state.article_sources
    # article_dates = st.session_state.article_dates

    script_parts = []

    intro = "Welcome to your daily Battery and Electrification news roundup! Let's dive into today's top stories.\n"
    script_parts.append(intro)

    i = 0
    for url, source, date in zip(article_urls, article_sources, article_dates):
        print(f"Processing article {i + 1}/{len(article_urls)}...")
        try:
            title, content = extract_article_text(url)
            summary = summarize_article(title, content, date, source)
            script_parts.append(summary)
            time.sleep(1)  # Be polite to OpenAI’s API

        except Exception as e:
            print(f"Failed to process article: {url}")
            print("Error:", e)
            continue
        
        i += 1

    outro = "\nThat's it for today! Thanks for tuning in — we'll be back next time with more stories. Until then, stay informed and stay curious!"
    script_parts.append(outro)

    st.session_state.final_script = "\n\n".join(script_parts)

