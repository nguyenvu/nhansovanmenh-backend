from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
from fastapi.staticfiles import StaticFiles
from deepface import DeepFace
from fastapi.responses import JSONResponse
app = FastAPI()
app.mount("/uploads", StaticFiles(directory=os.path.abspath("uploads")), name="uploads")

DB_NAME = "users.db"


def migrate_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    columns = [
        ("front_age", "INTEGER"),
        ("front_gender", "TEXT"),
        ("front_dominant_race", "TEXT"),
        ("front_dominant_emotion", "TEXT"),
        ("front_comment", "TEXT"),
        ("side_age", "INTEGER"),
        ("side_gender", "TEXT"),
        ("side_dominant_race", "TEXT"),
        ("side_dominant_emotion", "TEXT"),
        ("side_comment", "TEXT")
    ]
    for col, coltype in columns:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col} {coltype}")
        except sqlite3.OperationalError as e:
            if f"duplicate column name: {col}" in str(e) or "already exists" in str(e):
                pass  # Đã có cột này rồi
            else:
                raise
    conn.commit()
    conn.close()

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
    migrate_db()

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
    file_path = os.path.abspath(os.path.join(upload_dir, filename))
    with open(file_path, "wb") as f:
        f.write(await file.read())
    # Kiểm tra file tồn tại và log đường dẫn sau khi ghi file
    if not os.path.exists(file_path):
        error = f"File not found: {file_path}"
        return {"file_path": file_path, "deepface_result": None, "error": error}
    print(f"[DeepFace] Đang phân tích file: {file_path}")
    # Kiểm tra user tồn tại
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE id=?", (user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail=r"User not found")
    # Phân tích khuôn mặt bằng DeepFace
    error = None
    result = {}
    try:
        analysis = DeepFace.analyze(img_path=file_path, actions=["age", "gender", "race", "emotion"], enforce_detection=False)
        if isinstance(analysis, list):
            analysis = analysis[0]
        result = {
            "age": analysis.get("age"),
            "gender": analysis.get("dominant_gender", analysis.get("gender")),
            "dominant_race": analysis.get("dominant_race"),
            "dominant_emotion": analysis.get("dominant_emotion"),
            "comment": f"Khuôn mặt dự đoán: tuổi {analysis.get('age')}, giới tính {analysis.get('dominant_gender', analysis.get('gender'))}, sắc tộc {analysis.get('dominant_race')}, cảm xúc {analysis.get('dominant_emotion')}"
        }
    except Exception as e:
        error = str(e)
        result = {"age": None, "gender": None, "dominant_race": None, "dominant_emotion": None, "comment": None, "error": error}
    # Cập nhật đường dẫn ảnh và kết quả DeepFace vào DB
    if image_type == "front":
        cursor.execute("UPDATE users SET front_image_url=?, front_age=?, front_gender=?, front_dominant_race=?, front_dominant_emotion=?, front_comment=? WHERE id=?",
            (file_path, result.get("age"), result.get("gender"), result.get("dominant_race"), result.get("dominant_emotion"), result.get("comment"), user_id))
    elif image_type == "side":
        cursor.execute("UPDATE users SET side_image_url=?, side_age=?, side_gender=?, side_dominant_race=?, side_dominant_emotion=?, side_comment=? WHERE id=?",
            (file_path, result.get("age"), result.get("gender"), result.get("dominant_race"), result.get("dominant_emotion"), result.get("comment"), user_id))
    conn.commit()
    conn.close()
    return {
        "file_path": file_path,
        "deepface_result": result,
        "error": error
    }

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
    

# API trả kết quả nhận diện khuôn mặt (front) cho user
@app.get("/face-result/{user_id}")
def get_face_result(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT front_age, front_gender, front_dominant_race FROM users WHERE id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return JSONResponse(status_code=404, content={"error": "User not found"})
    return {
        "user_id": user_id,
        "front_age": row[0],
        "front_gender": row[1],
        "front_race": row[2]
    }
