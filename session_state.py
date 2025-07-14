import streamlit as st
import functions as fn

def init_session_state():
    """Initialize session state variables."""

    if 'topics' not in st.session_state:
        st.session_state.topics = None

    if 'from_date' not in st.session_state:
        st.session_state.from_date = None

    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False

    if 'form_confirmed' not in st.session_state:
        st.session_state.form_confirmed = False

    if 'article_urls' not in st.session_state:
        st.session_state.article_urls = []

    if 'article_sources' not in st.session_state:
        st.session_state.article_sources = []

    if 'article_dates' not in st.session_state:
        st.session_state.article_dates = []

    if 'script_generated' not in st.session_state:
        st.session_state.script_generated = False

    if 'final_script' not in st.session_state:
        st.session_state.final_script = None
