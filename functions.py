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
            "Author": [article.get('author', 'Unknown') for article in articles],
            "Description": [article.get('description', '') for article in articles],
            "Source": [article['source'].get('name', 'Unknown') for article in articles],
            "Date": [article['publishedAt'] for article in articles],
            "URL": [article['url'] for article in articles],
            "Include": [False for _ in articles]  # Add Include column with default False
        }
        
        df = pd.DataFrame(data)
        df['Include'] = df['Include'].astype(bool)  # Ensure boolean type
        return df
    

def extract_article_text(url):
    article = Article(url)
    article.download()
    article.parse()
    return article.title, article.text


def summarize_article(title, text, date, source, role='podcast_scriptwriter'):
    """Summarize an article using OpenAI's GPT-4 model with the latest API format."""
    client = OpenAI(
        # This is the default and can be omitted
        api_key=os.getenv('OPENAI_API_KEY'),
    )
    
    if role == 'summarizer':
        prompt_input = """You are a news article summarizer. Write a concise and engaging summary of the article below.
                        If the article is technical, maintain a professional tone. If it is general news, use a friendly and conversational tone.
                        Keep the summary to 300 words or less.
                        Mention the date and the source of the article in the summary."""

        messages_content = "You are a professional news article summarizer."

    elif role == 'podcast_scriptwriter':
        prompt_input = """You are a podcast scriptwriter. Write a short and engaging summary of the article below in a friendly but professional tone.
                        Mention the date and the source of the article in the summary.
                        Make it sound like it's being read on a serious news podcast. Keep it to 500 words or less. 
                        Minimise filler text in your generated output, and the emphasis should be on the content of the article. 
                        End with a short, natural-sounding transition to the next article."""

        messages_content = "You are a professional news article summarizer and podcast scriptwriter."

    prompt = f"""
    {prompt_input}

    TITLE: {title}
    DATE: {date}
    SOURCE: {source}

    ARTICLE:
    {text}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-16k",
        messages=[
            {
                "role": "system",
                "content": messages_content
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
def generate_podcast_script(article_urls, article_sources, article_dates, role='podcast_scriptwriter'):
    """Generate a podcast script from the selected articles."""

    # article_urls = st.session_state.article_urls
    # article_sources = st.session_state.article_sources
    # article_dates = st.session_state.article_dates

    script_parts = []

    intro = "Welcome to your news roundup! Let's dive into your selected news stories.\n"
    script_parts.append(intro)

    i = 0
    for url, source, date in zip(article_urls, article_sources, article_dates):
        st.write(f"Processing article {i + 1}/{len(article_urls)}...")
        try:
            title, content = extract_article_text(url)
            summary = summarize_article(title, content, date, source, role=role)
            script_parts.append(summary)
            time.sleep(1)  # Be polite to OpenAI’s API

        except Exception as e:
            st.write(f"Failed to process article: {url}")
            # st.write("Error:", e)
            continue
        
        i += 1

    outro = "\nThat brings us to the end of your selected stories! Thanks for tuning in — stay informed and stay curious!"
    script_parts.append(outro)

    st.session_state.final_script = "\n\n".join(script_parts)


def generate_podcast_elevenlabs():
    """Generate a podcast using ElevenLabs' TTS API."""

    from elevenlabs import play, VoiceSettings
    from elevenlabs.client import ElevenLabs

    # Initialize the client with your API key
    client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

    # Generate audio
    response = client.text_to_speech.convert(
        text=st.session_state.final_script,
        voice_id="pNInz6obpgDQGcFmaJgB",
        model_id="eleven_turbo_v2",
        output_format="mp3_44100_128",

        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
            speed=1.0,
        ),
    )
    return response


def generate_podcast_podcastfy():
    """Generate a podcast using Podcastfy's API."""

    from podcastfy.client import generate_podcast

    response = generate_podcast(urls=st.session_state.article_urls,
                                tts_model="gemini")
    
    return response


def generate_podcast_openai():
    """Generate a podcast using OpenAI's TTS API."""

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=st.session_state.final_script,
            response_format="mp3"
            # speed=1.1
        )
    return response
