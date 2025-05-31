from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Inicjalizacja aplikacji FastAPI
app = FastAPI()

# Dane do połączenia z bazą danych
DATABASE_URL = "postgresql://2024_gwozdz_bartlomiej:37685BG@195.150.230.208:5432/2024_gwozdz_bartlomiej"

# Tworzenie silnika bazy danych
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.get("/")
def read_root():
    return {"message": "API działa poprawnie!"}

@app.get("/test-connection")
def test_connection():
    try:
        # Otwarcie sesji
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            return {"message": "Połączenie z bazą danych działa poprawnie.", "result": [row[0] for row in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd połączenia z bazą danych: {str(e)}")

