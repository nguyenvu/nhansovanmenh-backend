from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os

from fastapi.staticfiles import StaticFiles
app = FastAPI()
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

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
    # Không nhận front_image_url, side_image_url từ client khi tạo user

class UserInDB(User):
    id: int
    front_image_url: Optional[str] = None
    side_image_url: Optional[str] = None

@app.post("/users/", response_model=UserInDB)
def create_user(user: User):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Khi tạo user, chưa có ảnh nên front_image_url, side_image_url là None
    cursor.execute(
        "INSERT INTO users (full_name, birth_date, birth_time, front_image_url, side_image_url) VALUES (?, ?, ?, ?, ?)",
        (user.full_name, user.birth_date, user.birth_time, None, None)
    )
    conn.commit()
    user_id = cursor.lastrowid
    # Trả về thông tin user, ảnh là None
    cursor.execute("SELECT id, full_name, birth_date, birth_time, front_image_url, side_image_url FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return UserInDB(id=row[0], full_name=row[1], birth_date=row[2], birth_time=row[3], front_image_url=row[4], side_image_url=row[5])

@app.get("/users/", response_model=List[UserInDB])
def get_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, birth_date, birth_time, front_image_url, side_image_url FROM users")
    rows = cursor.fetchall()
    conn.close()
    return [UserInDB(id=row[0], full_name=row[1], birth_date=row[2], birth_time=row[3], front_image_url=row[4], side_image_url=row[5]) for row in rows]


# Endpoint upload ảnh mặt trước/mặt bên
@app.post("/upload/{image_type}/")
async def upload_image(image_type: str, user_id: int, file: UploadFile = File(...)):
    if image_type not in ["front", "side"]:
        raise HTTPException(status_code=400, detail="Invalid image type")
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{image_type}_{user_id}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    # Kiểm tra user tồn tại
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=r"User not found")
    # Cập nhật đường dẫn ảnh vào DB
    if image_type == "front":
        cursor.execute("UPDATE users SET front_image_url=? WHERE id=?", (file_path, user_id))
    elif image_type == "side":
        cursor.execute("UPDATE users SET side_image_url=? WHERE id=?", (file_path, user_id))
    conn.commit()
    conn.close()
    return {"file_path": file_path}

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
