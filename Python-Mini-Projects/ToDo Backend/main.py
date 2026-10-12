from fastapi import FastAPI
import os
import psycopg2
from pydantic import BaseModel

app = FastAPI(title="ToDo App")
database_key=os.getenv("DB_KEY")

class Todo(BaseModel):
    title: str
    deadline: str

@app.post("/todos")
def add_new_todo(todo: Todo):
    conn = psycopg2.connect(database_key)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO todos (title, deadline) VALUES (%s, %s)",
        (todo.title, todo.deadline))
        conn.commit()
        return {"message": "yeni görev eklendi"}
    except Exception as e:
        conn.rollback()
        return {"Hata": str(e)}
    finally:
        c.close()
        conn.close()


@app.get("/todos")
def get_all_todos():
    conn = psycopg2.connect(database_key)
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM todos")
        todos = c.fetchall()
        return todos
    except Exception as e:
        return {"Hata": str(e)}
    finally:
        c.close()
        conn.close()

@app.delete("/todos/{id}")
def delete_todo(id: int):
    conn = psycopg2.connect(database_key)
    c = conn.cursor()
    try:
        c.execute("DELETE FROM todos WHERE id = %s", (id,))
        conn.commit()
        return {"message": "todo silindi"}
    except Exception as e:
        conn.rollback()
        return {"Hata": str(e)}
    finally:
        c.close()
        conn.close()


@app.put("/todos/{id}")
def update_todo(id: int, todo: Todo):
    conn = psycopg2.connect(database_key)
    c = conn.cursor()
    try:
        c.execute("UPDATE todos SET title = %s, deadline = %s WHERE id = %s",
        (todo.title, todo.deadline, id))
        conn.commit()
        return {"message": "bilgiler güncellendi"}
    except Exception as e:
        conn.rollback()
        return {"Hata": str(e)}
    finally:
        c.close()
        conn.close()


@app.get("/todos/{id}")
def get_specific_todo(id: int):
    conn = psycopg2.connect(database_key)
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM todos WHERE id = %s", (id,))
        result = c.fetchone()
        return result
    except Exception as e:
        return {"Hata": str(e)}
    finally:
        c.close()
        conn.close()