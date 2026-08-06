import os
import asyncio
import sqlite3
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import uvicorn

import database

BOT_TOKEN = "8960030512:AAHj3w9NKuLvUhD6cAxbP8llZJjL9F0rzo"
WEB_APP_URL = "https://landlord-punctuate-whooping.ngrok-free.dev"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

kb = InlineKeyboardMarkup(
    inline_keyboard=[[InlineKeyboardButton(text="📱 Открыть терминал", web_app=WebAppInfo(url=WEB_APP_URL))]]
)


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("Система учета времени (08:00 - 17:00):", reply_markup=kb)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.init_db()
    polling_task = asyncio.create_task(dp.start_polling(bot))
    yield
    polling_task.cancel()
    await bot.session.close()


app = FastAPI(title="Attendance System", lifespan=lifespan)

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_root():
    return FileResponse("index.html")


# --- 1. РЕГИСТРАТОР 1: ДОБАВЛЕНИЕ ЧЕЛОВЕКА ---
class NewEmployeeRequest(BaseModel):
    name: str
    monthly_salary: float


@app.get("/api/employees")
async def get_employees():
    return database.get_all_employees()


@app.post("/api/employees")
async def create_employee(data: NewEmployeeRequest):
    database.add_employee(data.name, data.monthly_salary)
    return {"status": "success", "message": f"Сотрудник {data.name} внесен в базу!"}


# --- 2. РЕГИСТРАТОР 2: ВХОД/ВЫХОД ПО ФОТО ---
class ScanRequest(BaseModel):
    employee_id: int
    image: str


@app.post("/api/scan")
async def scan_attendance(data: ScanRequest):
    conn = sqlite3.connect(database.DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, daily_salary, hourly_rate FROM employees WHERE id = ?", (data.employee_id,))
    emp = cursor.fetchone()

    if not emp:
        conn.close()
        return {"status": "error", "detail": "Рабочий не найден в базе!"}

    emp_id, emp_name, daily_salary, hourly_rate = emp
    today = datetime.now().strftime("%Y-%m-%d")
    now_str = datetime.now().strftime("%H:%M:%S")
    now_dt = datetime.now()

    # Проверяем, есть ли открытая смена
    cursor.execute(
        "SELECT id, check_in FROM shifts WHERE employee_id = ? AND date = ? AND status = 'open'",
        (emp_id, today)
    )
    open_shift = cursor.fetchone()

    if not open_shift:
        # Регистрация Прихода
        cursor.execute(
            "INSERT INTO shifts (employee_id, date, check_in, status) VALUES (?, ?, ?, 'open')",
            (emp_id, today, now_str)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"✅ ПРИХОД ЗАФИКСИРОВАН\nРабочий: {emp_name}\nВремя: {now_str}"}
    else:
        # Регистрация Ухода
        shift_id, check_in_str = open_shift
        check_in_dt = datetime.strptime(f"{today} {check_in_str}", "%Y-%m-%d %H:%M:%S")

        hours_worked = round((now_dt - check_in_dt).total_seconds() / 3600, 2)

        # Если отработал 9 часов (с 8 до 17) или больше — получает полный дневной оклад
        earned = daily_salary if hours_worked >= 9.0 else round(hours_worked * hourly_rate, 2)

        cursor.execute(
            "UPDATE shifts SET check_out = ?, hours_worked = ?, earned_salary = ?, status = 'closed' WHERE id = ?",
            (now_str, hours_worked, earned, shift_id)
        )
        conn.commit()
        conn.close()

        return {
            "status": "success",
            "message": f"🔴 УХОД ЗАФИКСИРОВАН\nРабочий: {emp_name}\nОтработано: {hours_worked} ч.\nЗарплата за день: {earned:,.0f} сум"
        }


@app.get("/api/attendance")
async def get_attendance():
    return database.get_today_shifts()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)