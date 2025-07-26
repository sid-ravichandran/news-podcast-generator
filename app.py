import streamlit as st
import functions as fn
import os
from datetime import datetime
import pandas as pd
import session_state as ss
import io

# Setup
st.set_page_config(page_title="News Podcast Generator", page_icon=":microphone:")
st.set_page_config(layout="wide")

st.title("News Podcast Generator")
st.header(":microphone: This AI-powered app summarises and generates a podcast from the latest news articles on your chosen topics :newspaper:")

with st.container(border=True):
    st.write("**Steps to generate your summaries and podcast:**")
    st.write("1. Fill out the form to select topics and a time frame for news articles.")
    st.write("2. Review and select the articles you want to include in your podcast.")
    st.write("3. Generate the summaries of the selected articles.")
    st.write("4. Generate the podcast audio from the articles")

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
        st.rerun()

if st.session_state.form_submitted:
    if st.button(":lock: Confirm Inputs"):
        st.session_state.form_confirmed = True

################################ Fetch and Select Articles ###################################
if st.session_state.form_confirmed:
    with st.container(border=True):
        st.subheader("Step 2: Select Articles for Podcast")
        st.write("- Review articles from the list below based on features such as titles and descriptions.")
        st.write("- Select articles you want to include in your podcast using the _Include_ column.")
        st.write("- For best results and performance, select no more than 10 articles.")
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

                st.success("Articles selected successfully! You can now proceed to generating the article summaries and the podcast.")

    ################################ Generate Podcast script ###################################

    if len(st.session_state.article_urls) > 0:
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
                    response = fn.generate_podcast_openai()

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
                audio_bytes = io.BytesIO(response.content).read()
                
                # Create download button for the audio file
                st.download_button(
                    label="🎧 Download Podcast",
                    data=audio_bytes,
                    file_name=f"podcast_audio.mp3",
                    mime="audio/mp3"
                )
                
                # Display audio player
                st.audio(audio_bytes, format="audio/mp3")
                st.success("Podcast generated successfully!")

else:
    st.warning("Please fill out the form and confirm inputs to fetch articles and generate a podcast.", icon="⚠️")