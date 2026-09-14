#форма
{
  "email": "user@example.com",
  "password": "secret123",
  "username": "testuser"
}

#войти в окружение
venv\Scripts\Activate.ps1

#поднять апку
uvicorn app.main:app --reload
