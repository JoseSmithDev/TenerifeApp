# poblacion_db/crear_logros.py
"""
Módulo para poblar logros (achievements).
Debe ejecutarse después de populate_locations y populate_provinces_islands_municipalities.
"""

import logging
from models import Achievement, Municipality, Island

logger = logging.getLogger(__name__)


def populate_achievements(session):
    """
    Crea los logros iniciales del sistema.
    
    Args:
        session: Sesión de SQLAlchemy activa
    """
    logger.info("Creando logros...")

    try:
        la_laguna = session.query(Municipality).filter_by(name="San Cristóbal de La Laguna").one()
        tenerife = session.query(Island).filter_by(name="Tenerife").one()
    except Exception as e:
        logger.error("No se encontraron las entidades necesarias para definir logros.")
        logger.error("Asegúrate de que los pasos de poblamiento anteriores se ejecutaron correctamente.")
        raise

    logros = [
        Achievement(
            name="Primeros Pasos",
            description="Visita 5 ubicaciones en total.",
            type="total_count",
            target_entity_type="total",
            target_entity_id=None,
            target_value=5,
            unlocked_image_url="url_logro_5.png"
        ),
        Achievement(
            name="Conquistador de La Laguna",
            description="Visita todas las ubicaciones en San Cristóbal de La Laguna.",
            type="municipality_complete",
            target_entity_type="municipality",
            target_entity_id=la_laguna.municipality_id,
            target_value=None,
            unlocked_image_url="url_logro_laguna.png"
        ),
        Achievement(
            name="Tinerfeño de Corazón",
            description="Visita todas las ubicaciones en Tenerife.",
            type="island_complete",
            target_entity_type="island",
            target_entity_id=tenerife.island_id,
            target_value=None,
            unlocked_image_url="url_logro_tenerife.png"
        ),
    ]

    session.add_all(logros)
    logger.info(f"Añadidos {len(logros)} logros a la sesión.")