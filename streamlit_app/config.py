API_URL = "http://127.0.0.1:8000"


def auth_headers():
    import streamlit as st
    return {"Authorization": f"Bearer {st.session_state.token}"}
