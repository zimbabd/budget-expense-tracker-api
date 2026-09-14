import requests
import streamlit as st
from datetime import datetime

from config import API_URL, auth_headers


def show_budgets_page():
    st.title("🎯 Бюджеты")

    now = datetime.now()
    col1, col2 = st.columns(2)
    month = col1.number_input("Месяц", min_value=1,
                              max_value=12, value=now.month)
    year = col2.number_input("Год", min_value=2000,
                             max_value=2100, value=now.year)

    # Статус бюджетов
    st.subheader("Статус")
    resp = requests.get(
        f"{API_URL}/budgets/status",
        headers=auth_headers(),
        params={"month": month, "year": year},
    )
    if resp.status_code == 200:
        statuses = resp.json()
        if statuses:
            for s in statuses:
                label = f"Категория {s['category_id']}" if s['category_id'] else "Общий"
                pct = s['usage_percent']
                color = "🔴" if s['is_exceeded'] else (
                    "🟡" if pct >= 80 else "🟢")
                st.markdown(f"{color} **{label}** — {pct}% использовано")
                st.progress(min(pct / 100, 1.0))
                st.caption(
                    f"Лимит: {s['limit_amount']} | "
                    f"Потрачено: {s['spent_amount']} | "
                    f"Осталось: {s['remaining_amount']}"
                )
        else:
            st.info("Бюджетов за этот период нет")

    st.divider()

    # Список бюджетов
    st.subheader("Все бюджеты")
    resp2 = requests.get(
        f"{API_URL}/budgets/",
        headers=auth_headers(),
        params={"month": month, "year": year},
    )
    budgets = resp2.json() if resp2.status_code == 200 else []
    if budgets:
        for b in budgets:
            col1, col2 = st.columns([4, 1])
            label = f"Категория {b['category_id']}" if b['category_id'] else "Общий"
            col1.write(
                f"**{label}** — лимит {b['limit_amount']} ({b['month']}/{b['year']})")
            if col2.button("Удалить", key=f"del_bud_{b['id']}"):
                r = requests.delete(
                    f"{API_URL}/budgets/{b['id']}", headers=auth_headers())
                if r.status_code == 204:
                    st.success("Удалено")
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Ошибка"))
    else:
        st.info("Бюджетов нет")

    st.divider()

    # Создать бюджет
    st.subheader("Новый бюджет")
    cats_resp = requests.get(f"{API_URL}/categories/", headers=auth_headers())
    categories = cats_resp.json() if cats_resp.status_code == 200 else []
    cat_options = {"Общий (без категории)": None}
    cat_options.update({c["name"]: c["id"] for c in categories})

    selected = st.selectbox("Категория", list(cat_options.keys()))
    limit = st.number_input("Лимит", min_value=0.01, step=0.01)
    b_month = st.number_input("Месяц", min_value=1,
                              max_value=12, value=now.month, key="bm")
    b_year = st.number_input("Год", min_value=2000,
                             max_value=2100, value=now.year, key="by")

    if st.button("Создать бюджет"):
        r = requests.post(
            f"{API_URL}/budgets/",
            headers=auth_headers(),
            json={
                "category_id": cat_options[selected],
                "limit_amount": limit,
                "month": b_month,
                "year": b_year,
            },
        )
        if r.status_code == 201:
            st.success("Бюджет создан")
            st.rerun()
        else:
            st.error(r.json().get("detail", "Ошибка"))
