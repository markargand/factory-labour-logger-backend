# routes_employees.py
# Endpoints for employees master data.
#  - GET /employees/  -> list all employees
#  - POST /employees/ -> upsert (insert or update) a list of employees

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import text

from database import get_db  # uses your existing database.py

router = APIRouter(prefix="/employees", tags=["employees"])

class Employee(BaseModel):
  id: str
  name: str
  badge: str | None = None
  pin: str | None = None
  hourly_rate: float | None = 0.0

@router.get("/", response_model=List[Employee])
def list_employees(db=Depends(get_db)):
  rows = db.execute(
    text("SELECT id, name, badge, pin, hourly_rate FROM employees ORDER BY name")
  ).mappings().all()
  return [dict(r) for r in rows]

@router.post("/", status_code=204)
def upsert_employees(payload: List[Employee], db=Depends(get_db)):
  for e in payload:
    db.execute(text("""
      INSERT INTO employees (id, name, badge, pin, hourly_rate)
      VALUES (:id, :name, :badge, :pin, :hourly_rate)
      ON CONFLICT (id) DO UPDATE SET
        name = EXCLUDED.name,
        badge = EXCLUDED.badge,
        pin = EXCLUDED.pin,
        hourly_rate = EXCLUDED.hourly_rate
    """), {
      "id": e.id,
      "name": e.name,
      "badge": e.badge,
      "pin": e.pin,
      "hourly_rate": e.hourly_rate if e.hourly_rate is not None else 0.0,
    })
  db.commit()
  return
