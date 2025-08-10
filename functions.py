import streamlit as st
import requests
import os
from dotenv import load_dotenv
import pandas as pd
from openai import OpenAI
from newspaper import Article
import time
import io
from pydub import AudioSegment


# Load environment variables
load_dotenv()


@st.cache_data
def fetch_articles(topics, from_date):
    # topics = st.session_state.topics
    # from_date = st.session_state.from_date

    if not topics or not from_date:
        return []
    
    topics_str = '+'.join(topics)
    # url = f"https://newsapi.org/v2/everything?q={topics_str}&from={from_date}&sortBy=popularity&apiKey={os.getenv('NEWS_API_KEY')}"
    url = (f"https://newsapi.org/v2/everything?"
           f"q={topics_str}"
           f"&from={from_date}"
           f"&language=en"  # English only
           f"&pageSize=21"  # Limit to 21 articles
           f"&sortBy=relevancy"  # Sort by relevancy
           # f"&domains=bloomberg.com,reuters.com,apnews.com,bbc.com,wsj.com,ft.com,nytimes.com"  # Reliable sources
           f"&apiKey={os.getenv('NEWS_API_KEY')}")

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for bad responses
        articles = response.json().get('articles', [])

        # Additional sorting based on source reliability and popularity
        source_weights = {
            'Reuters': 10,
            'Bloomberg': 9,
            'The Wall Street Journal': 8,
            'BBC News': 8,
            'The New York Times': 8,
            'Financial Times': 8,
            'Associated Press': 8
        }
        
        # Sort articles by source reliability
        articles.sort(key=lambda x: source_weights.get(x['source']['name'], 0), reverse=True)

        return articles[:21]
    
    except Exception as e:
        st.error(f"Error fetching articles: {str(e)}")
        return []


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
        col_order = ['Include', 'Title', 'Description', 'Source'] + [col for col in df.columns if col not in ['Include', 'Title', 'Description', 'Source']]
        return df[col_order]
    

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
                        Keep the summary to 500 words or less.
                        Mention the date and the source of the article in the summary."""

        messages_content = "You are a professional news article summarizer."

    elif role == 'podcast_scriptwriter':
        prompt_input = """You are a podcast scriptwriter. Write an engaging summary of the article below in a friendly but professional tone.
                        Mention the date and the source of the article in the summary. The podcast is unnamed so don't generate a name or mention it.
                        Make it sound like it's being read on a serious news podcast. Don't make it too short, the summary should be up to 500 words long but not more. 
                        Minimise filler text in your generated output, and the emphasis should be on the content of the article. Specifically try to bring out examples, numeric data and figures if possible.
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


# def generate_podcast_openai():
#     """Generate a podcast using OpenAI's TTS API."""

#     from openai import OpenAI
#     client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

#     response = client.audio.speech.create(
#             model="tts-1",
#             voice="alloy",
#             input=st.session_state.final_script,
#             response_format="mp3"
#             # speed=1.1
#         )
#     return response

def generate_podcast_openai():
    """Generate a podcast using OpenAI's TTS API keeping char limit in mind."""

    def chunk_text(text, max_chars=4096):
        chunks = []
        while len(text) > max_chars:
            split_at = text.rfind(' ', 0, max_chars)
            if split_at == -1:
                split_at = max_chars
            chunks.append(text[:split_at])
            text = text[split_at:].lstrip()
        if text:
            chunks.append(text)
        return chunks
    
    def merge_audio_segments(segments):
        combined = AudioSegment.empty()
        for segment in segments:
            combined += segment
        return combined

    text = st.session_state.final_script
    chunks = chunk_text(text)
    audio_segments = []

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    for chunk in chunks:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=chunk,
            response_format="mp3"
            # speed=1.1
        )
        mp3_bytes = io.BytesIO(response.content)
        segment = AudioSegment.from_file(mp3_bytes, format="mp3")
        audio_segments.append(segment)

    final_audio = merge_audio_segments(audio_segments)

    # Export merged audio to BytesIO
    output_buffer = io.BytesIO()
    final_audio.export(output_buffer, format="mp3")
    output_buffer.seek(0)

    return output_buffer
