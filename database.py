from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError



# Dependência para obter a sessão do banco de dados

DATABASE_URL = "sqlite:///./enduro.db"
       
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

from fastapi import HTTPException

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def adicionar_coluna_tempo(checkpoint_name: str):
    """
    Adiciona uma nova coluna à tabela de checkpoints.
    """
    try:
        with engine.connect() as connection:
            # Adiciona a coluna à tabela
            connection.execute(f"ALTER TABLE checkpoints ADD COLUMN {checkpoint_name} FLOAT")
            print(f"Coluna '{checkpoint_name}' adicionada com sucesso!")
    except SQLAlchemyError as e:
        print(f"Erro ao adicionar coluna: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adicionar coluna: {e}",
        )