# backend/app.py

from flask import Flask, jsonify, request
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, distinct, func, or_
from sqlalchemy.orm import sessionmaker, relationship, joinedload, declarative_base
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
import os
import sys
import datetime # Necesario para UserLocationVisit si usa default=datetime.utcnow

# --- Configuración del Path para Imports ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# --- Imports de tu Proyecto ---
# Asumimos que models.py está en el directorio padre (TenerifeApp/)
# y poblacion_db es un paquete en el directorio padre.
try:
    import models # Importa el módulo models para acceder a DATABASE_URL, Base y clases de modelos
    from models import (
        Location, Municipality, User, UserLocationVisit,
        Achievement, UserAchievement, engine as models_engine # Importar engine desde models
    )
    # Intenta importar SessionLocal de poblacion_db.session_setup
    # Se asume que session_setup.py define SessionLocal usando el engine de models.py
    from poblacion_db.session_setup import SessionLocal
    print("DEBUG: SessionLocal y engine importados desde poblacion_db.session_setup y models.py")
    engine = models_engine # Usar el engine de models.py
except ImportError as e:
    print(f"ADVERTENCIA: No se pudo importar de poblacion_db.session_setup o models ({e}). Definiendo localmente (esto es un fallback).")
    print("             Asegúrate de que poblacion_db/session_setup.py y models.py existan y estén configurados correctamente.")
    
    # Fallback si los imports fallan (requiere que models.py al menos defina Base y DATABASE_URL)
    if hasattr(models, 'DATABASE_URL') and hasattr(models, 'Base'):
        engine = create_engine(models.DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = models.Base # Usar Base de models
        # Aquí tendrías que re-definir tus clases de modelo si no se pudieron importar desde models
        # Esto indica un problema de estructura o de ejecución del script que necesita revisarse.
        # Por simplicidad, este fallback asume que las clases de modelo se importaron bien desde el 'import models'
        # pero si no es así, el código fallará más adelante.
        Location = models.Location
        Municipality = models.Municipality
        User = models.User
        UserLocationVisit = models.UserLocationVisit
        Achievement = models.Achievement
        UserAchievement = models.UserAchievement
    else:
        raise ImportError("No se pudo encontrar DATABASE_URL o Base en models.py, ni importar SessionLocal/engine. Revisa la configuración.")


# --- Importaciones de Terceros ---
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.distance import geodesic

# --- Constantes y Configuraciones Globales ---
CHECKIN_RADIUS_METERS = 4000

ACHIEVEMENTS_DEFINITIONS = [
    {"id": 1, "name": "Novato Explorador", "description": "Visita tu primera ubicación única.", "criteria": {"type": "total_unique_visits", "count": 1}},
    {"id": 2, "name": "Explorador Entusiasta", "description": "Visita 5 ubicaciones únicas.", "criteria": {"type": "total_unique_visits", "count": 5}},
    {"id": 3, "name": "Conquistador de Municipios (1)", "description": "Visita ubicaciones en 1 municipio diferente.", "criteria": {"type": "unique_municipalities", "count": 1}},
    {"id": 4, "name": "Conquistador de Municipios (3)", "description": "Visita ubicaciones en 3 municipios diferentes.", "criteria": {"type": "unique_municipalities", "count": 3}},
]

app = Flask(__name__)

# --- Context Manager para Sesiones de Base de Datos ---
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        # No hacemos commit aquí; se hará en cada ruta si es necesario
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

# --- Funciones de Ayuda ---
def _get_user_stats(db_session, user_id):
    unique_visits_count = db_session.query(func.count(distinct(UserLocationVisit.location_id)))\
        .filter(UserLocationVisit.user_id == user_id)\
        .scalar() or 0

    unique_municipalities_count = db_session.query(func.count(distinct(Location.municipality_id)))\
        .join(UserLocationVisit, Location.location_id == UserLocationVisit.location_id)\
        .filter(UserLocationVisit.user_id == user_id)\
        .scalar() or 0
    
    return {
        "unique_visits_count": unique_visits_count,
        "unique_municipalities_count": unique_municipalities_count
    }

def _check_and_award_achievements(db_session, user_id, user_stats):
    earned_achievement_ids_from_db = {ua.achievement_id for ua in db_session.query(UserAchievement.achievement_id).filter_by(user_id=user_id).all()}
    newly_unlocked_achievements_info = []

    for achievement_def in ACHIEVEMENTS_DEFINITIONS:
        achievement_id_template = achievement_def['id']
        achievement_in_db = db_session.query(Achievement).filter_by(achievement_id=achievement_id_template).first()
        
        if not achievement_in_db:
            print(f"ADVERTENCIA: Logro ID {achievement_id_template} no encontrado en DB. Saltando.")
            continue
        if achievement_in_db.achievement_id in earned_achievement_ids_from_db:
            continue

        criteria = achievement_def.get('criteria', {})
        criteria_type = criteria.get('type')
        required_count = criteria.get('count')
        is_unlocked = False

        if criteria_type == 'total_unique_visits' and required_count is not None:
            if user_stats['unique_visits_count'] >= required_count:
                is_unlocked = True
        elif criteria_type == 'unique_municipalities' and required_count is not None:
            if user_stats['unique_municipalities_count'] >= required_count:
                is_unlocked = True
        
        if is_unlocked:
            new_user_achievement = UserAchievement(user_id=user_id, achievement_id=achievement_in_db.achievement_id)
            db_session.add(new_user_achievement)
            newly_unlocked_achievements_info.append({
                "id": achievement_in_db.achievement_id,
                "name": achievement_in_db.name,
                "description": achievement_in_db.description
            })
    return newly_unlocked_achievements_info

# --- Endpoints de la API ---

@app.route('/locations', methods=['GET'])
def get_locations_list_route():
    municipality_id = request.args.get('municipality_id', type=int)
    search_query = request.args.get('q', type=str)
    
    with get_db() as db:
        query = db.query(Location, Municipality)\
                  .join(Municipality, Location.municipality_id == Municipality.municipality_id)

        if municipality_id is not None:
            query = query.filter(Location.municipality_id == municipality_id)
        
        if search_query and search_query.strip():
            search_term = f"%{search_query.strip()}%"
            query = query.filter(
                or_( # Usar or_ importado de sqlalchemy
                    Location.name.ilike(search_term),
                    Location.description.ilike(search_term)
                )
            )
        
        results = query.order_by(Location.name).all() # Añadir un orden
        locations_list = [{
            "location_id": loc.location_id, "name": loc.name, "description": loc.description,
            "latitude": loc.latitude, "longitude": loc.longitude,
            "municipality_id": loc.municipality_id, "municipality_name": muni.name,
            "difficulty": loc.difficulty, "is_natural": loc.is_natural,
            "best_season": loc.best_season, "best_time_of_day": loc.best_time_of_day,
            "main_image_url": loc.main_image_url
        } for loc, muni in results]
        return jsonify(locations_list), 200

@app.route('/locations/<int:location_id>', methods=['GET'])
def get_location_details_route(location_id):
    user_id = request.args.get('user_id', type=int)
    with get_db() as db:
        location_result = db.query(Location, Municipality)\
                            .join(Municipality, Location.municipality_id == Municipality.municipality_id)\
                            .filter(Location.location_id == location_id)\
                            .first()
        if not location_result:
            return jsonify({"message": "Ubicación no encontrada"}), 404
        
        location_obj, muni_obj = location_result
        has_visited = False
        if user_id is not None:
            visit = db.query(UserLocationVisit).filter_by(user_id=user_id, location_id=location_id).first()
            has_visited = visit is not None

        return jsonify({
            "location_id": location_obj.location_id, "name": location_obj.name,
            "description": location_obj.description, "latitude": location_obj.latitude, "longitude": location_obj.longitude,
            "municipality_id": location_obj.municipality_id, "municipality_name": muni_obj.name,
            "difficulty": location_obj.difficulty, "is_natural": location_obj.is_natural,
            "best_season": location_obj.best_season, "best_time_of_day": location_obj.best_time_of_day,
            "main_image_url": location_obj.main_image_url,
            "unlocked_content_url": location_obj.unlocked_content_url if has_visited else None
        }), 200

@app.route('/checkin', methods=['POST'])
def checkin_location_route():
    data = request.get_json()
    if not data:
        return jsonify({"message": "Petición sin datos JSON."}), 400

    try:
        user_lat = float(data['latitude'])
        user_lng = float(data['longitude'])
        user_id = int(data['user_id'])
        location_id = int(data['location_id'])
    except (KeyError, ValueError, TypeError):
        return jsonify({"message": "Datos inválidos o faltantes."}), 400

    with get_db() as db:
        location = db.query(Location).filter(Location.location_id == location_id).first()
        if not location: return jsonify({"message": f"Ubicación ID {location_id} no encontrada."}), 404
        
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user: return jsonify({"message": f"Usuario ID {user_id} no encontrado."}), 404

        user_coords = (user_lat, user_lng)
        location_coords = (location.latitude, location.longitude)
        distance_in_meters = geodesic(user_coords, location_coords).meters

        if distance_in_meters <= CHECKIN_RADIUS_METERS:
            existing_visit = db.query(UserLocationVisit).filter_by(user_id=user_id, location_id=location_id).first()
            new_visit_created_this_time = False
            
            if not existing_visit:
                new_visit = UserLocationVisit(user_id=user_id, location_id=location_id)
                db.add(new_visit)
                new_visit_created_this_time = True
            
            user_stats = _get_user_stats(db, user_id) # Stats ANTES de commit si es nueva visita, o actuales si ya existía
            if new_visit_created_this_time : # Si es una visita nueva, las stats para logros deben reflejarla
                 user_stats["unique_visits_count"] +=1 # Asumimos que esta visita es a una loc nueva para el conteo de esta sesión
                 # La de municipios es más compleja de actualizar incrementalmente aquí, _get_user_stats ya la recalculará bien después del commit.
                 # Para una lógica precisa de logros, es mejor calcular stats *después* del add y *antes* del commit, o después del commit y re-query.
                 # Por simplicidad, recalculamos stats después de añadir para que _check_and_award_achievements tenga la info más fresca posible
                 # si la visita es nueva.
                 # Si la visita es nueva, una forma de obtener stats actualizadas para logros es:
                 # db.flush() # Para que la nueva visita esté en la sesión para las queries de stats
                 # user_stats = _get_user_stats(db, user_id)
                 # Esto es complejo. Es más simple: _get_user_stats se llama, y si es una nueva visita, el conteo será +1.

            current_stats_for_achievements = _get_user_stats(db, user_id) # Stats actuales
            if new_visit_created_this_time and not db.query(UserLocationVisit).filter(UserLocationVisit.user_id == user_id, UserLocationVisit.location_id == location_id).count() > 1:
                # Si es una visita realmente nueva a esta locación para este usuario
                # (esta comprobación es un poco redundante con existing_visit, pero asegura para el conteo de unique_visits)
                # En realidad, _get_user_stats ya debería dar los conteos correctos si la visita se añade a la sesión antes de llamar a _get_user_stats
                pass


            newly_unlocked = _check_and_award_achievements(db, user_id, current_stats_for_achievements) # Usar current_stats
            
            try:
                db.commit()
                return jsonify({
                    "message": f"¡Check-in en {location.name} procesado!",
                    "visit_recorded": True,
                    "new_visit_created": new_visit_created_this_time,
                    "unlocked_content_url": location.unlocked_content_url,
                    "unlocked_achievements": newly_unlocked,
                    "distancia_metros": round(distance_in_meters, 0)
                }), 200
            except Exception as e_commit:
                db.rollback()
                return jsonify({"message": "Error interno al guardar el check-in."}), 500
        else:
            return jsonify({
                "message": f"Estás demasiado lejos de {location.name} ({distance_in_meters:.0f}m). Debes estar a menos de {CHECKIN_RADIUS_METERS}m.",
                "visit_recorded": False,
                "distancia_metros": round(distance_in_meters, 0)
            }), 200

@app.route('/register', methods=['POST'])
def register_user_route():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Nombre de usuario y contraseña son requeridos."}), 400

    username = data['username'].strip()
    password = data['password']
    if not username or not password:
        return jsonify({"message": "Nombre de usuario y contraseña no pueden estar vacíos."}), 400
        
    with get_db() as db:
        if db.query(User).filter(User.username == username).first():
            return jsonify({"message": "El nombre de usuario ya existe."}), 409

        new_user = User(username=username, password_hash=generate_password_hash(password))
        db.add(new_user)
        try:
            db.commit()
            db.refresh(new_user) 
            return jsonify({"message": "Usuario registrado exitosamente.", "user_id": new_user.user_id}), 201
        except Exception as e_commit:
            db.rollback()
            return jsonify({"message": "Error interno al registrar usuario."}), 500

@app.route('/login', methods=['POST'])
def login_user_route():
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({"message": "Nombre de usuario y contraseña son requeridos."}), 400
    
    username = data['username']
    password = data['password']
    with get_db() as db:
        user = db.query(User).filter(User.username == username).first()
        if user and check_password_hash(user.password_hash, password):
            return jsonify({"message": "Inicio de sesión exitoso.", "user_id": user.user_id}), 200
        else:
            return jsonify({"message": "Nombre de usuario o contraseña incorrectos."}), 401

@app.route('/users/<int:user_id>/visits', methods=['GET'])
def get_user_visits_and_progress_route(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"message": f"Usuario con ID {user_id} no encontrado."}), 404

        # 1. Obtener los IDs de las ubicaciones únicas visitadas por el usuario
        distinct_location_ids_tuples = db.query(distinct(UserLocationVisit.location_id))\
                                          .filter(UserLocationVisit.user_id == user_id)\
                                          .all()
        distinct_location_ids_list = [item[0] for item in distinct_location_ids_tuples]

        visited_locations_objects = []
        if distinct_location_ids_list:
            # 2. Consultar objetos Location y cargar ansiosamente su relación 'municipality'
            # Asegúrate de que la relación 'municipality' está definida en tu modelo Location
            # y que puedes acceder a ella como location_obj.municipality.
            # Si no, usa un join explícito: db.query(Location, Municipality).join(Municipality, ...)
            visited_locations_objects = db.query(Location)\
                                           .options(joinedload(Location.municipality))\
                                           .filter(Location.location_id.in_(distinct_location_ids_list))\
                                           .order_by(Location.name)\
                                           .all()
        
        visited_locations_list = []
        for loc_obj in visited_locations_objects:
            muni_name = loc_obj.municipality.name if loc_obj.municipality else "Desconocido"
            visited_locations_list.append({
                "location_id": loc_obj.location_id, "name": loc_obj.name, "description": loc_obj.description,
                "latitude": loc_obj.latitude, "longitude": loc_obj.longitude, "difficulty": loc_obj.difficulty,
                "is_natural": loc_obj.is_natural, "best_season": loc_obj.best_season, 
                "best_time_of_day": loc_obj.best_time_of_day, "main_image_url": loc_obj.main_image_url,
                "municipality_name": muni_name,
            })
        
        user_stats = _get_user_stats(db, user_id) # Para el conteo total y de municipios
        total_available_locations = db.query(func.count(Location.location_id)).scalar() or 0
        
        progress_by_municipality_query = db.query(Municipality.name, func.count(distinct(UserLocationVisit.location_id)))\
            .join(Location, Municipality.municipality_id == Location.municipality_id)\
            .join(UserLocationVisit, Location.location_id == UserLocationVisit.location_id)\
            .filter(UserLocationVisit.user_id == user_id)\
            .group_by(Municipality.name)\
            .all()
        
        progress_by_municipality_list = [
            {"municipality_name": name, "visited_count": count} for name, count in progress_by_municipality_query
        ]

        return jsonify({
            "total_visits": user_stats["unique_visits_count"], 
            "visited_locations": visited_locations_list, 
            "total_locations": total_available_locations,
            "progress_by_municipality": progress_by_municipality_list
        }), 200

