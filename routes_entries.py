# routes_entries.py
# Two endpoints (no auth for now):
#  - GET /entries/   -> list entries from Postgres
#  - POST /entries/  -> upsert (save) a list of entries into Postgres

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from sqlalchemy import text
from database import get_db  # make sure database.py exists as we created

router = APIRouter(prefix="/entries", tags=["entries"])

# Matches your frontend's Entry shape
class Entry(BaseModel):
    id: str
    employee_id: str
    project_id: str
    date: str
    start: str
    end: str
    break_min: int
    work_type: str
    notes: str
    hours: float
    rounded_from_min: int
    rounding_min: int
    status: str
    locked: bool
    created_at: str

@router.get("/", response_model=List[Entry])
def list_entries(db=Depends(get_db)):
    rows = db.execute(
        text('SELECT * FROM entries ORDER BY created_at DESC')
    ).mappings().all()
    return [dict(r) for r in rows]

@router.post("/", status_code=204)
def upsert_entries(payload: List[Entry], db=Depends(get_db)):
    for e in payload:
        db.execute(text("""
            INSERT INTO entries(
              id, employee_id, project_id, date, start, "end", break_min, work_type, notes,
              hours, rounded_from_min, rounding_min, status, locked, created_at
            ) VALUES (
              :id, :employee_id, :project_id, :date, :start, :end, :break_min, :work_type, :notes,
              :hours, :rounded_from_min, :rounding_min, :status, :locked, :created_at
            )
            ON CONFLICT (id) DO UPDATE SET
              employee_id = EXCLUDED.employee_id,
              project_id = EXCLUDED.project_id,
              date = EXCLUDED.date,
              start = EXCLUDED.start,
              "end" = EXCLUDED."end",
              break_min = EXCLUDED.break_min,
              work_type = EXCLUDED.work_type,
              notes = EXCLUDED.notes,
              hours = EXCLUDED.hours,
              rounded_from_min = EXCLUDED.rounded_from_min,
              rounding_min = EXCLUDED.rounding_min,
              status = EXCLUDED.status,
              locked = EXCLUDED.locked,
              created_at = EXCLUDED.created_at
        """), {
            "id": e.id,
            "employee_id": e.employee_id,
            "project_id": e.project_id,
            "date": e.date,
            "start": e.start,
            "end": e.end,
            "break_min": e.break_min,
            "work_type": e.work_type,
            "notes": e.notes,
            "hours": e.hours,
            "rounded_from_min": e.rounded_from_min,
            "rounding_min": e.rounding_min,
            "status": e.status,
            "locked": e.locked,
            "created_at": e.created_at
        })
    db.commit()
    return
