import requests
import streamlit as st
from datetime import datetime

from config import API_URL, auth_headers


def show_analytics_page():
    st.title("📊 Аналитика")

    now = datetime.now()
    col1, col2 = st.columns(2)
    month = col1.number_input("Месяц", min_value=1,
                              max_value=12, value=now.month)
    year = col2.number_input("Год", min_value=2000,
                             max_value=2100, value=now.year)

    resp = requests.get(
        f"{API_URL}/expenses/summary",
        headers=auth_headers(),
        params={"month": month, "year": year},
    )

    if resp.status_code != 200:
        st.error("Ошибка загрузки данных")
        return

    data = resp.json()

    if not data:
        st.info("Расходов за этот период нет")
        return

    # Итого
    total = sum(float(d["total_amount"]) for d in data)
    st.metric("Итого за месяц", f"{total:.2f} ₽")

    st.divider()

    # Таблица
    st.subheader("По категориям")
    for d in data:
        pct = float(d["total_amount"]) / total * 100
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"**{d['category_name']}**")
        col2.write(f"{float(d['total_amount']):.2f} ₽ ({pct:.1f}%)")
        col3.write(f"{d['expense_count']} шт.")
        st.progress(pct / 100)

    st.divider()

    # График
    st.subheader("График")
    chart_data = {d["category_name"]: float(d["total_amount"]) for d in data}
    st.bar_chart(chart_data)
