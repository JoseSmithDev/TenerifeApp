# backend/app.py

from flask import Flask, jsonify, request
from sqlalchemy import join, distinct, func
import models, json
from poblacion_db.session_setup import SessionLocal  # Importa Flask y jsonify para respuestas JSON
# Importa tus modelos y setup de sesión desde donde los hayas guardado
# Si models.py está en el mismo directorio:
# from models import Location, get_session
# Si tienes session_setup.py en poblacion_db y models.py arriba:
# from models import Location
# from poblacion_db.session_setup import get_session # Asegúrate que poblacion_db es un paquete y models.py es accesible

# Importamos engine, Location, Municipality y Base desde models.py
# (Deja esta línea también, la necesitas para usar esos nombres directamente)

# --- Ajusta estas importaciones según la estructura de tu proyecto ---
# Asumiremos que models.py está en la raíz del backend
import sys
import os

from models import engine, Location, Municipality, Base, User, UserLocationVisit, Achievement, UserAchievement #
# --- Importación para seguridad de contraseñas ---
from werkzeug.security import generate_password_hash, check_password_hash

# --- Importación para cálculo de distancia ---
from geopy.distance import geodesic # Importa la función geodesic de geopy.distance

CHECKIN_RADIUS_METERS = 4000


ACHIEVEMENTS = [
    {"id": 1, "name": "Novato Explorador", "description": "Visita tu primera ubicación única.", "criteria": {"type": "total_unique_visits", "count": 1}},
    {"id": 2, "name": "Explorador Entusiasta", "description": "Visita 5 ubicaciones únicas.", "criteria": {"type": "total_unique_visits", "count": 5}},
    {"id": 3, "name": "Conquistador de Municipios (1)", "description": "Visita ubicaciones en 1 municipio diferente.", "criteria": {"type": "unique_municipalities", "count": 1}},
    {"id": 4, "name": "Conquistador de Municipios (3)", "description": "Visita ubicaciones en 3 municipios diferentes.", "criteria": {"type": "unique_municipalities", "count": 3}},
    # Puedes añadir más logros aquí basados en otros criterios si quieres
]
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



@app.route('/locations', methods=['GET']) # <-- Decorador para la ruta /locations
def get_all_locations(): # <-- La función que maneja /locations GET
    print("DEBUG: Recibida petición a /locations")

    # --- Leer el parámetro de filtro por municipio desde la query string ---
    # request.args.get('municipality_id') obtiene el valor del parámetro 'municipality_id'
    # .get() devuelve None si el parámetro no está presente.
    municipality_id_str = request.args.get('municipality_id')
    municipality_id = None
    if municipality_id_str:
        try:
            municipality_id = int(municipality_id_str) # Intentar convertir a entero
            print(f"DEBUG: Filtro por municipality_id recibido: {municipality_id}")
        except ValueError:
            # Si el valor no es un entero, puedes manejar el error o ignorar el filtro
            print(f"DEBUG: Valor de municipality_id '{municipality_id_str}' no es un entero válido. Ignorando filtro.")
            # Opcional: Retornar un error 400 Bad Request si el filtro es inválido
            # return jsonify({"message": "ID de municipio inválido"}), 400


    with get_db() as db:
        # Consulta base: obtener todas las ubicaciones y sus municipios
        query = db.query(Location, Municipality).\
                   join(Municipality, Location.municipality_id == Municipality.municipality_id)

        # --- Aplicar filtro condicional por municipio ---
        if municipality_id is not None:
            # Si se proporcionó un municipality_id válido, añadir el filtro
            query = query.filter(Location.municipality_id == municipality_id)
            print(f"DEBUG: Aplicando filtro por municipality_id = {municipality_id}")
        else:
            print("DEBUG: No se aplicó filtro por municipality_id.")


        # Ejecutar la consulta (filtrada o no)
        locations = query.all()

        print(f"DEBUG: get_all_locations - Encontradas {len(locations)} ubicaciones (filtradas: {municipality_id is not None}).")


        # Formatear los resultados
        locations_list = []
        # locations es una lista de tuplas (Location, Municipality)
        for location, municipality in locations:
            locations_list.append({
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
                "municipality_id": location.municipality_id, # Incluir el ID del municipio también
                "municipality_name": municipality.name, # Incluir el nombre del municipio
            })

        # Retornar la lista de ubicaciones (filtrada o no)
        return jsonify(locations_list), 200

