# poblacion_db/populate_base_hierarchy.py
"""
Módulo para poblar la jerarquía base: Continente, País y Comunidades Autónomas.
Este script debe ejecutarse primero antes de poblar provincias, islas y municipios.
"""

import logging
from models import Continent, Country, AutonomousCommunity

logger = logging.getLogger(__name__)


def populate_base_hierarchy(session):
    """
    Crea la jerarquía base: Continente -> País -> Comunidades Autónomas.
    
    Args:
        session: Sesión de SQLAlchemy activa
    """
    logger.info("Creando jerarquía base: Continente, País, CCAA...")

    # 1. Crear Continente (Europa)
    europa = Continent(name="Europa")
    session.add(europa)
    session.flush()
    logger.info("Continente 'Europa' creado y flusheado.")

    # 2. Crear País (España) vinculado al continente
    espana = Country(name="España", continent=europa)
    session.add(espana)
    session.flush()
    logger.info("País 'España' creado y flusheado.")

    # 3. Crear Comunidades Autónomas vinculadas a España
    canarias = AutonomousCommunity(name="Canarias", country=espana)
    valencia = AutonomousCommunity(name="Comunidad Valenciana", country=espana)

    session.add_all([canarias, valencia])
    session.flush()
    logger.info("CCAA 'Canarias' y 'Comunidad Valenciana' creadas y flusheadas.")