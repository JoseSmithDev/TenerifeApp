# poblacion_db/crear_ubicaciones.py
"""
Módulo para poblar ubicaciones (locations).
Debe ejecutarse después de populate_provinces_islands_municipalities.
"""

import logging
import os
from models import Location, Municipality

logger = logging.getLogger(__name__)

# Configuración de URLs base (puede moverse a variables de entorno)
BASE_URL = os.getenv('BASE_URL', 'http://10.0.2.2:5000')


def populate_locations(session):
    """
    Crea ubicaciones de ejemplo.
    
    Args:
        session: Sesión de SQLAlchemy activa
    """
    logger.info("Creando ubicaciones...")

    try:
        la_laguna = session.query(Municipality).filter_by(name="San Cristóbal de La Laguna").one()
        sta_cruz = session.query(Municipality).filter_by(name="Santa Cruz de Tenerife").one()
        adeje = session.query(Municipality).filter_by(name="Adeje").one()
        valencia = session.query(Municipality).filter_by(name="Valencia").one()
    except Exception as e:
        logger.error("No se encontraron uno o más objetos Municipality necesarios.")
        logger.error("Asegúrate de que populate_provinces_islands_municipalities se ejecutó correctamente.")
        raise

    ubicaciones = [
        Location(
            name="Auditorio de Tenerife",
            description="Emblemático edificio diseñado por Santiago Calatrava en Santa Cruz de Tenerife.",
            latitude=28.4710,
            longitude=-16.2527,
            main_image_url=f"{BASE_URL}/static/location_images/auditorio-santa-cruz.jpg",
            unlocked_content_url=f"{BASE_URL}/static/location_images/auditorio-santa-cruz.jpg",
            difficulty="Fácil Acceso",
            is_natural=False,
            best_season="Todo el Año",
            best_time_of_day="Todo el Día",
            municipality=sta_cruz
        ),
        Location(
            name="Siam Park",
            description="Famoso parque acuático en Costa Adeje.",
            latitude=28.072088,
            longitude=-16.725585,
            main_image_url=f"{BASE_URL}/static/location_images/Siam-Park.jpg",
            unlocked_content_url=f"{BASE_URL}/static/location_images/Siam-Park.jpg",
            difficulty="Fácil Acceso",
            is_natural=False,
            best_season="Verano",
            best_time_of_day="Día Completo",
            municipality=adeje
        ),
        Location(
            name="Palmetum",
            description="Jardín botánico especializado en palmeras, construido sobre un antiguo vertedero.",
            latitude=28.4608,
            longitude=-16.2549,
            unlocked_content_url=f"{BASE_URL}/static/location_images/palmetum.jpg",
            difficulty="Fácil Acceso",
            is_natural=False,
            best_season="Todo el Año",
            best_time_of_day="Día Completo",
            municipality=sta_cruz
        ),
        Location(
            name="Ciudad de las Artes y las Ciencias",
            description="Impresionante complejo arquitectónico diseñado por Santiago Calatrava y Félix Candela.",
            latitude=39.4658,
            longitude=-0.3559,
            unlocked_content_url=f"{BASE_URL}/static/location_images/cac.jpg",
            difficulty="Fácil Acceso",
            is_natural=False,
            best_season="Todo el Año",
            best_time_of_day="Día Completo",
            municipality=valencia
        ),
        Location(
            name="Mercado Central de Valencia",
            description="Uno de los mercados de abastos más grandes de Europa, con arquitectura modernista.",
            latitude=39.4725,
            longitude=-0.3787,
            unlocked_content_url=f"{BASE_URL}/static/location_images/mercadocentral.jpg",
            difficulty="Fácil Acceso",
            is_natural=False,
            best_season="Todo el Año",
            best_time_of_day="Mañana",
            municipality=valencia
        ),
    ]

    session.add_all(ubicaciones)
    session.flush()

    logger.info(f"Añadidas {len(ubicaciones)} ubicaciones y flusheadas.")