@app.route('/users/<int:user_id>/achievements', methods=['GET'])
def get_user_achievements_earned_route(user_id):
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"message": f"Usuario con ID {user_id} no encontrado."}), 404

        earned_db_achievements = db.query(Achievement)\
            .join(UserAchievement, Achievement.achievement_id == UserAchievement.achievement_id)\
            .filter(UserAchievement.user_id == user_id)\
            .all()
        
        achievements_list = [{
            "id": ach.achievement_id, "name": ach.name, "description": ach.description
        } for ach in earned_db_achievements]
        return jsonify(achievements_list), 200

# --- Ejecutar la Aplicación ---
if __name__ == '__main__':
    print("DEBUG: Iniciando la aplicación Flask...")
    # Comprobación más segura para DATABASE_URL
    db_url_from_models = getattr(models, 'DATABASE_URL', None)
    if db_url_from_models:
         print("DEBUG: Database URL configurada:", db_url_from_models)
    else:
         print("ADVERTENCIA: DATABASE_URL no parece estar configurada o accesible vía models.py.")

    print("DEBUG: Radio de Check-in configurado:", CHECKIN_RADIUS_METERS, "metros.")
    
    # create_all se maneja mejor con scripts de inicialización/migraciones.
    # Si es necesario para desarrollo rápido y sabes que las tablas son seguras de crear:
    # Base.metadata.create_all(bind=engine)
    # print("DEBUG: Base.metadata.create_all(bind=engine) ejecutado (tablas creadas si no existían).")
    
    app.run(debug=True, host='0.0.0.0', port=5000)