# --- Rutas de la API ---
# --- Endpoint GET /locations/<int:location_id> (Manejador de 404) ---
# --- Asegúrate que tu función get_location_details esté CORRECTAMENTE definida ---
# Debería verse similar a esto, con el <int:location_id> en el decorador:
@app.route('/locations/<int:location_id>', methods=['GET'])
def get_location_details(location_id):
    # ... código de get_location_details (busca por location_id) ...
    print(f"DEBUG: Recibida petición a /locations/{location_id}")
    with get_db() as db:
        # Asegúrate que tu consulta aquí filtra por Location.location_id == location_id
        # ... consulta ...
        location = db.query(Location, Municipality)\
             .join(Municipality, Location.municipality_id == Municipality.municipality_id)\
             .filter(Location.location_id == location_id)\
             .first() # <--- Aquí NO debería haber \
        
        if location:
             location_obj, muni_obj = location # Desempaquetar la tupla
             location_data = {
                "location_id": location_obj.location_id,
                "name": location_obj.name,
                "description": location_obj.description,
                "latitude": location_obj.latitude,
                "longitude": location_obj.longitude,
                "unlocked_content_url": location_obj.unlocked_content_url,
                "difficulty": location_obj.difficulty,
                "is_natural": location_obj.is_natural,
                "best_season": location_obj.best_season,
                "best_time_of_day": location_obj.best_time_of_day,
                "municipality_id": location_obj.municipality_id,
                "municipality_name": muni_obj.name,
            }
             print(f"DEBUG /locations/{location_id}: Contenido del diccionario location_data: {location_data}")
             return jsonify(location_data), 200
        else:
            print(f"DEBUG /locations/{location_id}: Ubicación no encontrada.")
            return jsonify({"message": "Ubicación no encontrada"}), 404

# ... Otros endpoints irán aquí (checkin, users, reviews, etc.) ...

# Puedes añadir más endpoints aquí (ej: /locations/<int:location_id>)

# backend/app.py

# ... tus importaciones (Flask, jsonify, request, sys, os, models, etc.) ...
# ... tu configuración de DB (engine, SessionLocal, get_db) ...
# ... tus modelos (Continent, Country, Location, User, etc.) ...
# ... tu ruta GET /locations ...
# ... tu ruta GET /locations/<int:location_id> ...


