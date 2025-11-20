# routes_projects.py
# Endpoints for projects master data.
#  - GET /projects/  -> list all projects
#  - POST /projects/ -> upsert (insert or update) a list of projects

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from sqlalchemy import text

from database import get_db  # uses your existing database.py

router = APIRouter(prefix="/projects", tags=["projects"])

class Project(BaseModel):
  id: str
  code: str
  name: str

@router.get("/", response_model=List[Project])
def list_projects(db=Depends(get_db)):
  rows = db.execute(
    text("SELECT id, code, name FROM projects ORDER BY code")
  ).mappings().all()
  return [dict(r) for r in rows]

@router.post("/", status_code=204)
def upsert_projects(payload: List[Project], db=Depends(get_db)):
  for p in payload:
    db.execute(text("""
      INSERT INTO projects (id, code, name)
      VALUES (:id, :code, :name)
      ON CONFLICT (id) DO UPDATE SET
        code = EXCLUDED.code,
        name = EXCLUDED.name
    """), {
      "id": p.id,
      "code": p.code,
      "name": p.name,
    })
  db.commit()
  return
