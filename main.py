from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def init_db():
    conn = sqlite3.connect("erp.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            email TEXT,
            solde REAL DEFAULT 0.0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS factures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            description TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id)
        )
    """)
    conn.commit()
    conn.close()

init_db()

class ClientCreate(BaseModel):
    nom: str
    email: Optional[str] = None

class FactureCreate(BaseModel):
    client_id: int
    montant: float
    description: Optional[str] = None

@app.get("/")
def read_root():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/clients")
def get_clients():
    conn = sqlite3.connect("erp.db")
    cursor = conn.cursor()
    clients = cursor.execute("SELECT id, nom, email, solde FROM clients").fetchall()
    conn.close()
    return [{"id": c[0], "nom": c[1], "email": c[2], "solde": c[3]} for c in clients]

@app.post("/api/clients")
def create_client(client: ClientCreate):
    conn = sqlite3.connect("erp.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clients (nom, email) VALUES (?, ?)", (client.nom, client.email))
    conn.commit()
    conn.close()
    return {"message": "Client créé"}

@app.get("/api/factures")
def get_factures():
    conn = sqlite3.connect("erp.db")
    cursor = conn.cursor()
    factures = cursor.execute("""
        SELECT f.id, f.client_id, c.nom, f.montant, f.description, f.date 
        FROM factures f JOIN clients c ON f.client_id = c.id
    """).fetchall()
    conn.close()
    return [{"id": f[0], "client_id": f[1], "client_nom": f[2], "montant": f[3], "description": f[4], "date": f[5]} for f in factures]

@app.post("/api/factures")
def create_facture(facture: FactureCreate):
    conn = sqlite3.connect("erp.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO factures (client_id, montant, description) VALUES (?, ?, ?)",
        (facture.client_id, facture.montant, facture.description)
    )
    cursor.execute(
        "UPDATE clients SET solde = solde + ? WHERE id = ?",
        (facture.montant, facture.client_id)
    )
    conn.commit()
    conn.close()
    return {"message": "Facture créée et solde client mis à jour !"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
