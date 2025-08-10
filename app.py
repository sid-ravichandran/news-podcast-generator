import streamlit as st
import functions as fn
import os
from datetime import datetime, timedelta
import pandas as pd
import session_state as ss
import io

# Setup
st.markdown("""
    <style>
    .main {
        padding: 2rem;
        background-color: #f8f9fa;
    }
    .stTitle {
        color: #1e3d59;
        font-size: 3rem !important;
        padding-bottom: 1rem;
    }
    .stHeader {
        color: #17a2b8;
        font-size: 1.8rem !important;
    }
    .stContainer {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #b22222;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
            
    /* Article card styling */
    [data-testid="stContainer"] {
        background-color: white;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stContainer"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* Button styling */
    [data-testid="baseButton-primary"] {
        background-color: #17a2b8;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 2rem;
        font-weight: bold;
    }
            
    /* Updated Checkbox styling for dark mode compatibility */
    [data-testid="stCheckbox"] {
        background-color: transparent;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        color: inherit;
    }
    
    /* Style for checkbox label */
    [data-testid="stCheckbox"] label {
        color: inherit !important;
    }
    
    /* Style for checkbox input */
    [data-testid="stCheckbox"] input {
        accent-color: #17a2b8;
    }
    
    /* Article card additional styling for dark mode */
    [data-testid="stContainer"] {
        background-color: var(--background-color);
        color: var(--text-color);
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    /* Ensure text remains visible in dark mode */
    [data-testid="stContainer"] * {
        color: inherit;
    }
    </style>
    """, unsafe_allow_html=True)

