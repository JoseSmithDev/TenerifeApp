# poblacion_db/main_populate.py
"""
Script principal para poblar la base de datos con datos iniciales.
Ejecuta los scripts de poblamiento en el orden correcto.
"""

import logging
import traceback
from poblacion_db.session_setup import SessionLocal
from poblacion_db.populate_base_hierarchy import populate_base_hierarchy
from poblacion_db.crear_provincias_islas_municipios import populate_provinces_islands_municipalities
from poblacion_db.crear_ubicaciones import populate_locations
from poblacion_db.crear_niveles import populate_levels
from poblacion_db.crear_logros import populate_achievements
from models import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_population():
    """
    Pobla la base de datos con datos iniciales.
    Borra y recrea todas las tablas antes de poblar.
    """
    logger.info("Iniciando proceso de poblamiento de la base de datos...")
    
    # Borrar y recrear tablas
    logger.info("Borrando todas las tablas existentes...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Tablas borradas.")

    logger.info("Creando todas las tablas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tablas creadas.")

    session = SessionLocal()

    try:
        # Secuencia de poblamiento en orden jerárquico
        populate_base_hierarchy(session)
        populate_provinces_islands_municipalities(session)
        populate_locations(session)
        populate_levels(session)
        populate_achievements(session)

        session.commit()
        logger.info("Poblamiento completado exitosamente. Cambios confirmados.")

    except Exception as e:
        session.rollback()
        logger.error(f"Error durante el poblamiento. Revirtiendo cambios: {e}")
        logger.error(traceback.format_exc())
        raise
    finally:
        session.close()
        logger.info("Sesión de base de datos cerrada.")


if __name__ == "__main__":
    run_population()