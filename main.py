from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3

app = FastAPI()

DB_NAME = "users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            birth_time TEXT NOT NULL,
            front_image_url TEXT,
            side_image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class User(BaseModel):
    full_name: str
    birth_date: str
    birth_time: str
    front_image_url: Optional[str] = None
    side_image_url: Optional[str] = None

class UserInDB(User):
    id: int

@app.post("/users/", response_model=UserInDB)
def create_user(user: User):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (full_name, birth_date, birth_time, front_image_url, side_image_url) VALUES (?, ?, ?, ?, ?)",
        (user.full_name, user.birth_date, user.birth_time, user.front_image_url, user.side_image_url)
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return UserInDB(id=user_id, **user.dict())

@app.get("/users/", response_model=List[UserInDB])
def get_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, birth_date, birth_time, front_image_url, side_image_url FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [UserInDB(id=row[0], full_name=row[1], birth_date=row[2], birth_time=row[3], front_image_url=row[4], side_image_url=row[5]) for row in rows]

@app.get("/users/{user_id}", response_model=UserInDB)
def get_user(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, birth_date, birth_time, front_image_url, side_image_url FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return UserInDB(id=row[0], full_name=row[1], birth_date=row[2], birth_time=row[3], front_image_url=row[4], side_image_url=row[5])
    else:
        raise HTTPException(status_code=404, detail="User not found")