# --- Nueva Ruta para Check-in ---
@app.route('/checkin', methods=['POST'])
def checkin_location():
    print("DEBUG: Recibida petición a /checkin")

    # ... (código para obtener y validar datos user_id, location_id, user_lat, user_lng) ...
    # Asegúrate que la conversión a float de user_lat/lng está ANTES de usar en geodesic
    try:
        user_lat = float(request.json.get('latitude'))
        user_lng = float(request.json.get('longitude'))
        user_id = int(request.json.get('user_id')) # Asegurar que user_id es int
        location_id = int(request.json.get('location_id')) # Asegurar que location_id es int
    except (ValueError, TypeError):
        print("DEBUG: Petición /checkin - Coordenadas o IDs no válidos.")
        return jsonify({"message": "Los IDs y coordenadas deben ser valores numéricos válidos"}), 400


    print(f"DEBUG: Datos recibidos para check-in: UserID={user_id}, LocationID={location_id}, Lat={user_lat}, Lng={user_lng}")

    # Conectar a la base de datos
    with get_db() as db:
        # Buscar la ubicación por el ID proporcionado
        location = db.query(Location).filter(Location.location_id == location_id).first()

        if location is None:
            print(f"DEBUG: Petición /checkin - Ubicación con ID {location_id} no encontrada en DB.")
            return jsonify({"message": f"Ubicación con ID {location_id} no encontrada en la base de datos"}), 404

        # --- Lógica de Verificación de Distancia ---
        user_coords = (user_lat, user_lng)
        location_coords = (location.latitude, location.longitude)
        distance_in_meters = geodesic(user_coords, location_coords).meters
        

        print(f"DEBUG: Distancia calculada: {distance_in_meters:.2f} metros. Radio permitido: {CHECKIN_RADIUS_METERS} metros.")


        # Comparar la distancia con el radio permitido
        if distance_in_meters <= CHECKIN_RADIUS_METERS:
            # --- CHECK-IN EXITOSO POR DISTANCIA ---
            print(f"DEBUG: Check-in exitoso por distancia para ubicación {location.name}. Procediendo a registrar visita.")

            # *** IMPLEMENTACIÓN: Registrar el check-in en la base de datos para el usuario ***
            # Opcional: Verificar si el usuario ya ha visitado esta ubicación muy recientemente (código comentado anteriormente)

            try:
                # Crear una nueva instancia de visita
                # visit_timestamp se generará por defecto con datetime.utcnow() si no lo especificas en el modelo
                new_visit = UserLocationVisit(user_id=user_id, location_id=location_id)

                db.add(new_visit) # Añadir la nueva visita a la sesión
                db.refresh(new_visit) # Refrescar para obtener el ID de la visita y timestamp real de DB

                print(f"DEBUG: Check-in - Visita registrada exitosamente: VisitID={new_visit.visit_id}, UserID={user_id}, LocationID={location_id}, Timestamp={new_visit.visit_timestamp}")

                print(f"DEBUG Backend: Verificando logros para user {user_id} después de visitar location {location_id}")

                 # 1. Obtener estadísticas actualizadas del usuario
                # Reutilizamos lógica de consulta de /users/<user_id>/visits
                # Contar ubicaciones únicas visitadas
                unique_visits_count = db.query(func.count(distinct(UserLocationVisit.location_id)))\
                                .filter_by(user_id=user_id)\
                                .scalar() # Usar .scalar() para obtener el único resultado del conteo
                
                # Contar municipios únicos visitados
                # Necesitamos unir UserLocationVisit -> Location -> Municipality
                unique_municipalities_count = db.query(func.count(distinct(Municipality.municipality_id)))\
                                        .join(Location, Location.municipality_id == Municipality.municipality_id)\
                                        .join(UserLocationVisit, UserLocationVisit.location_id == Location.location_id)\
                                        .filter(UserLocationVisit.user_id == user_id)\
                                        .scalar() # Usar .scalar() para obtener el único resultado del conteo

                print(f"DEBUG Backend: Estadísticas actualizadas - Visitas Únicas: {unique_visits_count}, Municipios Únicos: {unique_municipalities_count}")

                # 2. Obtener IDs de logros ya ganados por el usuario
                earned_achievement_ids = {ua.achievement_id for ua in db.query(UserAchievement).filter_by(user_id=user_id).all()}
                print(f"DEBUG Backend: Logros ya ganados por user {user_id}: {earned_achievement_ids}")

                unlocked_achievements = []

                # 3. Iterar a través de los logros definidos y comprobar
                # Asegúrate de que tu lista ACHIEVEMENTS esté definida en este archivo o importada
                # ACHIEVEMENT_TOTAL_VISITAS = 1 # Ejemplo de ID de logro (ajustar según tu ACHIEVEMENTS)
                # ACHIEVEMENT_PRIMER_MUNICIPIO = 2 # Ejemplo de ID de logro (ajustar según tu ACHIEVEMENTS)
                # ... etc.

                for achievement_data in ACHIEVEMENTS: # Itera sobre la lista de logros definidos (debes tenerla)
                    achievement_id = achievement_data['id']
                    required_visits = achievement_data.get('required_visits') # None si no aplica
                    required_municipalities = achievement_data.get('required_municipalities') # None si no aplica

                # 4. Comprobar si el logro ya fue ganado
                    if achievement_id in earned_achievement_ids:
                        print(f"DEBUG Backend: Logro {achievement_id} ya ganado. Saltando comprobación.")
                        continue # Saltar si ya lo tiene


                # 5. Comprobar si cumple los requisitos CON las estadísticas actualizadas
                is_unlocked = False
                if required_visits is not None and unique_visits_count >= required_visits:
                    is_unlocked = True # Cumple requisito de visitas
            
                if required_municipalities is not None and unique_municipalities_count >= required_municipalities:
                    # Si tiene requisito de visitas Y municipios, ambos deben cumplirse.
                    # Si solo tiene requisito de municipios, basta con que cumpla ese.
                    if required_visits is not None: # Si también requiere visitas, comprueba que is_unlocked ya sea True
                        if is_unlocked and unique_municipalities_count >= required_municipalities:
                           is_unlocked = True
                        else:
                           is_unlocked = False # No cumple ambos
                    else: # Si solo requiere municipios
                     is_unlocked = True

                # Lógica más compleja para otros tipos de logros iría aquí
                # ej: required_locations: [{'location_id': 1}, {'location_id': 5}]


                # 6. Si el logro es desbloqueado y no lo tenía
                if is_unlocked:
                    print(f"DEBUG Backend: Logro {achievement_id} DESBLOQUEADO para user {user_id}!")
                    new_user_achievement = UserAchievement(user_id=user_id, achievement_id=achievement_id)
                    db.add(new_user_achievement) # Añadir el nuevo logro ganado a la sesión
                    unlocked_achievements.append(achievement_data) # Añadir a la lista de logros desbloqueados en esta petición

                # --- Fin Lógica de Desbloqueo de Logros ---
        
                db.commit() # Guardar la nueva visita Y los nuevos logros (si los hay) en la base de datos

                # --- Código existente o modificado: Retornar la respuesta ---
                # Puedes modificar la respuesta para incluir los logros desbloqueados
                response_data = {
                    "message": "Check-in exitoso!",
                    "location_id": location_id,
                    "user_id": user_id,
                    "unlocked_achievements": unlocked_achievements # Añadimos la lista de logros desbloqueados
                }
                return jsonify(response_data), 200

                # Retornar respuesta de éxito
                return jsonify({
                    "message": f"¡Check-in exitoso en {location.name}! Tu visita ha sido registrada.",
                    "status": "success",
                    "distancia_metros": round(distance_in_meters, 2),
                    "radio_permitido_metros": CHECKIN_RADIUS_METERS,
                    "visit_id": new_visit.visit_id # Opcional: devolver el ID de la visita creada
                }), 200 # 200 OK
        
            except Exception as e:
                db.rollback()
                print(f"DEBUG: Check-in - Error al registrar visita para UserID={user_id}, LocationID={location_id}: {e}")
                # Este mensaje es devuelto al frontend
                return jsonify({"message": f"Error interno al registrar la visita: {e}", "status": "error_db"}), 500


        else:
            # --- CHECK-IN FALLIDO (Demasiado lejos) ---
            print(f"DEBUG: Check-in fallido para ubicación {location.name}. Demasiado lejos.")
            # Retornar respuesta de fallo por distancia
            return jsonify({
                "message": f"Estás demasiado lejos de {location.name} ({distance_in_meters:.2f}m). Necesitas estar más cerca de {CHECKIN_RADIUS_METERS}m para hacer check-in.",
                "status": "too_far",
                "distancia_metros": round(distance_in_meters, 2),
                "radio_permitido_metros": CHECKIN_RADIUS_METERS
            }), 200 # Retornamos 200 porque la petición POST fue válida




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



