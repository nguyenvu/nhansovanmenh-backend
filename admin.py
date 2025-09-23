from fastapi import FastAPI, Depends, HTTPException, status, Request
import os
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, RedirectResponse
import secrets
import sqlite3
from fastapi.templating import Jinja2Templates

app = FastAPI()
security = HTTPBasic()
DB_NAME = "users.db"
templates = Jinja2Templates(directory="templates")

ADMIN_USERNAME = "admin123"
ADMIN_PASSWORD = "admin123"

# Simple authentication dependency
def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, username: str = Depends(authenticate)):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, birth_date, birth_time, front_image_url, side_image_url, front_age, front_gender, front_dominant_race, front_dominant_emotion, front_comment, side_age, side_gender, side_dominant_race, side_dominant_emotion, side_comment FROM users")
    users = cursor.fetchall()
    conn.close()
    def basename(path):
        return os.path.basename(path) if path else ""
    # Jinja2 không có filter basename mặc định, truyền vào context
    return templates.TemplateResponse("admin_list.html", {"request": request, "users": users, "basename": basename})

@app.get("/admin/delete/{user_id}")
def delete_user(user_id: int, username: str = Depends(authenticate)):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT front_image_url, side_image_url FROM users WHERE id=?", (user_id,))
    img_row = cursor.fetchone()
    if img_row:
        for img_path in img_row:
            if img_path and os.path.exists(img_path):
                try:
                    os.remove(img_path)
                except Exception:
                    pass
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/edit/{user_id}", response_class=HTMLResponse)
def edit_user_page(user_id: int, username: str = Depends(authenticate)):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, birth_date, birth_time, front_image_url, side_image_url FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        return HTMLResponse(content="User not found", status_code=404)
    html = f"""
    <html><head><title>Edit User</title></head><body>
    <h2>Edit User</h2>
    <form method='post' action='/admin/edit/{user[0]}'>
    Name: <input name='full_name' value='{user[1]}'/><br>
    Birth Date: <input name='birth_date' value='{user[2]}'/><br>
    Birth Time: <input name='birth_time' value='{user[3]}'/><br>
    Front Image URL: <input name='front_image_url' value='{user[4]}'/><br>
    Side Image URL: <input name='side_image_url' value='{user[5]}'/><br>
    <input type='submit' value='Save'/>
    </form>
    <a href='/admin'>Back to list</a></body></html>
    """
    return HTMLResponse(content=html)

@app.post("/admin/edit/{user_id}")
def edit_user(user_id: int, request: Request, username: str = Depends(authenticate)):
    async def edit_user(user_id: int, request: Request, username: str = Depends(authenticate)):
        form = await request.form()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET full_name=?, birth_date=?, birth_time=?, front_image_url=?, side_image_url=? WHERE id=?",
                       (form['full_name'], form['birth_date'], form['birth_time'], form['front_image_url'], form['side_image_url'], user_id))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/admin", status_code=303)

@app.get("/admin/add", response_class=HTMLResponse)
def add_user_page(username: str = Depends(authenticate)):
    html = """
    <html><head><title>Add User</title></head><body>
    <h2>Add New User</h2>
    <form method='post' action='/admin/add'>
    Name: <input name='full_name'/><br>
    Birth Date: <input name='birth_date'/><br>
    Birth Time: <input name='birth_time'/><br>
    Front Image URL: <input name='front_image_url'/><br>
    Side Image URL: <input name='side_image_url'/><br>
    <input type='submit' value='Add'/>
    </form>
    <a href='/admin'>Back to list</a></body></html>
    """
    return HTMLResponse(content=html)

@app.post("/admin/add")
def add_user(request: Request, username: str = Depends(authenticate)):
    async def add_user(request: Request, username: str = Depends(authenticate)):
        form = await request.form()
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (full_name, birth_date, birth_time, front_image_url, side_image_url) VALUES (?, ?, ?, ?, ?)",
                       (form['full_name'], form['birth_date'], form['birth_time'], form['front_image_url'], form['side_image_url']))
        conn.commit()
        conn.close()
        return RedirectResponse(url="/admin", status_code=303)
