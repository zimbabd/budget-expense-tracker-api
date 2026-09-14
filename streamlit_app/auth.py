import requests
import streamlit as st

from config import API_URL, auth_headers


def show_auth_page():
    st.title("💰 Budget Tracker")
    tab1, tab2 = st.tabs(["Войти", "Регистрация"])

    with tab1:
        st.subheader("Вход")
        email = st.text_input("Email", key="login_email")
        password = st.text_input(
            "Пароль", type="password", key="login_password")
        if st.button("Войти"):
            if not email or not password:
                st.error("Заполни все поля")
            else:
                resp = requests.post(
                    f"{API_URL}/auth/token",
                    data={"username": email, "password": password},
                )
                if resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.success("Успешно!")
                    st.rerun()
                else:
                    st.error("Неверный email или пароль")

    with tab2:
        st.subheader("Регистрация")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input(
            "Пароль", type="password", key="reg_password")
        if st.button("Зарегистрироваться"):
            if not reg_email or not reg_password:
                st.error("Заполни все поля")
            else:
                resp = requests.post(
                    f"{API_URL}/auth/register",
                    json={"email": reg_email, "password": reg_password},
                )
                if resp.status_code == 201:
                    st.success("Аккаунт создан — войди в систему")
                else:
                    detail = resp.json().get("detail", "Ошибка")
                    st.error(detail)
