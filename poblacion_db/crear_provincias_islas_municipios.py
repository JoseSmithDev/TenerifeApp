# poblacion_db/crear_provincias_islas_municipios.py
"""
Módulo para poblar provincias, islas y municipios.
Debe ejecutarse después de populate_base_hierarchy.
"""

import logging
from models import Province, Island, Municipality, AutonomousCommunity, Country

logger = logging.getLogger(__name__)


def populate_provinces_islands_municipalities(session):
    """
    Crea provincias, islas y municipios.
    
    Args:
        session: Sesión de SQLAlchemy activa
    """
    logger.info("Creando provincias, islas y municipios...")

    try:
        espana = session.query(Country).filter_by(name="España").one()
        canarias = session.query(AutonomousCommunity).filter_by(name="Canarias").one()
        valencia_ca = session.query(AutonomousCommunity).filter_by(name="Comunidad Valenciana").one()
    except Exception as e:
        logger.error("No se encontraron los objetos Country o AutonomousCommunity necesarios.")
        logger.error("Asegúrate de que populate_base_hierarchy se ejecutó correctamente.")
        raise

    # Crear Provincias
    sta_cruz_tf_province = Province(name="Santa Cruz de Tenerife", autonomous_community=canarias)
    valencia_province = Province(name='Valencia', autonomous_community=valencia_ca)
    session.add_all([sta_cruz_tf_province, valencia_province])
    session.flush()
    logger.info("Provincias creadas y flusheadas.")

    # Crear Isla
    tenerife_island = Island(name="Tenerife", province=sta_cruz_tf_province)
    session.add(tenerife_island)
    session.flush()
    logger.info("Isla 'Tenerife' creada y flusheada.")

    # Crear Municipios de Tenerife
    municipios_tnf_nombres = [
        "Adeje", "Arafo", "Arico", "Arona", "Buenavista del Norte", "Candelaria",
        "Fasnia", "Garachico", "Granadilla de Abona", "Guía de Isora", "Güímar",
        "Icod de los Vinos", "La Guancha", "La Matanza de Acentejo", "La Orotava",
        "La Victoria de Acentejo", "Los Realejos", "Los Silos", "Puerto de la Cruz",
        "San Cristóbal de La Laguna", "San Juan de la Rambla", "San Miguel de Abona",
        "Santa Cruz de Tenerife", "Santa Úrsula", "Santiago del Teide", "El Sauzal",
        "Tacoronte", "El Tanque", "Tegueste", "Vilaflor de Chasna",
    ]

    municipios_vlc_nombres = ["Valencia"]

    municipio_objects_tnf = [
        Municipality(name=nombre, province=sta_cruz_tf_province)
        for nombre in municipios_tnf_nombres
    ]
    municipio_objects_vlc = [
        Municipality(name=nombre, province=valencia_province)
        for nombre in municipios_vlc_nombres
    ]

    todos_los_municipios = municipio_objects_tnf + municipio_objects_vlc
    session.add_all(todos_los_municipios)
    session.flush()

    logger.info(
        f"Provincia 'Santa Cruz de Tenerife', Isla 'Tenerife', Provincia 'Valencia' "
        f"y {len(todos_los_municipios)} municipios creados y flusheados."
    )