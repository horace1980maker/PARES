from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:5176", "http://localhost:5177"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock Data
MOCK_ORGANIZATIONS = {
    'Ecuador': [
        { 'name': 'Fundación Futuro Latinoamericano', 'description': 'Promoting sustainable development and conflict management.' },
    ],
    'Mexico': [
        { 'name': 'Pronatura', 'description': 'Conservation of flora, fauna, and priority ecosystems.' },
    ],
}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/countries")
def get_countries():
    return list(MOCK_ORGANIZATIONS.keys())

@app.get("/organizations/{country_name}")
def get_organizations(country_name: str):
    if country_name not in MOCK_ORGANIZATIONS:
        return []
    return MOCK_ORGANIZATIONS[country_name]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
