# poblacion_db/crear_logros.py

# Importación correcta de session_setup (si la necesitas localmente, si no, no la importes aquí)
# from .session_setup import get_session
# from .session_setup import SessionLocal

# Importación ABSOLUTA de models.py
from models import Achievement, Municipality
import models # Posiblemente necesites Municipality u otros modelos para definir logros por entidad

# No importes la variable 'session' globalmente
# from session_setup import session # <-- ¡Incorrecto!

# Asegúrate de que la función se llame exactamente 'populate_achievements'
def populate_achievements(session): # <-- La función debe recibir la instancia de sesión
    print("Creando logros...")

    # --- Lógica para obtener entidades necesarias (ej: Municipios, Islas) si los logros son por entidad ---
    # Esto es necesario si tus logros son del tipo 'municipality_complete' o 'island_complete'
    # Ejemplo: Consultar el objeto La Laguna si tienes un logro de 'Completar La Laguna'
    try:
        # Asegúrate de que los municipios/islas ya se crearon en pasos anteriores
        la_laguna_obj = session.query(Municipality).filter_by(name="San Cristóbal de La Laguna").one()
        tenerife_obj = session.query(models.Island).filter_by(name="Tenerife").one() # Usa models.Island
        # Consulta otras entidades si es necesario
    except Exception as e:
         print(f"Error: No se encontraron las entidades necesarias (ej. Municipio, Isla) para definir logros. Asegúrate de que los pasos de poblamiento anteriores se ejecutaron y que los nombres coinciden. Error: {e}")
         raise # Re-lanza el error para que main_populate.py lo capture y haga rollback


    # --- Definir y crear los objetos Achievement ---

    logros_list = [
        Achievement(
            name="Primeros Pasos",
            description="Visita 5 ubicaciones en total.",
            type="total_count",
            target_entity_type="total", # Indica que aplica al total
            target_entity_id=None, # No aplica a una entidad específica
            target_value=5, # Número de visitas requerido
            unlocked_image_url="url_logro_5.png"
        ),
        Achievement(
            name="Conquistador de La Laguna",
            description="Visita todas las ubicaciones en San Cristóbal de La Laguna.",
            type="municipality_complete",
            target_entity_type="municipality",
            target_entity_id=la_laguna_obj.municipality_id, # Usar el ID del objeto consultado
            target_value=None, # La lógica del backend calculará el total de ubicaciones en este municipio
            unlocked_image_url="url_logro_laguna.png"
        ),
         Achievement(
            name="Tinerfeño de Corazón",
            description="Visita todas las ubicaciones en Tenerife.",
            type="island_complete",
            target_entity_type="island",
            target_entity_id=tenerife_obj.island_id, # Usar el ID del objeto consultado
            target_value=None,
            unlocked_image_url="url_logro_tenerife.png"
        ),
        # Añade aquí la definición de todos tus logros según el esquema de la DB
    ]

    # Añade todos los objetos Achievement a la sesión
    session.add_all(logros_list)

    # Opcional: Flush para que los IDs de logro se generen si es necesario
    # session.flush()

    # No hagas session.commit() aquí. El commit final lo hace main_populate.py.

    print(f"Añadidos {len(logros_list)} logros a la sesión.")


# Este script está diseñado para ser llamado por main_populate.py