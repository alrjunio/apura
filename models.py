from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, Time
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pydantic import BaseModel
from typing import Optional, List
from datetime import time
from database import Base, engine


class Enduro(Base):
    __tablename__ = "enduros"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)
    date = Column(String)
    hora_largada = Column(String)

    competitors = relationship("Competitor", back_populates="enduro")
    checkpoints = relationship("Checkpoint", back_populates="enduro")
    tempos = relationship("Tempo", back_populates="enduro")
    categories = relationship("Category", back_populates="enduro")


class Competitor(Base):
    __tablename__ = "competitors"
    id = Column(Integer, primary_key=True, index=True)
    enduro_id = Column(Integer, ForeignKey("enduros.id"))
    name = Column(String, index=True)
    placa = Column(String)
    categories_id = Column(Integer, ForeignKey("categories.id"))

    enduro = relationship("Enduro", back_populates="competitors")
    checkpoints = relationship("Checkpoint", back_populates="competitor")
    tempos = relationship("Tempo", back_populates="competitor")
    category = relationship("Category", back_populates="competitors")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id = Column(Integer, primary_key=True, index=True)
    enduro_id = Column(Integer, ForeignKey("enduros.id"))
    competitor_id = Column(Integer, ForeignKey("competitors.id"))
    checkpoint_name = Column(String, nullable=False)
    time = Column(Float, nullable=False)  # Tempo em segundos

    enduro = relationship("Enduro", back_populates="checkpoints")
    competitor = relationship("Competitor", back_populates="checkpoints")
    tempos = relationship("Tempo", back_populates="checkpoint")


class Tempo(Base):
    __tablename__ = "tempos"
    id = Column(Integer, primary_key=True, index=True)
    enduro_id = Column(Integer, ForeignKey("enduros.id"))
    checkpoint_id = Column(Integer, ForeignKey("checkpoints.id"))
    competitor_id = Column(Integer, ForeignKey("competitors.id"))
    largada = Column(Float)  # Tempo em segundos

    enduro = relationship("Enduro", back_populates="tempos")
    checkpoint = relationship("Checkpoint", back_populates="tempos")
    competitor = relationship("Competitor", back_populates="tempos")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    enduro_id = Column(Integer, ForeignKey("enduros.id"))
    name = Column(String)

    enduro = relationship("Enduro", back_populates="categories")
    competitors = relationship("Competitor", back_populates="category")


# Classes Pydantic para validação
class EnduroUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    date: Optional[str] = None
    hora_largada: time = None


class CompetitorUpdate(BaseModel):
    enduro_id: Optional[int] = None
    name: Optional[str] = None
    placa: Optional[str] = None
    category: Optional[str] = None


class CheckpointUpdate(BaseModel):
    enduro_id: Optional[int] = None
    checkpoint_name: Optional[str] = None
    time: Optional[float] = None


class TempoUpdate(BaseModel):
    enduro_id: Optional[int] = None
    checkpoint_id: Optional[int] = None
    competitor_id: Optional[int] = None
    largada: Optional[float] = None


class CategoryUpdate(BaseModel):
    enduro_id: Optional[int] = None
    name: Optional[str] = None


class EnduroCreate(BaseModel):
    name: str
    location: str
    date: str
    hora_largada: time


class CompetitorCreate(BaseModel):
    enduro_id: int
    name: str
    placa: str
    category: str
    categories_id: int


class CheckpointCreate(BaseModel):
    enduro_id: int
    checkpoint_name: str
    time: time


class TempoCreate(BaseModel):
    enduro_id: int
    checkpoint_id: int
    competitor_id: int
    largada: time


class CategoryCreate(BaseModel):
    enduro_id: int
    name: str


Base.metadata.create_all(bind=engine)
