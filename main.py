from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from typing import Optional

# Inicjalizacja aplikacji FastAPI
app = FastAPI()

# Dane do połączenia z bazą danych
DATABASE_URL = "postgresql://2024_gwozdz_bartlomiej:37685BG@195.150.230.208:5432/2024_gwozdz_bartlomiej"

# Tworzenie silnika bazy danych
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Modele danych
class ZagadkiRequest(BaseModel):
    id_autora: int
    kategoria: str
    obraz: str
    rozwiazanie: str

class AutorRequest(BaseModel):
    nazwa: str

class ZagadkiResponse(BaseModel):
    id: int
    kategoria: str
    obraz: str
    rozwiazanie: str
    autor: str

class ZagadkiWithAutorRequest(BaseModel):
    zagadki: ZagadkiRequest
    autor: Optional[AutorRequest] = None

# Endpointy
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

@app.get("/zagadki/{id}", response_model=ZagadkiResponse)
def get_zagadki_by_id(id: int):
    query = """
        SELECT z.id, z.kategoria, z.obraz, z.rozwiazanie, a.nazwa
        FROM zagadkomat.zagadki AS z
        JOIN zagadkomat.autor AS a ON z.id_autora = a.id_autora
        WHERE z.id = :id
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), {"id": id}).fetchone()
            if result:
                return {
                    "id": result[0],
                    "kategoria": result[1],
                    "obraz": result[2],
                    "rozwiazanie": result[3],
                    "autor": result[4],
                }
            else:
                raise HTTPException(status_code=404, detail="Nie znaleziono zagadki o podanym ID.")
    except Exception as e:
        logging.error(f"Błąd w get_zagadki_by_id: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd: {str(e)}")

@app.get("/zagadki-ids")
def get_all_zagadki_ids():
    query = "SELECT id FROM zagadkomat.zagadki"
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query)).fetchall()
            return {"ids": [row[0] for row in result]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd: {str(e)}")

@app.post("/zagadki")
def add_zagadki(request: ZagadkiWithAutorRequest):
    zagadki = request.zagadki
    autor = request.autor
    logging.info(f"Próba dodania zagadki: {zagadki} z autorem: {autor}")

    try:
        with engine.begin() as connection:
            autor_query = "SELECT id_autora FROM zagadkomat.autor WHERE nazwa = :nazwa"
            autor_result = connection.execute(text(autor_query), {"nazwa": autor.nazwa}).fetchone()

            if autor_result:
                id_autora = autor_result[0]
                logging.info(f"Znaleziono istniejącego autora: {autor.nazwa} (id: {id_autora})")
            else:
                new_autor_query = "INSERT INTO zagadkomat.autor (nazwa) VALUES (:nazwa) RETURNING id_autora"
                id_autora = connection.execute(text(new_autor_query), {"nazwa": autor.nazwa}).fetchone()[0]
                logging.info(f"Dodano nowego autora: {autor.nazwa} (id: {id_autora})")

            zagadki_query = """
                INSERT INTO zagadkomat.zagadki (id_autora, kategoria, obraz, rozwiazanie)
                VALUES (:id_autora, :kategoria, :obraz, :rozwiazanie)
                RETURNING id
            """
            new_id = connection.execute(
                text(zagadki_query),
                {
                    "id_autora": id_autora,
                    "kategoria": zagadki.kategoria,
                    "obraz": zagadki.obraz,
                    "rozwiazanie": zagadki.rozwiazanie,
                },
            ).fetchone()[0]
            logging.info(f"Dodano nową zagadkę: {new_id}")

        return {"message": "Zagadki dodano pomyślnie.", "new_id": new_id}
    except Exception as e:
        logging.error(f"Błąd w add_zagadki: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Błąd: {str(e)}")


@app.get("/author-id")
def get_author_id(nazwa: str):
    query = "SELECT id_autora FROM zagadkomat.autor WHERE nazwa = :nazwa"
    try:
        with engine.connect() as connection:
            result = connection.execute(text(query), {"nazwa": nazwa}).fetchone()
            if result:
                return result[0]  # zwracaj samą liczbę
            else:
                raise HTTPException(status_code=404, detail="Autor nie istnieje.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Błąd: {str(e)}")


