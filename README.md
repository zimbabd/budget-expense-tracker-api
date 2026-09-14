```markdown
# Budget & Expense Tracker API

REST API для управления личными финансами. Позволяет отслеживать расходы, устанавливать бюджеты по категориям и получать аналитику по тратам.

## Стек

- **Python 3.11+**
- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0** — ORM
- **MySQL** — база данных (через XAMPP)
- **Alembic** — миграции
- **JWT** — аутентификация (python-jose + bcrypt)
- **Pydantic v2** — валидация данных

## Возможности

- Регистрация и аутентификация пользователей (JWT)
- CRUD для категорий расходов
- CRUD для расходов с фильтрацией по категории, дате, типу
- Бюджеты по категориям и общий месячный лимит
- Предупреждения при превышении бюджета (в ответе на создание расхода)
- Статус бюджетов: потрачено, осталось, процент использования
- Аналитика расходов по категориям за месяц
- Автогенерация повторяющихся расходов

## Установка и запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/your-username/budget-expense-tracker-api.git
cd budget-expense-tracker-api
```

### 2. Создать виртуальное окружение

```bash
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate     # Linux/Mac
```

### 3. Установить зависимости

```bash
pip install -r requirements.txt
```

### 4. Настроить переменные окружения

Скопируй `.env.example` в `.env` и заполни:

```bash
cp .env.example .env
```

```env
DATABASE_URL=mysql+pymysql://root:@localhost:3306/budget_tracker
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 5. Создать базу данных

В MySQL создай базу `budget_tracker`, затем примени миграции:

```bash
alembic upgrade head
```

### 6. Запустить сервер

```bash
uvicorn app.main:app --reload
```

API доступен на `http://127.0.0.1:8000`  
Документация (Swagger UI): `http://127.0.0.1:8000/docs`

## Эндпоинты

### Auth
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/token` | Получить JWT токен |

### Categories
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/categories/` | Список категорий |
| POST | `/categories/` | Создать категорию |
| GET | `/categories/{id}` | Получить категорию |
| PUT | `/categories/{id}` | Обновить категорию |
| DELETE | `/categories/{id}` | Удалить категорию |

### Expenses
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/expenses/` | Список расходов (фильтры: category_id, date_from, date_to, is_recurring) |
| POST | `/expenses/` | Создать расход (возвращает budget_warning если превышен лимит) |
| GET | `/expenses/summary` | Аналитика по категориям за месяц/год |
| POST | `/expenses/recurring/generate` | Сгенерировать повторяющиеся расходы |
| GET | `/expenses/{id}` | Получить расход |
| PATCH | `/expenses/{id}` | Обновить расход |
| DELETE | `/expenses/{id}` | Удалить расход |

### Budgets
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/budgets/` | Список бюджетов (фильтры: month, year, category_id) |
| POST | `/budgets/` | Создать бюджет |
| GET | `/budgets/status` | Статус бюджетов за месяц (потрачено, осталось, %) |
| GET | `/budgets/{id}` | Получить бюджет |
| DELETE | `/budgets/{id}` | Удалить бюджет |

## Примеры запросов

### Регистрация
```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

### Получить токен
```bash
curl -X POST http://127.0.0.1:8000/auth/token \
  -d "username=user@example.com&password=secret123"
```

### Создать расход
```bash
curl -X POST http://127.0.0.1:8000/expenses/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"category_id": 1, "amount": 50.00, "description": "Продукты", "expense_date": "2026-09-14", "is_recurring": false}'
```

### Аналитика за месяц
```bash
curl -X GET "http://127.0.0.1:8000/expenses/summary?month=9&year=2026" \
  -H "Authorization: Bearer <token>"
```
