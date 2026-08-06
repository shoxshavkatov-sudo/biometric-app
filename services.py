import os
import datetime
import numpy as np
import face_recognition
from sqlalchemy.orm import Session
from models import Worker, Shift


def get_face_encoding_from_file(file_path: str):
    image = face_recognition.load_image_file(file_path)
    encodings = face_recognition.face_encodings(image)
    return encodings[0] if encodings else None


def register_worker(db: Session, full_name: str, hourly_rate: float, photo_path: str, tg_id: int = None):
    encoding = get_face_encoding_from_file(photo_path)
    if encoding is None:
        return None, "Лицо на фото не найдено!"

    worker = Worker(
        full_name=full_name,
        hourly_rate=hourly_rate,
        telegram_id=tg_id,
        face_encoding=encoding.tobytes()
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return worker, "Сотрудник успешно зарегистрирован!"


def process_check_in_out(db: Session, photo_path: str):
    unknown_encoding = get_face_encoding_from_file(photo_path)
    if unknown_encoding is None:
        return {"status": "error", "message": "Лицо не распознано на снимке."}

    workers = db.query(Worker).all()
    matched_worker = None

    for w in workers:
        known_encoding = np.frombuffer(w.face_encoding, dtype=np.float64)
        results = face_recognition.compare_faces([known_encoding], unknown_encoding, tolerance=0.48)
        if results[0]:
            matched_worker = w
            break

    if not matched_worker:
        return {"status": "error", "message": "Сотрудник не найден в базе данных!"}

    now = datetime.datetime.now()
    # Проверяем, есть ли незакрытая смена
    open_shift = db.query(Shift).filter(
        Shift.worker_id == matched_worker.id,
        Shift.check_out == None
    ).first()

    if not open_shift:
        # Открываем новую смену
        new_shift = Shift(worker_id=matched_worker.id, check_in=now)
        db.add(new_shift)
        db.commit()
        return {
            "status": "success",
            "action": "check_in",
            "worker": matched_worker.full_name,
            "message": f"Приход зафиксирован в {now.strftime('%H:%M')}"
        }
    else:
        # Закрываем существующую смену
        open_shift.check_out = now
        duration = (now - open_shift.check_in).total_seconds() / 3600.0
        open_shift.hours_worked = round(duration, 2)
        open_shift.earned_amount = round(open_shift.hours_worked * matched_worker.hourly_rate, 2)

        db.commit()
        return {
            "status": "success",
            "action": "check_out",
            "worker": matched_worker.full_name,
            "hours": open_shift.hours_worked,
            "earned": open_shift.earned_amount,
            "message": f"Смена закрыта! Отработано: {open_shift.hours_worked} ч. Заработано: {open_shift.earned_amount:,.0f} сум."
        }