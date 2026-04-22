"""FastAPI сервер для интеграции с n8n. Запускается параллельно с ботом."""
import logging
from datetime import date
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field
import uvicorn
from config import N8N_WEBHOOK_SECRET, API_PORT, ADMIN_TELEGRAM_ID
from data.services import SERVICES_BY_ID, PAYMENT_LABELS
from services import google_sheets, google_calendar
from handlers.booking import _get_available_slots, _format_date

logger = logging.getLogger(__name__)
app = FastAPI(title="Manicure Bot — n8n API", version="1.0.0")
_bot = None


def set_bot(bot): global _bot; _bot = bot


def _auth(secret):
    if N8N_WEBHOOK_SECRET and secret != N8N_WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret")


class SlotsReq(BaseModel):
    date: str
    service_id: str


class BookingReq(BaseModel):
    date: str; time: str; service_id: str
    client_name: str; client_phone: str
    payment: str = "cash"; telegram_id: int = 0


@app.get("/health")
async def health(): return {"status": "ok"}


@app.get("/services")
async def list_services(x_webhook_secret: Optional[str] = Header(default=None)):
    _auth(x_webhook_secret)
    from data.services import SERVICES
    return [{"id": s.id, "name": s.name, "duration_minutes": s.duration_minutes, "price": s.price} for s in SERVICES]


@app.post("/available_slots")
async def available_slots(body: SlotsReq, x_webhook_secret: Optional[str] = Header(default=None)):
    _auth(x_webhook_secret)
    svc = SERVICES_BY_ID.get(body.service_id)
    if not svc: raise HTTPException(404, f"Service not found: {body.service_id}")
    if body.date < date.today().isoformat(): raise HTTPException(400, "Date in the past")
    existing = google_sheets.get_bookings_for_date(body.date)
    return {"date": body.date, "service": svc.name, "available_slots": _get_available_slots(svc.duration_minutes, existing)}


@app.post("/bookings", status_code=201)
async def create_booking(body: BookingReq, x_webhook_secret: Optional[str] = Header(default=None)):
    _auth(x_webhook_secret)
    svc = SERVICES_BY_ID.get(body.service_id)
    if not svc: raise HTTPException(404, "Service not found")
    available = _get_available_slots(svc.duration_minutes, google_sheets.get_bookings_for_date(body.date))
    if body.time not in available: raise HTTPException(409, f"Slot {body.time} not available")
    pay = PAYMENT_LABELS.get(body.payment, body.payment)
    bid = google_sheets.add_booking(body.date, body.time, body.client_name, body.client_phone,
                                    svc.name, svc.duration_minutes, svc.price, pay, body.telegram_id)
    eid = google_calendar.create_event(body.date, body.time, svc.duration_minutes,
                                       body.client_name, body.client_phone, svc.name, pay, bid)
    if eid: google_sheets.update_event_id(bid, eid)
    if _bot:
        try: await _bot.send_message(ADMIN_TELEGRAM_ID, f"🤖 *Запись через n8n*\n\nID: `{bid}`\n💅 {svc.name}\n📅 {_format_date(body.date)}, {body.time}\n👤 {body.client_name}\n📞 {body.client_phone}", parse_mode="Markdown")
        except Exception: pass
    return {"booking_id": bid, "date": body.date, "time": body.time, "service": svc.name, "price": svc.price}


@app.post("/bookings/{booking_id}/cancel")
async def cancel_booking(booking_id: str, x_webhook_secret: Optional[str] = Header(default=None)):
    _auth(x_webhook_secret)
    if not google_sheets.cancel_booking(booking_id): raise HTTPException(404, "Booking not found")
    return {"booking_id": booking_id, "status": "cancelled"}


async def run_api_server():
    config = uvicorn.Config(app, host="0.0.0.0", port=API_PORT, log_level="warning")
    await uvicorn.Server(config).serve()
