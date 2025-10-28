from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from fastapi import FastAPI, Form, HTTPException
import os, jwt, bcrypt, datetime as dt, psycopg

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later we can restrict to your Netlify domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True)

@app.get("/")
def root():
    return {"status": "ok", "app": "factory-labour-logger"}

@app.get("/health")
def health():
    return {"status": "ok"}

# ---------- MODELS ----------
class UserOut(BaseModel):
    id: str
    email: str
    name: str
    role: str

class TokenOut(BaseModel):
    token: str
    user: UserOut

# ---------- AUTH ----------
@app.post("/auth/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends()):
    with get_conn() as con:
        row = con.execute(
            "select id,email,name,role,password_hash from app_user where email=%s",
            (form.username,),
        ).fetchone()
        if not row or not bcrypt.checkpw(form.password.encode(), row[4].encode()):
            raise HTTPException(401, "Invalid credentials")
        payload = {
            "sub": row[0],
            "role": row[3],
            "exp": dt.datetime.utcnow() + dt.timedelta(hours=8),
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
        return {"token": token, "user": {"id": row[0], "email": row[1], "name": row[2], "role": row[3]}}

def require_token(authorization: str = Header(None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split()[1]
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        raise HTTPException(401, "Invalid token")

# ---------- EMPLOYEES ----------
class EmployeeIn(BaseModel):
    name: str
    badge: str | None = None
    pin: str | None = None

@app.get("/employees")
def list_employees(_: dict = Depends(require_token)):
    with get_conn() as con:
        rows = con.execute("select id,name,badge,pin from employee order by name").fetchall()
        return [{"id": r[0], "name": r[1], "badge": r[2], "pin": r[3]} for r in rows]

@app.post("/employees")
def create_employee(body: EmployeeIn, _: dict = Depends(require_token)):
    with get_conn() as con:
        row = con.execute(
            "insert into employee(name,badge,pin) values (%s,%s,%s) returning id",
            (body.name, body.badge, body.pin),
        ).fetchone()
        return {"id": row[0], **body.dict()}

# ---------- PROJECTS ----------
class ProjectIn(BaseModel):
    code: str
    name: str

@app.get("/projects")
def list_projects(_: dict = Depends(require_token)):
    with get_conn() as con:
        rows = con.execute("select id,code,name from project order by code").fetchall()
        return [{"id": r[0], "code": r[1], "name": r[2]} for r in rows]

@app.post("/projects")
def create_project(body: ProjectIn, _: dict = Depends(require_token)):
    with get_conn() as con:
        row = con.execute(
            "insert into project(code,name) values (%s,%s) returning id",
            (body.code, body.name),
        ).fetchone()
        return {"id": row[0], **body.dict()}

# ---------- ENTRIES ----------
class EntryIn(BaseModel):
    employeeId: str
    projectId: str
    date: str
    start: str
    end: str
    breakMin: int = 0
    workType: str | None = None
    notes: str | None = None
    hours: float
    roundedFromMin: int | None = None
    roundingMin: int | None = None

@app.get("/entries")
def list_entries(_: dict = Depends(require_token)):
    with get_conn() as con:
        rows = con.execute(
            "select id,employee_id,project_id,date,start_time,end_time,break_min,work_type,notes,hours,rounded_from_min,rounding_min,status,locked,created_at from entry order by created_at desc"
        ).fetchall()
        keys = ["id","employeeId","projectId","date","start","end","breakMin","workType","notes","hours","roundedFromMin","roundingMin","status","locked","createdAt"]
        return [dict(zip(keys, r)) for r in rows]

@app.post("/entries")
def create_entry(body: EntryIn, _: dict = Depends(require_token)):
    with get_conn() as con:
        row = con.execute(
            '''insert into entry(employee_id,project_id,date,start_time,end_time,break_min,work_type,notes,hours,rounded_from_min,rounding_min)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) returning id,created_at''',
            (body.employeeId, body.projectId, body.date, body.start, body.end, body.breakMin, body.workType, body.notes, body.hours, body.roundedFromMin, body.roundingMin)
        ).fetchone()
        return {"id": row[0], "createdAt": row[1].isoformat()}

# ✅ TEMPORARY LOGIN ENDPOINT (accepts your admin credentials)
@app.post("/auth/login")
def auth_login(username: str = Form(...), password: str = Form(...)):
    demo_users = {
        "mark@argand.ie": {"password": "ArgandA3!", "name": "Mark", "role": "admin"},
    }
    user = demo_users.get(username)
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Return the shape your frontend expects:
    return {
        "token": "demo-token",  # placeholder
        "user": {"email": username, "name": user["name"], "role": user["role"]},
    }
