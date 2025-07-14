import streamlit as st
import functions as fn
import os
from datetime import datetime
import pandas as pd
import session_state as ss

# Setup
st.set_page_config(page_title="News Podcast Generator", page_icon=":microphone:")
st.set_page_config(layout="centered")

st.title("News Podcast Generator")
st.header(":microphone: This AI-powered app generates a podcast from the latest news articles on your chosen topics :newspaper:")

with st.container(border=True):
    st.write("**Steps to generate your podcast:**")
    st.write("1. Fill out the form to select topics and a time frame for news articles.")
    st.write("2. Review and select the articles you want to include in your podcast.")
    st.write("3. Generate the podcast script based on the selected articles.")
    st.write("4. Generate the podcast audio from the script")

################################ User inputs for news articles ###################################

ss.init_session_state()

# Fetch articles based on user-selected topics and time frame
# topics = ['batteries', 'electrification']
# from_date = "2025-07-01"

# Create input form
st.subheader("Step 1: News Topics and Time Frame")
with st.form("topic_form"):
    st.write("**Step 1: Select News Topics and Time Frame**")

    topics_input = st.text_input(
        "Enter topics for news articles to search for (comma-separated)",
        value="batteries, electrification",
        help="Enter topics separated by commas (e.g., batteries, electrification, solar)"
    )
    
    from_date = st.date_input(
        "Select start date for articles",
        value=datetime.now(),
        help="Select the earliest date for fetching articles"
    )
    
    submit_button = st.form_submit_button("Fetch Articles")
    
    if submit_button:
        st.session_state.topics = [topic.strip() for topic in topics_input.split(",")]
        st.session_state.from_date = from_date.strftime("%Y-%m-%d")
        st.session_state.form_submitted = True

        st.write(f"**Entered Topics:** {', '.join(st.session_state.topics)}")
        st.write(f"**Entered start Date:** {st.session_state.from_date}")

# Add a reset button outside the form
if st.session_state.form_submitted:
    if st.button(":arrows_counterclockwise: Reset Inputs"):
        st.session_state.topics = None
        st.session_state.from_date = None
        st.session_state.form_submitted = False
        st.experimental_rerun()

if st.session_state.form_submitted:
    if st.button(":lock: Confirm Inputs"):
        st.session_state.form_confirmed = True

################################ Fetch and Select Articles ###################################
if st.session_state.form_confirmed:
    with st.container(border=True):
        st.subheader("Step 2: Review and Select Articles for Podcast")
        st.write(":newspaper: **Articles Fetched**")

        articles = fn.fetch_articles()

        # DEBUG: Display the articles fetched
        # with st.expander("Show Articles Fetched"):
        #     st.write(articles)

        df_articles = fn.create_table_of_articles(articles)
        df_articles_edited = st.data_editor(df_articles)

        # DEBUG
        # df_articles_edited = st.data_editor(df_articles.iloc[[0]].reset_index(drop=True))

        article_urls = df_articles_edited[df_articles_edited['Include'] == True]['URL'].tolist()
        article_sources = df_articles_edited[df_articles_edited['Include'] == True]['Source'].tolist()
        article_dates = df_articles_edited[df_articles_edited['Include'] == True]['Date'].tolist()

        if st.button("Submit document selection"):
            if not article_urls:
                st.warning("No articles selected. Please select at least one article to generate a podcast.", icon="⚠️")
            else:
                st.session_state.article_urls = article_urls
                st.session_state.article_sources = article_sources
                st.session_state.article_dates = article_dates

                st.success("Articles selected successfully! You can now generate the podcast.")

    ################################ Generate Podcast script ###################################

    if len(st.session_state.article_urls) > 0:
        with st.container(border=True):
            st.subheader("**Step 3: Generate Podcast Script**")

            if st.button(":writing_hand: Generate Podcast Script"):
                fn.generate_podcast_script(st.session_state.article_urls, st.session_state.article_sources, st.session_state.article_dates)

                # Create folder for storing podcast scripts if it doesn't exist
                os.makedirs("scripts_folder", exist_ok=True)

                # download final_script as a text file
                script_file_path = f"scripts_folder/daily_podcast_{st.session_state.from_date}.txt"
                with open(script_file_path, "w") as f:
                    f.write(st.session_state.final_script)

                st.session_state.script_generated = True
                st.success("Podcast script generated and saved successfully!")

                with st.expander("Show Podcast Script"):
                    st.markdown(st.session_state.final_script)

    ################################# Generate Podcast ###################################

    if st.session_state.script_generated:
        with st.container(border=True):
            st.subheader("**Step 4: Generate Podcast Audio**")

            from elevenlabs import play, VoiceSettings
            from elevenlabs.client import ElevenLabs

            if st.button(":microphone: Generate Podcast"):
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

                # Create audio folder if it doesn't exist
                os.makedirs("audio_folder", exist_ok=True)
                save_file_path = f"audio_folder/daily_podcast_{st.session_state.from_date}.mp3"

                # Save the audio file locally
                with open(save_file_path, "wb") as f:
                    for chunk in response:
                        if chunk:
                            f.write(chunk)

                st.success("Podcast generated and saved successfully!")

                # Play podcast audio
                # play(response)
                # st.audio("daily_podcast.mp3")

else:
    st.warning("Please fill out the form to fetch articles and generate a podcast.", icon="⚠️")