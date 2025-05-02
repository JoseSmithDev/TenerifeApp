# poblacion_db/session_setup.py (o setup_db/session_setup.py)

from sqlalchemy.orm import sessionmaker
# Importación ABSOLUTA de models.py que está en la raíz del proyecto
from models import engine, Base # Base si la usas aquí, ej. para create_all


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session_factory():
    """Retorna una nueva instancia de sesión."""
    return SessionLocal()

# O si prefieres pasar la sesión directamente desde main_populate
# def populate_continents(session):
#     # Usa la sesión pasada como argumento
#     pass