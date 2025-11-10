import asyncio
import signal
import os
from datetime import datetime

import sqlite3
import aiohttp
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

app = FastAPI()

# === БАЗА ===
conn = sqlite3.connect("attendance.db", check_same_thread=False)
conn.execute("""CREATE TABLE IF NOT EXISTS log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    action TEXT,
    time TEXT
)""")
conn.commit()

# === СПИСОК УЧЕНИКОВ ===
STUDENTS = ["ИВАНОВ", "ПЕТРОВ", "СИДОРОВ", "КУЗНЕЦОВ", "СМИРНОВА"]

# === ТЕЛЕГРАМ ===
BOT_TOKEN = "8399420502:AAHqJPTmsD0K7r1spXziNOS3JDCjiH5lDkI"
CHAT_ID = "5330392057"  

async def send_tg(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(url, data=payload)
        except:
            pass  # не падаем, если ТГ недоступен

# === ГЛАВНАЯ ===
@app.get("/")
async def root():
    return HTMLResponse("""
    <html><head><title>СИСТЕМА ПОСЕЩАЕМОСТИ</title><meta charset="utf-8">
    <style>body{background:#000;color:#0f0;font-family:Arial;text-align:center;padding-top:10%;}
    h1{font-size:3em;text-shadow:0 0 20px #0f0;}</style></head>
    <body><h1>БОТ ЖИВОЙ 24/7</h1>
    <p><a href="/admin" style="color:lime;font-size:2em;">АДМИНКА</a></p>
    </body></html>
    """)

# === ВЕБХУК ===
@app.post("/webhook/telegram")
async def webhook(request: Request):
    try:
        data = await request.json()
        if "message" in data and data["message"]["text"] == "/start":
            await send_tg("Система работает!")
    except:
        pass
    return JSONResponse({"ok": True})

# === ВХОД / ВЫХОД ===
@app.get("/enter")
async def enter(user: str = Query(...)):
    name = user.upper()
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO log (name, action, time) VALUES (?, 'ВХОД', ?)", (name, t))
    conn.commit()
    await send_tg(f"ВХОД: {name}")
    return HTMLResponse(f"<h1 style='color:green;'>ВХОД {name}</h1><meta http-equiv='refresh' content='2;url=/'>")

@app.get("/leave")
async def leave(user: str = Query(...)):
    name = user.upper()
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("INSERT INTO log (name, action, time) VALUES (?, 'ВЫХОД', ?)", (name, t))
    conn.commit()
    await send_tg(f"ВЫХОД: {name}")
    return HTMLResponse(f"<h1 style='color:red;'>ВЫХОД {name}</h1><meta http-equiv='refresh' content='2;url=/'>")

# === АДМИНКА ===
@app.get("/admin")
async def admin():
    rows = conn.execute("SELECT * FROM log ORDER BY id DESC LIMIT 200").fetchall()
    html = "<html><head><title>АДМИНКА</title><meta charset='utf-8'><style>body{background:#000;color:#0f0;padding:20px;}"
    html += "table{border-collapse:collapse;width:100%;}th,td{border:1px solid #0f0;padding:10px;}</style></head><body>"
    html += "<h1>ПОСЛЕДНИЕ 200 ЗАПИСЕЙ</h1><table><tr><th>ID</th><th>ФАМИЛИЯ</th><th>ДЕЙСТВИЕ</th><th>ВРЕМЯ</th></tr>"
    for r in rows:
        color = "lime" if r[2] == "ВХОД" else "red"
        html += f"<tr><td>{r[0]}</td><td>{r[1]}</td><td style='color:{color}'>{r[2]}</td><td>{r[3]}</td></tr>"
    html += "</table><br><a href='/export' style='color:cyan;font-size:2em;'>СКАЧАТЬ EXCEL</a></body></html>"
    return HTMLResponse(html)

# === ЭКСПОРТ В EXCEL (через openpyxl — без pandas!) ===
@app.get("/export")
async def export():
    import pandas as pd  # импортируем только здесь
    df = pd.read_sql_query("SELECT * FROM log ORDER BY time DESC", conn)
    filename = "посещаемость.xlsx"
    df.to_excel(filename, index=False)
    return FileResponse(filename, filename=filename)

# === ПРОВЕРКА ПРОПУСКОВ ===
async def check_absent():
    while True:
        await asyncio.sleep(300)
        today = datetime.now().strftime("%Y-%m-%d")
        present = [r[0] for r in conn.execute(
            "SELECT name FROM log WHERE time LIKE ? AND action='ВХОД'", (f"{today}%",)).fetchall()]
        absent = [s for s in STUDENTS if s not in present]
        if absent:
            await send_tg(f"ПРОПУСТИЛИ: {', '.join(absent)}")

@app.on_event("startup")
async def startup():
    asyncio.create_task(check_absent())

# === ЗАПУСК ===
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))

