from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import os

# Ensure database directory exists
os.makedirs("db", exist_ok=True)

# Database Setup
DATABASE_PATH = "../db/fastapi_db.db"

# Initialize DB and Create Table
def init_db():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            completed BOOLEAN NOT NULL DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Pydantic Schema
class TaskBase(BaseModel):
    title: str
    completed: bool = False

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int

# FastAPI App
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Get all tasks
@app.get("/tasks", response_model=List[Task])
def get_tasks():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, completed FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "completed": bool(row[2])} for row in rows]

# ✅ Create a new task
@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, completed) VALUES (?, ?)",
        (task.title, int(task.completed))
    )
    conn.commit()
    task_id = cursor.lastrowid
    conn.close()
    return {"id": task_id, "title": task.title, "completed": task.completed}

# ✅ Update an existing task
@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task_update: TaskCreate):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing_task = cursor.fetchone()
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    
    cursor.execute(
        "UPDATE tasks SET title = ?, completed = ? WHERE id = ?",
        (task_update.title, int(task_update.completed), task_id)
    )
    conn.commit()
    conn.close()
    return {"id": task_id, "title": task_update.title, "completed": task_update.completed}

# ✅ Delete a task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    existing_task = cursor.fetchone()
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"message": "Task deleted"}