# --- Ruta para obtener todas las ubicaciones (incluyendo filtro por municipio) ---




@app.route('/register', methods=['POST'])
def register_user():
    print("DEBUG: Recibida petición a /register")
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        print("DEBUG: Registro - Faltan username o password en JSON.")
        return jsonify({"message": "Se requiere nombre de usuario y contraseña"}), 400

    username = request.json['username']
    password = request.json['password']

    print(f"DEBUG: Registro - Intentando registrar usuario: {username}")

    with get_db() as db:
        # Verificar si el nombre de usuario ya existe
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"DEBUG: Registro - Usuario existente: {username}")
            return jsonify({"message": "El nombre de usuario ya existe"}), 409 # 409 Conflict

        # Hashear la contraseña de forma segura
        password_hash = generate_password_hash(password)

        # Crear el nuevo usuario
        new_user = User(username=username, password_hash=password_hash)
        db.add(new_user)

        try:
            db.commit() # Intentar guardar en DB
            print(f"DEBUG: Registro - Usuario {username} registrado exitosamente con ID: {new_user.user_id}")
            # db.refresh(new_user) # Opcional si necesitas el ID inmediatamente después del commit

            # Retornar una respuesta de éxito
            return jsonify({"message": "Usuario registrado exitosamente", "user_id": new_user.user_id}), 201 # 201 Created

        except Exception as e:
            db.rollback() # Deshacer si hay un error
            print(f"DEBUG: Registro - Error al registrar usuario {username}: {e}")
            return jsonify({"message": f"Error al registrar usuario: {e}"}), 500 # 500 Internal Server Error
        

