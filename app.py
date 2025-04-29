# backend/app.py

from flask import Flask, jsonify, request # Importa Flask y jsonify para respuestas JSON
# Importa tus modelos y setup de sesión desde donde los hayas guardado
# Si models.py está en el mismo directorio:
# from models import Location, get_session
# Si tienes session_setup.py en poblacion_db y models.py arriba:
# from models import Location
# from poblacion_db.session_setup import get_session # Asegúrate que poblacion_db es un paquete y models.py es accesible


# --- Ajusta estas importaciones según la estructura de tu proyecto ---
# Asumiremos que models.py está en la raíz del backend
import sys
import os

# Añade el directorio superior al path para poder importar models
# Obtén el directorio actual (donde está app.py, si está en backend/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Obtén el directorio padre (donde deberían estar models.py y poblacion_db)
parent_dir = os.path.join(current_dir, os.pardir)
sys.path.insert(0, parent_dir)

# Ahora deberías poder importar models y session_setup (si lo creaste)
from models import engine, Location, Base # Importamos Base también para el setup de sesión
# Si usas session_setup.py en poblacion_db:
# from poblacion_db.session_setup import get_session, SessionLocal


# --- Configuración de la Sesión de DB para Flask ---
# Es crucial manejar las sesiones correctamente en una aplicación web.
# Una práctica común es crear/cerrar una sesión por cada petición.

# Si no creaste session_setup.py, puedes definir SessionLocal aquí:
from sqlalchemy.orm import sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Configuración de la Aplicación Flask ---

app = Flask(__name__)

# Decorador para manejar la sesión de base de datos en cada petición
@app.before_request
def before_request():
    # Crea una sesión de DB antes de cada petición
    # request.db_session = SessionLocal() # Puedes adjuntarla al objeto request para fácil acceso
    # O simplemente usar get_db() en cada ruta
    pass # Usaremos una función get_db() dentro de las rutas o con un contexto

@app.teardown_request
def teardown_request(exception=None):
    # Cierra la sesión de DB después de cada petición, manejando posibles errores
    # db_session = getattr(request, 'db_session', None)
    # if db_session is not None:
    #     db_session.close()
    pass # La gestionaremos con un bloque try/finally o contextlib

# Función de utilidad para obtener una sesión y cerrarla automáticamente (recomendado)
from contextlib import contextmanager

@contextmanager
def get_db():
    """Proporciona una sesión de DB transaccional"""
    db = SessionLocal()
    try:
        yield db # Entrega la sesión al bloque 'with'
        db.commit() # Commit implícito al salir sin error
    except Exception:
        db.rollback() # Rollback si hay un error
        raise # Relanza la excepción
    finally:
        db.close() # Cierra la sesión


# --- Rutas de la API ---

@app.route('/locations', methods=['GET'])
def get_locations():
    """
    Endpoint para obtener la lista de todas las ubicaciones.
    """
    locations_list = []
    with get_db() as db: # Usa el contexto para gestionar la sesión
        # Consultar todas las ubicaciones desde la DB
        locations = db.query(Location).all()

        # Convertir objetos SQLAlchemy a diccionarios para JSON
        for loc in locations:
            # Aquí, si quieres incluir datos de la jerarquía, necesitarías cargar la relación
            # y añadirlos al diccionario. Por ahora, solo datos de Location.
            # loc.municipality.name # Esto accedería al nombre del municipio
            # loc.municipality.island.name # Y así sucesivamente

            location_data = {
                "location_id": loc.location_id,
                "name": loc.name,
                "description": loc.description,
                "latitude": loc.latitude,
                "longitude": loc.longitude,
                "unlocked_content_url": loc.unlocked_content_url,
                "difficulty": loc.difficulty,
                "is_natural": loc.is_natural,
                "best_season": loc.best_season,
                "best_time_of_day": loc.best_time_of_day,
                # Incluir el ID del municipio por ahora
                "municipality_id": loc.municipality_id,
                # Si quieres el nombre del municipio directamente:
                "municipality_name": loc.municipality.name if loc.municipality else None
            }

             # --- Añade esta línea para depurar ---
            print("Contenido del diccionario location_data:")
            print(location_data)
            print("-" * 20) # Línea separadora opcional para claridad en la salida
            # --- Fin de líneas de depuración ---

            locations_list.append(location_data)

    # Devolver la lista de ubicaciones como respuesta JSON
    return jsonify(locations_list)

# --- Endpoint GET /locations/<int:location_id> (Manejador de 404) ---
@app.route('/locations/<int:location_id>', methods=['GET'])
def get_location_details(location_id):
    """
    Endpoint para obtener los detalles de una ubicación específica por su ID.
    """
    with get_db() as db: # Usa el contexto para gestionar la sesión
        # Consultar la ubicación por su ID
        # Usamos .filter(Location.location_id == location_id) para buscar por PK
        # Usamos .first() que devuelve None si no encuentra nada (más fácil de manejar para 404)
        location = db.query(Location).filter(Location.location_id == location_id).first()

        # Si la ubicación no se encuentra, devolver un error 404
        if location is None:
            print(f"DEBUG /locations/{location_id}: Ubicación no encontrada en la DB.") # Debug
            return jsonify({"message": f"Ubicación con ID {location_id} no encontrada"}), 404 # 404 es el código de estado HTTP

        # Si la ubicación existe, convertir el objeto SQLAlchemy a un diccionario
        # Incluir información del municipio usando la relación
        municipality_name = location.municipality.name if location.municipality else None # Accede al nombre del municipio

        location_data = {
            "location_id": location.location_id,
            "name": location.name,
            "description": location.description,
            "latitude": location.latitude,
            "longitude": location.longitude,
            "unlocked_content_url": location.unlocked_content_url,
            "difficulty": location.difficulty,
            "is_natural": location.is_natural,
            "best_season": location.best_season,
            "best_time_of_day": location.best_time_of_day,
            # Incluir el ID y nombre del municipio
            "municipality_id": location.municipality_id,
            "municipality_name": municipality_name, # <-- Añadido nombre del municipio
            # TODO: Si necesitas más datos de jerarquía (isla, provincia), deberás cargarlos y añadirlos aquí
            # Ejemplo:
            # "island_name": location.municipality.island.name if location.municipality and location.municipality.island else None,
        }
        # TODO: Añadir más campos si necesitas más detalles en el frontend

        # --- Añade esta línea para depurar la salida de /locations/<id> ---
        print(f"DEBUG /locations/{location_id}: Contenido del diccionario location_data:")
        print(location_data)
        print("-" * 20)
        # --- Fin de líneas de depuración ---


        # Devolver el diccionario como respuesta JSON
        return jsonify(location_data)

# ... Otros endpoints irán aquí (checkin, users, reviews, etc.) ...

# Puedes añadir más endpoints aquí (ej: /locations/<int:location_id>)

# --- Ejecutar la Aplicación ---

if __name__ == '__main__':
    # Asegúrate de que la DB y las tablas existen (puedes llamarlo aquí o desde un script separado)
    # from models import create_database_tables
    # create_database_tables()

    # Asegúrate de que la DB esté poblada (ejecuta populate_db.py antes)
    # print("Recordatorio: Asegúrate de haber ejecutado models.py y populate_db.py antes de iniciar el servidor.")

    print("Iniciando servidor Flask...")
    # Puedes configurar el host y puerto si es necesario (ej: host='0.0.0.0' para acceso externo)
    app.run(debug=True) # debug=True es útil durante el desarrollo