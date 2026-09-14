import streamlit as st

st.set_page_config(page_title="Budget Tracker", page_icon="💰", layout="wide")

API_URL = "http://127.0.0.1:8000"

if "token" not in st.session_state:
    st.session_state.token = None
if "user_id" not in st.session_state:
    st.session_state.user_id = None


def auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}


def is_logged_in():
    return st.session_state.token is not None


# Навигация
if not is_logged_in():
    from auth import show_auth_page
    show_auth_page()
else:
    st.sidebar.title("💰 Budget Tracker")
    page = st.sidebar.radio(
        "Навигация",
        ["Расходы", "Категории", "Бюджеты", "Аналитика"],
    )
    if st.sidebar.button("Выйти"):
        st.session_state.token = None
        st.rerun()

    if page == "Расходы":
        from expenses import show_expenses_page
        show_expenses_page()
    elif page == "Категории":
        from categories import show_categories_page
        show_categories_page()
    elif page == "Бюджеты":
        from budgets import show_budgets_page
        show_budgets_page()
    elif page == "Аналитика":
        from analytics import show_analytics_page
        show_analytics_page()
