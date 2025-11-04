# poblacion_db/session_setup.py
"""
Configuración de sesiones de SQLAlchemy para el proyecto.
"""

from sqlalchemy.orm import sessionmaker
from models import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)