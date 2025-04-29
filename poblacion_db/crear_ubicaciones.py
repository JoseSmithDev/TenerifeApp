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
        latitude=28.0718,
        longitude=-16.3379,
        unlocked_content_url="https://ejemplo.com/foto_siampark.jpg", # TODO: Reemplazar por URL real
        difficulty="Fácil Acceso",
        is_natural=False,
        best_season="Verano", # O "Todo el Año"
        best_time_of_day="Día Completo",
        municipality=adeje_obj # <-- Usa el objeto Municipality de Adeje
    )
    ubicaciones_list.append(parque_siam)

    # TODO: Añade aquí la lógica para crear las 18 ubicaciones restantes.
    # Por cada ubicación, crea el objeto Location y añádelo a la lista 'ubicaciones_list'.
    # Asegúrate de asignar el 'municipality' correcto usando los objetos Municipality consultados.
    # Puedes usar un diccionario grande con todos los datos de las 20 ubicaciones e iterar.
    # Ejemplo (Pseudocódigo):
    # datos_20_ubicaciones = [...] # Lista o dict con datos de todas las ubicaciones
    # for data in datos_20_ubicaciones:
    #     # Consultar el municipio para ESTA ubicación (o tener los objetos municipio en un dict)
    #     muni_obj_for_this_loc = session.query(Municipality).filter_by(name=data['municipio_nombre']).one()
    #     loc = Location(
    #         name=data['name'],
    #         description=data['description'],
    #         latitude=data['latitude'],
    #         longitude=data['longitude'],
    #         unlocked_content_url=data['unlocked_content_url'],
    #         difficulty=data['difficulty'],
    #         is_natural=data['is_natural'],
    #         best_season=data['best_season'],
    #         best_time_of_day=data['best_time_of_day'],
    #         municipality=muni_obj_for_this_loc # <-- Enlazar
    #     )
    #     ubicaciones_list.append(loc)


    # Añade todos los objetos Location a la sesión de una vez
    session.add_all(ubicaciones_list) # Añade la lista completa

    # --- Añade esta línea aquí ---
    session.flush() # Fuerza la inserción de ubicaciones. Útil si el siguiente paso (logros)
                    # necesita IDs de ubicación o consultarlas por atributos no PK.

    # No hagas session.commit() aquí. El commit final lo hace main_populate.py.

    print(f"Añadidas {len(ubicaciones_list)} ubicaciones a la sesión y flusheadas.") # Muestra el total


# Este script está diseñado para ser llamado por main_populate.py