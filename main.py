import asyncio
import signal
import os
from datetime import datetime

import sqlite3
import pandas as pd
import aiohttp

from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

app = FastAPI(title="СИСТЕМА ПОСЕЩАЕМОСТИ — ЖИВЁТ 24/7")

# === БАЗА ДАННЫХ ===
conn = sqlite3.connect("attendance.db", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    action TEXT,
    time TEXT
)""")
conn.commit()

# === СПИСОК УЧЕНИКОВ (добавляй своих) ===
STUDENTS = ["ИВАНОВ", "ПЕТРОВ", "СИДОРОВ", "КУЗНЕЦОВ", "СМИРНОВА"]

# === ТЕЛЕГРАМ ТОКЕН И ЧАТ ===
BOT_TOKEN = "8399420502:AAHqJPTmsD0K7r1spXziNOS3JDCjiH5lDkI"
CHAT_ID = "ТВОЙ_CHAT_ID"  # ← замени на свой! (узнай через @userinfobot)

# === ГОЛОСОВОЕ СООБЩЕНИЕ В ТГ ===
async def send_tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    async with aiohttp.ClientSession() as session:
        await session.post(url, data=payload)

# === ГЛАВНАЯ ===
@app.get("/")
async def root():
    return HTMLResponse("""
    <html><head><title>СИСТЕМА ПОСЕЩАЕМОСТИ</title><meta charset="utf-8">
    <style>body{font-family:Arial;background:#000;color:#0f0;text-align:center;padding-top:10%;}
    h1{font-size:3em;text-shadow:0 0 20px #0f0;} a{color:#0f0;font-size:2em;}</style></head>
    <body><h1>БОТ ЖИВОЙ 24/7</h1>
    <p>Вебхук: /webhook/telegram</p>
    <p><a href="/admin">АДМИНКА</a> | <a href="/health">HEALTH</a></p>
    </body></html>
    """)

# === ЗДОРОВЬЕ ===
@app.get("/health")
async def health():
    return {"status": "OK", "time": datetime.now().isoformat()}

# === ВЕБХУК ТЕЛЕГРАМ (ПРОСТО РАБОТАЕТ) ===
@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    try:
        update = await request.json()
        msg = update.get("message", {})
        text = msg.get("text", "")
        chat_id = msg.get("chat", {}).get("id")
        
        if text == "/start":
            await send_tg("Система запущена!")
        elif text == "/admin":
            await send_tg("Админка: https://твой-проект.up.railway.app/admin")
            
    except Exception as e:
        print("Ошибка вебхука:", e)
    return JSONResponse({"ok": True})

# === ВХОД / ВЫХОД ===
@app.get("/enter")
async def enter(user: str = Query(...)):
    name = user.upper()
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO log (name, action, time) VALUES (?, 'ВХОД', ?)", (name, time))
    conn.commit()
    await send_tg(f"Добро пожаловать, {name}!")
    return HTMLResponse(f"<h1 style='color:green;'>ВХОД {name}</h1><meta http-equiv='refresh' content='2;url=/'>")

@app.get("/leave")
async def leave(user: str = Query(...)):
    name = user.upper()
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO log (name, action, time) VALUES (?, 'ВЫХОД', ?)", (name, time))
    conn.commit()
    await send_tg(f"До свидания, {name}!")
    return HTMLResponse(f"<h1 style='color:red;'>ВЫХОД {name}</h1><meta http-equiv='refresh' content='2;url=/'>")

# === АДМИНКА ===
@app.get("/admin")
async def admin():
    rows = conn.execute("SELECT * FROM log ORDER BY id DESC LIMIT 200").fetchall()
    html = "<html><head><title>АДМИНКА</title><meta charset='utf-8'><style>body{background:#000;color:#0f0;font-family:Arial;padding:20px;}"
    html += "table{border-collapse:collapse;width:100%;}th,td{border:1px solid #0f0;padding:10px;}</style></head><body>"
    html += "<h1>ПОСЛЕДНИЕ 200 ОТМЕТОК</h1><table><tr><th>ID</th><th>ФАМИЛИЯ</th><th>ДЕЙСТВИЕ</th><th>ВРЕМЯ</th></tr>"
    for r in rows:
        color = "lime" if r[2] == "ВХОД" else "red"
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td style='color:{color};'>{r[2]}</td><td>{r[3]}</td></tr>"
    html += "</table><br><a href='/export' style='color:cyan;font-size:2em;'>СКАЧАТЬ EXCEL</a>"
    html += " | <a href='/' style='color:yellow;'>НА ГЛАВНУЮ</a></body></html>"
    return HTMLResponse(html)

# === ЭКСПОРТ В EXCEL ===
@app.get("/export")
async def export():
    df = pd.DataFrame(conn.execute("SELECT * FROM log ORDER BY time DESC").fetchall(),
                      columns=["ID", "ФАМИЛИЯ", "ДЕЙСТВИЕ", "ВРЕМЯ"])
    df.to_excel("посещаемость.xlsx", index=False)
    return FileResponse("посещаемость.xlsx", filename="посещаемость.xlsx")

# === ПРОВЕРКА ПРОПУСКОВ КАЖДЫЕ 5 МИНУТ ===
async def check_absent():
    while True:
        await asyncio.sleep(300)
        today = datetime.now().strftime("%Y-%m-%d")
        present = [row[0] for row in conn.execute(
            "SELECT name FROM log WHERE time LIKE ? AND action='ВХОД'", (f"{today}%",)).fetchall()]
        absent = [s for s in STUDENTS if s not in present]
        if absent:
            await send_tg(f"ПРОПУСК: {', '.join(absent)}")

# === ЗАПУСК ===
@app.on_event("startup")
async def startup():
    asyncio.create_task(check_absent())
    print("Система запущена — БОТ ЖИВОЙ 24/7")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
