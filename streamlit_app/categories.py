import requests
import streamlit as st

from config import API_URL, auth_headers


def show_categories_page():
    st.title("📂 Категории")

    resp = requests.get(f"{API_URL}/categories/", headers=auth_headers())
    categories = resp.json() if resp.status_code == 200 else []

    # Список
    if categories:
        for cat in categories:
            col1, col2 = st.columns([4, 1])
            col1.write(f"**{cat['name']}** (id: {cat['id']})")
            if col2.button("Удалить", key=f"del_cat_{cat['id']}"):
                r = requests.delete(
                    f"{API_URL}/categories/{cat['id']}", headers=auth_headers()
                )
                if r.status_code == 204:
                    st.success("Удалено")
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Ошибка"))
    else:
        st.info("Категорий пока нет")

    st.divider()

    # Создать
    st.subheader("Новая категория")
    name = st.text_input("Название")
    if st.button("Создать"):
        if not name:
            st.error("Введи название")
        else:
            r = requests.post(
                f"{API_URL}/categories/",
                headers=auth_headers(),
                json={"name": name},
            )
            if r.status_code == 201:
                st.success(f"Категория «{name}» создана")
                st.rerun()
            else:
                st.error(r.json().get("detail", "Ошибка"))
