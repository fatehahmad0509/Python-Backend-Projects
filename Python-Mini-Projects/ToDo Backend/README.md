# 📝 FastAPI ToDo API

A simple RESTful ToDo API built with **FastAPI** and **PostgreSQL**. This project demonstrates basic CRUD operations using raw SQL with `psycopg2`.

## ✨ Features

* Create a new todo
* Get all todos
* Get a specific todo by ID
* Update an existing todo
* Delete a todo
* PostgreSQL integration
* Error handling with `try/except/finally`
* SQL Injection protection using parameterized queries

## 🛠️ Technologies

* Python
* FastAPI
* PostgreSQL
* psycopg2
* Pydantic

## 📦 Installation

1. Clone the repository:

```bash
git clone https://github.com/your-username/todo-api.git
cd todo-api
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file and add your database connection string:

```env
DB_KEY=postgresql://username:password@localhost:5432/database_name
```

4. Start the server:

```bash
uvicorn main:app --reload
```

The API will be available at:

```
http://127.0.0.1:8000
```

Interactive API documentation:

```
http://127.0.0.1:8000/docs
```

## 📚 API Endpoints

| Method | Endpoint      | Description       |
| ------ | ------------- | ----------------- |
| POST   | `/todos`      | Create a new todo |
| GET    | `/todos`      | Get all todos     |
| GET    | `/todos/{id}` | Get a todo by ID  |
| PUT    | `/todos/{id}` | Update a todo     |
| DELETE | `/todos/{id}` | Delete a todo     |

## 📄 Example Request

**POST /todos**

```json
{
  "title": "Learn FastAPI",
  "deadline": "2026-07-10"
}
```

## 📁 Project Structure

```text
.
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## 🚀 Future Improvements

* JWT Authentication
* Password Hashing
* Response Models
* HTTP Exception Handling
* Pagination
* Docker Support
* Unit Tests
* SQLAlchemy ORM
* Async Database Support

## 📜 License

This project is open-source and available for educational purposes.
