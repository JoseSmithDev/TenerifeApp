# poblacion_db/crear_provincias_islas_municipios.py

# Importa el módulo models completo (necesario para consultas como models.Country)
import models

# Importaciones específicas de clases que vas a crear/usar directamente
from models import Province, Island, Municipality, AutonomousCommunity, Country

# Importación correcta de session_setup (si la necesitas localmente para pruebas, si no, no)
# from .session_setup import get_session
# from poblacion_db.session_setup import get_session

# No importes la variable 'session' globalmente
# from session_setup import session # <-- ¡Incorrecto!

# La función debe recibir la sesión como argumento
def populate_provinces_islands_municipalities(session): # <-- Recibe la sesión
    print("Creando provincias, islas y municipios...")

    # --- Lógica para obtener los objetos padre (España, Canarias) usando la sesión ---
    # Estos deben haber sido creados y flusheados en populate_base_hierarchy
    try:
        # Usamos models.Country y models.AutonomousCommunity porque importamos 'import models'
        # y estamos consultando esos modelos específicos.
        espana_obj = session.query(models.Country).filter_by(name="España").one()
        canarias_obj = session.query(models.AutonomousCommunity).filter_by(name="Canarias").one()
        # Si quieres ser más robusto, puedes verificar que no sean None, aunque .one() ya hace eso.
    except Exception as e:
        print(f"Error crítico: No se encontraron los objetos Country o AutonomousCommunity necesarios para crear jerarquía inferior.")
        print(f"Asegúrate de que populate_base_hierarchy se ejecutó y flusheó correctamente, y que los nombres 'España' y 'Canarias' son exactos.")
        # Mostrar detalles del error original
        # import traceback
        # traceback.print_exc()
        raise # Re-lanza el error para que main_populate.py lo capture y haga rollback


    # --- Lógica para crear la Provincia, la Isla y los Municipios de Tenerife ---

    # 1. Crear Provincia (Santa Cruz de Tenerife)
    # Se enlaza a la Comunidad Autónoma de Canarias
    sta_cruz_tf_province = Province(name="Santa Cruz de Tenerife", autonomous_community=canarias_obj)
    session.add(sta_cruz_tf_province)
    # Hacemos flush para que la provincia tenga ID antes de crear la isla que la referencia
    session.flush()


    # 2. Crear Isla (Tenerife)
    # Se enlaza a la Provincia de Santa Cruz de Tenerife
    tenerife_island = Island(name="Tenerife", province=sta_cruz_tf_province)
    session.add(tenerife_island)
    # Hacemos flush para que la isla tenga ID antes de crear los municipios que la referencian
    session.flush()


    # 3. Crear Municipios de Tenerife
    # Se enlazan a la Isla de Tenerife
    # --- LISTA COMPLETA DE MUNICIPIOS DE TENERIFE ---
    # **VERIFICA ESTOS NOMBRES MINUCIOSAMENTE.**
    # Esta fue la causa más probable del error anterior (No row was found).
    # Copia y pega esta lista si es necesario en tu código de populate_ubicaciones
    # para asegurar que los nombres de consulta coincidan exactamente.
    municipios_data = [
        "Adeje",
        "Arafo",
        "Arico",
        "Arona",
        "Buenavista del Norte",
        "Candelaria",
        "Fasnia",
        "Garachico",
        "Granadilla de Abona",
        "Guía de Isora",
        "Güímar", # Ojo con la tilde en Güímar
        "Icod de los Vinos",
        "La Guancha",
        "La Matanza de Acentejo",
        "La Orotava",
        "La Victoria de Acentejo",
        "Los Realejos",
        "Los Silos",
        "Puerto de la Cruz",
        "San Cristóbal de La Laguna", # Ojo con tildes y espacios
        "San Juan de la Rambla",
        "San Miguel de Abona",
        "Santa Cruz de Tenerife", # Ojo: Este es el municipio de Santa Cruz, distinto de la provincia.
        "Santa Úrsula", # Ojo con la tilde en Úrsula
        "Santiago del Teide",
        "El Sauzal",
        "Tacoronte",
        "El Tanque", # Nombre oficial es 'El Tanque', no solo 'Tanque'
        "Tegueste",
        "Vilaflor de Chasna", # Nombre oficial es 'Vilaflor de Chasna', no solo 'Vilaflor'
    ]

    # Crear objetos Municipality a partir de la lista de nombres y enlazarlos a la isla de Tenerife
    municipio_objects = [Municipality(name=nombre, island=tenerife_island) for nombre in municipios_data]
    session.add_all(municipio_objects)


    # --- Añade esta línea ---
    # Es CRUCIAL flushear después de añadir los municipios para que puedan ser consultados
    # por su nombre en el siguiente script (populate_locations).
    session.flush()


    print(f"Añadidas Provincia 'Santa Cruz de Tenerife', Isla 'Tenerife' y {len(municipio_objects)} municipios a la sesión y flusheados.")


# Este script está diseñado para ser llamado por main_populate.py
# main_populate.py lo llamará después de populate_base_hierarchy.