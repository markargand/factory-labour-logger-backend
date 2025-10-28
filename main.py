# main.py — minimal, known-good FastAPI with temp login
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routes_entries import router as entries_router

app = FastAPI(title="Factory Labour Logger API")

# CORS: allow your Netlify site to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later: replace with your Netlify domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(entries_router)

@app.get("/")
def root():
    return {"status": "ok", "app": "factory-labour-logger"}

@app.get("/health")
def health():
    return {"status": "ok"}

# 🔐 TEMP login: accepts your admin email/password so you can sign in
@app.post("/auth/login")
def auth_login(username: str = Form(...), password: str = Form(...)):
    demo_users = {
        "mark@argand.ie": {"password": "ArgandA3!", "name": "Mark", "role": "admin"},
    }
    u = demo_users.get(username)
    if not u or u["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"token": "demo-token", "user": {"email": username, "name": u["name"], "role": u["role"]}}
