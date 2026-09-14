import requests
import streamlit as st
from datetime import datetime, date

from config import API_URL, auth_headers


def show_expenses_page():
    st.title("💸 Расходы")

    # Получаем категории для фильтров и формы
    cats_resp = requests.get(f"{API_URL}/categories/", headers=auth_headers())
    categories = cats_resp.json() if cats_resp.status_code == 200 else []
    cat_map = {c["name"]: c["id"] for c in categories}

    # Фильтры
    st.subheader("Фильтры")
    col1, col2, col3 = st.columns(3)
    cat_filter_options = ["Все"] + list(cat_map.keys())
    selected_cat = col1.selectbox("Категория", cat_filter_options)
    date_from = col2.date_input("Дата от", value=None)
    date_to = col3.date_input("Дата до", value=None)

    params = {}
    if selected_cat != "Все":
        params["category_id"] = cat_map[selected_cat]
    if date_from:
        params["date_from"] = str(date_from)
    if date_to:
        params["date_to"] = str(date_to)

    # Список расходов
    resp = requests.get(f"{API_URL}/expenses/",
                        headers=auth_headers(), params=params)
    expenses = resp.json() if resp.status_code == 200 else []

    if expenses:
        for e in expenses:
            cat_name = next((c["name"] for c in categories if c["id"]
                            == e["category_id"]), str(e["category_id"]))
            col1, col2 = st.columns([5, 1])
            col1.write(
                f"**{e['expense_date']}** | {cat_name} | "
                f"**{e['amount']}** | {e['description'] or '—'}"
                + (" 🔁" if e["is_recurring"] else "")
            )
            if col2.button("Удалить", key=f"del_exp_{e['id']}"):
                r = requests.delete(
                    f"{API_URL}/expenses/{e['id']}", headers=auth_headers())
                if r.status_code == 204:
                    st.success("Удалено")
                    st.rerun()
                else:
                    st.error(r.json().get("detail", "Ошибка"))
    else:
        st.info("Расходов нет")

    st.divider()

    # Создать расход
    st.subheader("Новый расход")
    if not categories:
        st.warning("Сначала создай категорию")
        return

    selected_new = st.selectbox("Категория", list(
        cat_map.keys()), key="new_exp_cat")
    amount = st.number_input("Сумма", min_value=0.01, step=0.01)
    description = st.text_input("Описание (необязательно)")
    exp_date = st.date_input("Дата", value=date.today())
    is_recurring = st.checkbox("Повторяющийся")

    if st.button("Добавить расход"):
        r = requests.post(
            f"{API_URL}/expenses/",
            headers=auth_headers(),
            json={
                "category_id": cat_map[selected_new],
                "amount": amount,
                "description": description or None,
                "expense_date": str(exp_date),
                "is_recurring": is_recurring,
            },
        )
        if r.status_code == 201:
            data = r.json()
            if data.get("budget_warning"):
                st.warning(f"⚠️ {data['budget_warning']}")
            else:
                st.success("Расход добавлен")
            st.rerun()
        else:
            st.error(r.json().get("detail", "Ошибка"))

    st.divider()

    # Генерация recurring
    st.subheader("🔁 Сгенерировать повторяющиеся расходы")
    now = datetime.now()
    col1, col2 = st.columns(2)
    rec_month = col1.number_input(
        "Месяц", min_value=1, max_value=12, value=now.month, key="rec_m")
    rec_year = col2.number_input(
        "Год", min_value=2000, max_value=2100, value=now.year, key="rec_y")
    if st.button("Сгенерировать"):
        r = requests.post(
            f"{API_URL}/expenses/recurring/generate",
            headers=auth_headers(),
            params={"month": rec_month, "year": rec_year},
        )
        if r.status_code == 201:
            created = r.json()
            if created:
                st.success(f"Создано {len(created)} расходов")
            else:
                st.info("Все повторяющиеся расходы уже сгенерированы")
            st.rerun()
        else:
            st.error(r.json().get("detail", "Ошибка"))