@app.route('/users/<int:user_id>/visits', methods=['GET'])
def get_user_visits(user_id): # El user_id de la URL se pasa como argumento a la función
    print(f"DEBUG: Recibida petición a /users/{user_id}/visits")

    with get_db() as db:
        # Opcional: Verificar si el usuario existe (buena práctica)
        user = db.query(User).filter(User.user_id == user_id).first()
        if user is None:
            print(f"DEBUG: get_user_visits - Usuario con ID {user_id} no encontrado.")
            return jsonify({"message": f"Usuario con ID {user_id} no encontrado"}), 404 # 404 Not Found

        # Consultar las visitas de este usuario, uniendo con la tabla locations
        # Queremos obtener los detalles de la ubicación visitada
        # ¡CORREGIDO! Pedimos los 3 modelos en la consulta
        visits = (db.query(UserLocationVisit, Location, Municipality) # <-- Abre paréntesis aquí
                         .join(Location, UserLocationVisit.location_id == Location.location_id)
                         .join(Municipality, Location.municipality_id == Municipality.municipality_id)
                         .filter(UserLocationVisit.user_id == user_id)
                         .all()) # <-- Cierra paréntesis aquí y NO pongas \
        print(f"DEBUG: get_user_visits - Encontradas {len(visits)} visitas para UserID {user_id}.")

        # --- Consulta para el Total de UBICACIONES DISPONIBLES ---
        # Cuenta todas las filas en la tabla Location
        total_available_locations_query = db.query(func.count(Location.location_id)).scalar() # .scalar() obtiene el primer resultado de una columna única

        print(f"DEBUG: get_user_visits - Total de ubicaciones disponibles encontradas: {total_available_locations_query}.")
        
        visited_location_ids_query = db.query(distinct(UserLocationVisit.location_id)).\
                                       filter(UserLocationVisit.user_id == user_id).\
                                       subquery() # La convertimos en una subconsulta

        # Luego, consultamos los detalles de esas ubicaciones únicas, uniendo con Municipality
        # Seleccionamos las ubicaciones cuyo ID está en la lista de IDs visitados
        unique_visits_query = (db.query(Location, Municipality)
                               .join(Municipality, Location.municipality_id == Municipality.municipality_id)
                               .filter(Location.location_id.in_(visited_location_ids_query)) # Filtrar por los IDs únicos visitados
                               .all()) # Obtener la lista de objetos Location y Municipality para ubicaciones únicas
        
         # --- NUEVA Consulta para Progreso por Municipio ---
        # Contar ubicaciones únicas visitadas por municipio para este usuario
        progress_by_municipality_query = (db.query(Municipality.name, func.count(distinct(Location.location_id)))
                                           .join(Location, Municipality.municipality_id == Location.municipality_id)
                                           .join(UserLocationVisit, Location.location_id == UserLocationVisit.location_id)
                                           .filter(UserLocationVisit.user_id == user_id) # Filtrar por el usuario
                                           .group_by(Municipality.name) # Agrupar por nombre de municipio
                                           .all()) # Ejecutar la consulta
        
        print(f"DEBUG: get_user_visits - Progreso por municipio encontrado: {progress_by_municipality_query}")

        # El número total de ubicaciones únicas visitadas es la longitud de esta lista
        total_unique_visits = len(unique_visits_query)

        print(f"DEBUG: get_user_visits - Encontradas {total_unique_visits} UBICACIONES ÚNICAS visitadas para UserID {user_id}.")

        progress_by_municipality_list = []
        # progress_by_municipality_query es una lista de tuplas: (municipality_name, visited_count)
        for muni_name, visited_count in progress_by_municipality_query:
            progress_by_municipality_list.append({
                "municipality_name": muni_name,
                "visited_count": visited_count
            })


        # Formatear los resultados en una lista de diccionarios para la respuesta JSON
        # visits es una lista de tuplas (UserLocationVisit, Location)
        visited_locations_list = []
        for location, municipality in unique_visits_query:
            visited_locations_list.append({
                # Incluir detalles relevantes de la ubicación
                "location_id": location.location_id,
                "name": location.name,
                "description": location.description,
                "latitude": location.latitude,
                "longitude": location.longitude,
                "difficulty": location.difficulty,
                "is_natural": location.is_natural,
                "best_season": location.best_season,
                "best_time_of_day": location.best_time_of_day,
                "municipality_name": municipality.name, # Asumiendo que ya tienes este campo
                # Opcional: incluir detalles de la visita si son relevantes (timestamp, etc.)
                # "visit_id": visit.visit_id,
                # "visit_timestamp": visit.visit_timestamp.isoformat() # Formato ISO 8601 para compatibilidad JSON
            })

        response_data = {
            "total_visits": total_unique_visits,
            "visited_locations": visited_locations_list,
            "total_locations": total_available_locations_query,
            "progress_by_municipality": progress_by_municipality_list # <-- ¡Añade el progreso por municipio aquí!
        }
        return jsonify(response_data), 200