st.set_page_config(
    page_title="NewsVox | AI News Podcast Generator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title section with columns
col1, col2 = st.columns([1, 3])
with col1:
    st.image("https://img.icons8.com/clouds/200/000000/microphone.png", width=100)
with col2:
    st.title("NewsVox 🎙️: AI News Podcast Generator")
    st.markdown("*Transform text to talk: Your personalized news podcast creator* 🎙️📰")

with st.container():
    st.markdown("""
    ### How It Works 🔄
    1. 📝 **Input Topics**: Enter your interests and timeframe
    2. 📰 **Select Articles**: Choose from relevant news sources
    3. ✍️ **Generate Summaries**: AI creates concise article summaries
    4. 🎧 **Create Podcast**: Convert summaries to audio
    """)

################################ User inputs for news articles ###################################

ss.init_session_state()

# Fetch articles based on user-selected topics and time frame
# topics = ['batteries', 'electrification']
# from_date = "2025-07-01"

# Create input form
st.subheader("Step 1: News Topics and Time Frame")
with st.form("topic_form"):
    st.markdown("### 🎯 Step 1: Select Your News Preferences")

    topics_input = st.text_input(
        "📚 Topics of Interest",
        value=None,
        placeholder="Example topics: batteries, electrification, ...",
        help="Separate topics with commas (e.g., batteries, electrification, solar)"
    )
    
    from_date = st.date_input(
        "📅 From Date for search (set to a date in the past)",
        value=datetime.now() - timedelta(weeks=2),
        help="Select start date for news articles"
    )
    
    submit_button = st.form_submit_button("🔍 Find Articles")
    
    if submit_button:
        st.session_state.topics = [topic.strip() for topic in topics_input.split(",")] if topics_input else None
        st.session_state.from_date = from_date.strftime("%Y-%m-%d")
        st.session_state.form_submitted = True

        if (st.session_state.topics is None) or (st.session_state.from_date is None):
            st.warning("Please enter valid topics and/or date.", icon="⚠️")
        else:
            st.write(f"**Entered Topics:** {', '.join(st.session_state.topics)}")
            st.write(f"**Entered start Date:** {st.session_state.from_date}")

# Add a reset button outside the form
if st.session_state.form_submitted:
    if st.button(":arrows_counterclockwise: Reset Inputs"):
        st.session_state.topics = None
        st.session_state.from_date = None
        st.session_state.form_submitted = False
        st.session_state.articles_selected = False
        st.rerun()

if st.session_state.form_submitted:
    if st.button(":lock: Confirm Inputs"):
        if (st.session_state.topics != None) & (st.session_state.from_date != None):
            st.session_state.form_confirmed = True
        else:
            st.session_state.form_confirmed = False
            st.warning("No valid inputs provided, please **Reset Inputs** and try a different search.", icon="⚠️")

################################ Fetch and Select Articles ###################################
if st.session_state.form_confirmed:
    with st.container(border=True):
        st.markdown("""
        ### Step 2: 📰 Select from Available Articles
        Select articles for your podcast by checking the boxes in the 'Include' column.
        **For best results, please select no more than 10 articles**
        """)

        st.markdown("""
        <style>
        .dataframe {
            font-family: 'Arial', sans-serif;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.9em;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        }
        </style>
        """, unsafe_allow_html=True)

        with st.spinner("Fetching articles..."):
            articles = fn.fetch_articles(st.session_state.topics, st.session_state.from_date)

        # DEBUG: Display the articles fetched
        # with st.expander("Show Articles Fetched"):
        #     st.write(articles)

        df_articles = fn.create_table_of_articles(articles)

        # if len(df_articles) > 0:
        #     st.success(f"Found {len(df_articles)} articles")
        #     df_articles_edited = st.data_editor(df_articles)

        #     # DEBUG
        #     # df_articles_edited = st.data_editor(df_articles.iloc[[0]].reset_index(drop=True))

        #     article_urls = df_articles_edited[df_articles_edited['Include'] == True]['URL'].tolist()[:10]
        #     article_sources = df_articles_edited[df_articles_edited['Include'] == True]['Source'].tolist()[:10]
        #     article_dates = df_articles_edited[df_articles_edited['Include'] == True]['Date'].tolist()[:10]

        #     if st.button("Submit article selection"):
        #         if not article_urls:
        #             st.warning("No articles selected. Please select at least one article to generate a podcast.", icon="⚠️")
        #         else:
        #             st.session_state.article_urls = article_urls
        #             st.session_state.article_sources = article_sources
        #             st.session_state.article_dates = article_dates
        #             st.session_state.articles_selected = True

        #             st.success("Articles selected successfully! You can now proceed to generating the article summaries and the podcast.")
        # else:
        #     st.warning("No articles found. Please **Reset Inputs** and try a different search.", icon="⚠️")

        if len(df_articles) > 0:
            st.success(f"📚 Showing top {len(df_articles)} articles")
            
            st.markdown("""
            **Articles are sorted by:**
            1. Source reliability (major news outlets)
            2. Relevance to your topics
            3. Publication date
            """)
            
            # Create three columns for article cards
            cols = st.columns(3)
            
            # Track selected articles
            if 'selected_articles' not in st.session_state:
                st.session_state.selected_articles = set()
            
            for idx, row in df_articles.iterrows():
                with cols[idx % 3]:
                    # Create a card-like container
                    with st.container(border=True):
                        # Article title as header
                        st.markdown(f"#### {row['Title'][:100]}...")
                        
                        # Source and date info
                        st.markdown(f"""
                        <div style='display: flex; justify-content: space-between; color: #666;'>
                            <span>📰 {row['Source']}</span>
                            <span>📅 {pd.to_datetime(row['Date']).strftime('%Y-%m-%d')}</span>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Description with truncation
                        st.markdown(f"*{row['Description'][:150]}...*")
                        
                        # Author info if available
                        if row['Author'] and row['Author'] != 'Unknown':
                            st.markdown(f"✍️ By: {row['Author']}")
                        
                        # Selection checkbox
                        is_selected = st.checkbox(
                            "Select this article",
                            key=f"article_{idx}",
                            value=idx in st.session_state.selected_articles
                        )
                        
                        if is_selected:
                            st.session_state.selected_articles.add(idx)
                        else:
                            st.session_state.selected_articles.discard(idx)
                        
                        # Read more link
                        st.markdown(f"[🔗 Read full article]({row['URL']})")
            
            # Selection summary and warning
            n_selected = len(st.session_state.selected_articles)
            if n_selected > 0:
                st.info(f"📝 You have selected {n_selected} article{'s' if n_selected > 1 else ''}")
                if n_selected > 10:
                    st.warning("⚠️ For best results, please select no more than 10 articles")
            
            # Submit button for article selection
            if st.button("✅ Confirm Selection", type="primary"):
                if n_selected == 0:
                    st.warning("No articles selected. Please select at least one article to generate a podcast.", icon="⚠️")
                else:
                    # Get selected articles data
                    selected_indices = list(st.session_state.selected_articles)[:10]  # Limit to first 10
                    selected_df = df_articles.iloc[selected_indices]
                    
                    st.session_state.article_urls = selected_df['URL'].tolist()
                    st.session_state.article_sources = selected_df['Source'].tolist()
                    st.session_state.article_dates = selected_df['Date'].tolist()
                    st.session_state.articles_selected = True
                    
                    st.success("✨ Articles selected successfully! You can now proceed to generating the article summaries and podcast.")
        else:
            st.warning("No articles found. Please **Reset Inputs** and try a different search.", icon="⚠️")

    ################################ Generate Podcast script ###################################

    if st.session_state.articles_selected == True:
        with st.container(border=True):
            st.subheader("**Step 3: Generate Article Summaries**")

            if st.button(":writing_hand: Generate News Summaries"):
                with st.spinner("Generating news summaries..."):
                    fn.generate_podcast_script(st.session_state.article_urls, st.session_state.article_sources, st.session_state.article_dates,
                                               role='podcast_scriptwriter')

                # # DEPRECATED - Automatically download final_script as a text file
                # # Create folder for storing podcast scripts if it doesn't exist
                # os.makedirs("scripts_folder", exist_ok=True)
                # script_file_path = f"scripts_folder/daily_podcast_{st.session_state.from_date}.txt"
                # with open(script_file_path, "w") as f:
                #     f.write(st.session_state.final_script)

                # Add download button for the news summaries
                st.download_button(
                    label="Download News Summaries",
                    data=st.session_state.final_script,
                    file_name=f"news_summaries_podcast.txt",
                    mime="text/plain"
                )

                st.session_state.script_generated = True

            if st.session_state.script_generated == True:
                st.success("News summaries generated!")
                
                with st.expander("Show News Summaries"):
                    st.markdown(st.session_state.final_script)

    ################################# Generate Podcast ###################################

    if st.session_state.script_generated:
        with st.container(border=True):
            st.subheader("**Step 4: Generate Podcast Audio**")

            if st.button(":microphone: Generate Podcast"):
                with st.spinner("Generating audio..."):
                    ####################### Elevanlabs - do not use - limited free tier #######################
                    # response = fn.generate_podcast_elevenlabs()

                    ####################### Podcastfy - do not use - file permission errors ###################
                    # response = fn.generate_podcast_podcastfy()

                    ####################### OpenAI TTS - use this for generating podcast audio ################
                    audio_buffer = fn.generate_podcast_openai()

                ####################### DEPRECATED - Automatically save the podcast audio file ############
                # # Create audio folder if it doesn't exist
                # os.makedirs("audio_folder", exist_ok=True)
                # save_file_path = f"audio_folder/daily_podcast_{st.session_state.from_date}.mp3"

                # # Save the audio file locally
                # with open(save_file_path, "wb") as f:
                #     for chunk in response:
                #         if chunk:
                #             f.write(chunk)

                # Combine all chunks into a single bytes object
                # audio_bytes = io.BytesIO(response.content).read()
                
                # Create download button for the audio file
                st.download_button(
                    label="🎧 Download Podcast",
                    data=audio_buffer,
                    file_name=f"podcast_audio.mp3",
                    mime="audio/mp3"
                )
                
                # Display audio player
                st.audio(audio_buffer, format="audio/mp3")
                st.success("Podcast generated successfully!")

else:
    st.warning("Please fill out the form and confirm inputs to fetch articles and generate a podcast.", icon="⚠️")

# Add at the bottom of the file
st.markdown("""
---
<div style='text-align: center; color: #666;'>
    <p>Made with ❤️ by Sid Ravichandran</p>
    <p>Powered by OpenAI, News API, and Streamlit</p>
</div>
""", unsafe_allow_html=True)
