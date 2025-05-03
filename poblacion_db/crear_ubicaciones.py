# poblacion_db/crear_ubicaciones.py

# Importaciones necesarias
# Importación ABSOLUTA de models.py para las clases
from models import Location, Municipality # Necesitamos Location y Municipality para crear objetos y consultar

# No necesitas importar session_setup aquí si recibes la sesión como argumento
# from .session_setup import get_session # o from poblacion_db.session_setup import get_session

# No importes la variable 'session' globalmente
# from session_setup import session # <-- ¡Incorrecto!

# La función para poblar ubicaciones debe recibir la instancia de sesión
def populate_locations(session):
    print("Creando ubicaciones...")

    # --- Obtener los objetos Municipality necesarios usando la sesión ---
    # Estos municipios deben haber sido creados y flusheados en populate_provinces_islands_municipalities
    # Los nombres deben coincidir EXACTAMENTE con los insertados.
    try:
        # Consultamos los municipios necesarios para las ubicaciones de ejemplo
        # Asegúrate de que los nombres coinciden con los insertados en el script anterior
        la_laguna_obj = session.query(Municipality).filter_by(name="San Cristóbal de La Laguna").one()
        sta_cruz_obj = session.query(Municipality).filter_by(name="Santa Cruz de Tenerife").one() # Ojo, es un municipio, no la provincia entera
        adeje_obj = session.query(Municipality).filter_by(name="Adeje").one()
        valencia_obj = session.query(Municipality).filter_by(name="Valencia").one()
        # TODO: Añadir consultas para todos los municipios necesarios para tus 20 ubicaciones
        # Ejemplo:
        # orotava_obj = session.query(Municipality).filter_by(name="La Orotava").one()
        # arona_obj = session.query(Municipality).filter_by(name="Arona").one()

    except Exception as e:
        # Capturamos la excepción (probablemente NoRowFound) e imprimimos un mensaje útil
        print(f"Error: No se encontraron uno o más objetos Municipality necesarios para crear ubicaciones.")
        print(f"Asegúrate de que: ")
        print(f"1. El script populate_provinces_islands_municipalities se ejecutó y flusheó correctamente.")
        print(f"2. Los nombres de los municipios en este script (filter_by) coinciden EXACTAMENTE (mayúsculas, minúsculas, tildes, espacios) con los nombres usados en populate_provinces_islands_municipalities.")
        print(f"Error original de SQLAlchemy: {e}")
        raise # Re-lanza la excepción para que main_populate.py capture y haga rollback


    # --- Definir y crear los objetos Location ---
    # Usa los objetos Municipality consultados para asignar la relación

    ubicaciones_list = [] # Creamos una lista para todas las ubicaciones

    # Ejemplo 1: Auditorio de Tenerife (en Santa Cruz de Tenerife - municipio)
    auditorio_tf = Location(
        name="Auditorio de Tenerife",
        description="Emblemático edificio diseñado por Santiago Calatrava en Santa Cruz de Tenerife.",
        latitude=28.4710,
        longitude=-16.2527,
        unlocked_content_url="https://ejemplo.com/foto_auditorio.jpg", # TODO: Reemplazar por URL real
        difficulty="Fácil Acceso",
        is_natural=False,
        best_season="Todo el Año",
        best_time_of_day="Todo el Día", # O "Tarde/Noche"
        municipality=sta_cruz_obj # <-- Usa el objeto Municipality de Santa Cruz (municipio)
    )
    ubicaciones_list.append(auditorio_tf)

    # Ejemplo 2: Siam Park (en Adeje)
    parque_siam = Location(
        name="Siam Park",
        description="Famoso parque acuático en Costa Adeje.",
        latitude=28.072088,
        longitude=-16.725585,
        unlocked_content_url="https://ejemplo.com/foto_siampark.jpg", # TODO: Reemplazar por URL real
        difficulty="Fácil Acceso",
        is_natural=False,
        best_season="Verano", # O "Todo el Año"
        best_time_of_day="Día Completo",
        municipality=adeje_obj # <-- Usa el objeto Municipality de Adeje
    )
    ubicaciones_list.append(parque_siam)

    palmetum_tnf = Location(
        name="Palmetum",
        description="Jardín botánico especializado en palmeras, construido sobre un antiguo vertedero.",
        latitude=28.4608,
        longitude=-16.2549,
        unlocked_content_url='https://ejemplo.com/foto_palmetum.jpg', # TODO: Reemplazar por URL real
        difficulty="Fácil Acceso",
        is_natural=False,
        best_season="Todo el Año", # O "Todo el Año"
        best_time_of_day="Día Completo",
        municipality=sta_cruz_obj 
    )
    ubicaciones_list.append(palmetum_tnf)

    ciudad_art_ciencia = Location(
        name='Ciudad de las Artes y las Ciencias',
        description= 'Impresionante complejo arquitectónico diseñado por Santiago Calatrava y Félix Candela.',
        latitude= 39.4658, # Coordenada aproximada
        longitude= -0.3559, # Coordenada aproximada
        unlocked_content_url='https://ejemplo.com/foto_cac.jpg', # Placeholder
        difficulty= 'Fácil Acceso',
        is_natural= False,
        best_season= 'Todo el Año',
        best_time_of_day= 'Día Completo',
        municipality= valencia_obj # <-- ID del municipio de Valencia
    )
    ubicaciones_list.append(ciudad_art_ciencia)

    mercado_central = Location(
        name='Mercado Central de Valencia',
        description= 'Uno de los mercados de abastos más grandes de Europa, con arquitectura modernista.',
        latitude= 39.4725, # Coordenada aproximada
        longitude= -0.3787, # Coordenada aproximada
        unlocked_content_url='https://ejemplo.com/foto_mercadocentral.jpg', # Placeholder
        difficulty= 'Fácil Acceso',
        is_natural= False,
        best_season= 'Todo el Año',
        best_time_of_day= 'Mañana', # Típicamente abre por las mañanas
        municipality= valencia_obj  # <-- ID del municipio de Valencia
    )
    ubicaciones_list.append(mercado_central)

    # Añade todos los objetos Location a la sesión de una vez
    session.add_all(ubicaciones_list) # Añade la lista completa

    # --- Añade esta línea aquí ---
    session.flush() # Fuerza la inserción de ubicaciones. Útil si el siguiente paso (logros)
                    # necesita IDs de ubicación o consultarlas por atributos no PK.

    # No hagas session.commit() aquí. El commit final lo hace main_populate.py.

    print(f"Añadidas {len(ubicaciones_list)} ubicaciones a la sesión y flusheadas.") # Muestra el total


# Este script está diseñado para ser llamado por main_populate.py