# --- Nueva Ruta para Inicio de Sesión de Usuario ---
@app.route('/login', methods=['POST'])
def login_user():
    print("DEBUG: Recibida petición a /login")
    if not request.json or not 'username' in request.json or not 'password' in request.json:
        print("DEBUG: Login - Faltan username o password en JSON.")
        return jsonify({"message": "Se requiere nombre de usuario y contraseña"}), 400

    username = request.json['username']
    password = request.json['password']

    print(f"DEBUG: Login - Intentando iniciar sesión para usuario: {username}")

    with get_db() as db:
        # Buscar el usuario por nombre de usuario
        user = db.query(User).filter(User.username == username).first()

        # Verificar si el usuario existe y si la contraseña es correcta
        if user and check_password_hash(user.password_hash, password):
            # *** TODO: Implementar manejo de sesión o tokens de autenticación aquí ***
            # Por ahora, solo confirmamos el login y devolvemos el user_id.
            print(f"DEBUG: Login exitoso para usuario: {username} (ID: {user.user_id})")
            return jsonify({"message": "Inicio de sesión exitoso", "user_id": user.user_id}), 200 # 200 OK
        else:
            print(f"DEBUG: Login fallido para usuario: {username} (Credenciales inválidas)")
            return jsonify({"message": "Nombre de usuario o contraseña incorrectos"}), 401 # 401 Unauthorized


@app.route('/users/<int:user_id>/achievements', methods=['GET'])
def get_user_achievements(user_id):
    print(f"DEBUG: Recibida petición a /users/{user_id}/achievements")

    progress_response, status_code = get_user_visits(user_id) # Llama a la función existente

    if status_code != 200:
        # Si get_user_visits falló (ej: usuario no encontrado), retornamos ese error
        return progress_response, status_code
    
    # Decodificamos el cuerpo de la respuesta de get_user_visits
    progress_data = json.loads(progress_response.get_data()) # Obtiene los datos del Response object

    # Extraer los datos necesarios para evaluar logros
    total_unique_visits = progress_data.get('total_visits', 0)
    progress_by_municipality = progress_data.get('progress_by_municipality', [])

    # Calcular el número de municipios únicos visitados
    unique_municipalities_count = len(progress_by_municipality)

    # --- Evaluar qué logros ha ganado el usuario ---
    earned_achievements = []
    for achievement in ACHIEVEMENTS:
        criteria = achievement.get('criteria')
        if criteria:
            criteria_type = criteria.get('type')
            criteria_count = criteria.get('count')

            if criteria_type == 'total_unique_visits' and criteria_count is not None:
                if total_unique_visits >= criteria_count:
                    # Si cumple el criterio de total de visitas únicas
                    earned_achievements.append({
                        "id": achievement["id"],
                        "name": achievement["name"],
                        "description": achievement["description"],
                        # Podrías añadir una marca de tiempo de cuándo lo ganó si tuvieras una tabla de Logros Ganados
                        # "earned_at": "..."
                    })
            elif criteria_type == 'unique_municipalities' and criteria_count is not None:
                 if unique_municipalities_count >= criteria_count:
                     # Si cumple el criterio de número de municipios únicos
                     # Evitar duplicados si un logro depende de otro (ej: 3 municipios vs 1)
                     if not any(a.get('id') == achievement["id"] for a in earned_achievements):
                         earned_achievements.append({
                            "id": achievement["id"],
                            "name": achievement["name"],
                            "description": achievement["description"],
                         })


    print(f"DEBUG: Logros ganados encontrados para UserID {user_id}: {earned_achievements}")

    # Retornar la lista de logros ganados
    return jsonify(earned_achievements), 200



# --- Asegúrate de que esta parte está al final del archivo ---
if __name__ == '__main__':
    # ... (código para iniciar Flask) ...
    print("DEBUG: Database URL configurada:", models.DATABASE_URL)
    print("DEBUG: Radio de Check-in configurado:", CHECKIN_RADIUS_METERS, "metros.")
    print("Iniciando servidor Flask...")
    app.run(debug=True, port=5000)
    

# --- Ejecutar la Aplicación ---

#if __name__ == '__main__':
    # Asegúrate de que la DB y las tablas existen (puedes llamarlo aquí o desde un script separado)
    # from models import create_database_tables
    # create_database_tables()

    # Asegúrate de que la DB esté poblada (ejecuta populate_db.py antes)
    # print("Recordatorio: Asegúrate de haber ejecutado models.py y populate_db.py antes de iniciar el servidor.")

#    print("Iniciando servidor Flask...")
    # Puedes configurar el host y puerto si es necesario (ej: host='0.0.0.0' para acceso externo)
#    app.run(debug=True) # debug=True es útil durante el desarrollo