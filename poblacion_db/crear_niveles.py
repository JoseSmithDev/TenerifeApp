# poblacion_db/crear_niveles.py
"""
Módulo para poblar niveles del sistema.
"""

import logging
from models import Level

logger = logging.getLogger(__name__)


def populate_levels(session):
    """
    Crea los niveles iniciales del sistema.
    
    Args:
        session: Sesión de SQLAlchemy activa
    """
    logger.info("Creando niveles...")
    
    niveles = [
        Level(name="Novato Explorador", visits_required=0, image_url="url_nivel_1.png"),
        Level(name="Visitante Local", visits_required=3, image_url="url_nivel_2.png"),
        Level(name="Conquistador de Tenerife", visits_required=10, image_url="url_nivel_3.png"),
        Level(name="Leyenda de Tenerife", visits_required=20, image_url="url_nivel_4.png"),
    ]
    
    session.add_all(niveles)
    logger.info(f"Añadidos {len(niveles)} niveles a la sesión.")