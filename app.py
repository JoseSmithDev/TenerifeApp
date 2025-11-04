# app.py
"""
API Flask para la aplicación TenerifeApp.
Maneja usuarios, ubicaciones, check-ins y logros.
"""

import logging
import os
import sys
from contextlib import contextmanager
from flask import Flask, jsonify, request
from sqlalchemy import distinct, func, or_
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.distance import geodesic

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuración del Path para Imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Imports del proyecto
try:
    import models
    from models import (
        Location, Municipality, User, UserLocationVisit,
        Achievement, UserAchievement, engine as models_engine
    )
    from poblacion_db.session_setup import SessionLocal
    engine = models_engine
    logger.info("Módulos importados correctamente desde models.py y poblacion_db.session_setup")
except ImportError as e:
    logger.error(f"Error al importar módulos: {e}")
    raise ImportError(
        "No se pudieron importar los módulos necesarios. "
        "Asegúrate de que models.py y poblacion_db/session_setup.py existan."
    )

# Constantes y Configuraciones Globales
CHECKIN_RADIUS_METERS = 4000

ACHIEVEMENTS_DEFINITIONS = [
    {
        "id": 1,
        "name": "Novato Explorador",
        "description": "Visita tu primera ubicación única.",
        "criteria": {"type": "total_unique_visits", "count": 1}
    },
    {
        "id": 2,
        "name": "Explorador Entusiasta",
        "description": "Visita 5 ubicaciones únicas.",
        "criteria": {"type": "total_unique_visits", "count": 5}
    },
    {
        "id": 3,
        "name": "Conquistador de Municipios (1)",
        "description": "Visita ubicaciones en 1 municipio diferente.",
        "criteria": {"type": "unique_municipalities", "count": 1}
    },
    {
        "id": 4,
        "name": "Conquistador de Municipios (3)",
        "description": "Visita ubicaciones en 3 municipios diferentes.",
        "criteria": {"type": "unique_municipalities", "count": 3}
    },
]

app = Flask(__name__)


# Context Manager para Sesiones de Base de Datos
@contextmanager
def get_db():
    """Context manager para sesiones de base de datos."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Funciones de Ayuda
def _validate_coordinates(latitude, longitude):
    """Valida que las coordenadas estén en rangos válidos."""
    if not (-90 <= latitude <= 90):
        raise ValueError("Latitud debe estar entre -90 y 90")
    if not (-180 <= longitude <= 180):
        raise ValueError("Longitud debe estar entre -180 y 180")
    return True


def _get_user_stats(db_session, user_id):
    """
    Obtiene estadísticas del usuario.
    
    Returns:
        dict: Diccionario con unique_visits_count y unique_municipalities_count
    """
    unique_visits_count = db_session.query(
        func.count(distinct(UserLocationVisit.location_id))
    ).filter(UserLocationVisit.user_id == user_id).scalar() or 0

    unique_municipalities_count = db_session.query(
        func.count(distinct(Location.municipality_id))
    ).join(
        UserLocationVisit, Location.location_id == UserLocationVisit.location_id
    ).filter(UserLocationVisit.user_id == user_id).scalar() or 0

    return {
        "unique_visits_count": unique_visits_count,
        "unique_municipalities_count": unique_municipalities_count
    }


def _check_and_award_achievements(db_session, user_id, user_stats):
    """
    Verifica y otorga logros al usuario basándose en sus estadísticas.
    
    Returns:
        list: Lista de logros recién desbloqueados
    """
    earned_achievement_ids = {
        ua.achievement_id
        for ua in db_session.query(UserAchievement.achievement_id)
        .filter_by(user_id=user_id).all()
    }
    newly_unlocked_achievements = []

    for achievement_def in ACHIEVEMENTS_DEFINITIONS:
        achievement_id = achievement_def['id']
        achievement_in_db = db_session.query(Achievement).filter_by(
            achievement_id=achievement_id
        ).first()

        if not achievement_in_db:
            logger.warning(f"Logro ID {achievement_id} no encontrado en DB. Saltando.")
            continue

        if achievement_in_db.achievement_id in earned_achievement_ids:
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
            new_user_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_in_db.achievement_id
            )
            db_session.add(new_user_achievement)
            newly_unlocked_achievements.append({
                "id": achievement_in_db.achievement_id,
                "name": achievement_in_db.name,
                "description": achievement_in_db.description
            })

    return newly_unlocked_achievements


# Endpoints de la API

@app.route('/locations', methods=['GET'])
def get_locations_list_route():
    """Obtiene lista de ubicaciones con filtros opcionales."""
    municipality_id = request.args.get('municipality_id', type=int)
    search_query = request.args.get('q', type=str)

    with get_db() as db:
        query = db.query(Location, Municipality).join(
            Municipality, Location.municipality_id == Municipality.municipality_id
        )

        if municipality_id is not None:
            query = query.filter(Location.municipality_id == municipality_id)

        if search_query and search_query.strip():
            search_term = f"%{search_query.strip()}%"
            query = query.filter(
                or_(
                    Location.name.ilike(search_term),
                    Location.description.ilike(search_term)
                )
            )

        results = query.order_by(Location.name).all()
        locations_list = [{
            "location_id": loc.location_id,
            "name": loc.name,
            "description": loc.description,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "municipality_id": loc.municipality_id,
            "municipality_name": muni.name,
            "difficulty": loc.difficulty,
            "is_natural": loc.is_natural,
            "best_season": loc.best_season,
            "best_time_of_day": loc.best_time_of_day,
            "main_image_url": loc.main_image_url
        } for loc, muni in results]

        return jsonify(locations_list), 200


@app.route('/locations/<int:location_id>', methods=['GET'])
def get_location_details_route(location_id):
    """Obtiene detalles de una ubicación específica."""
    user_id = request.args.get('user_id', type=int)

    with get_db() as db:
        location_result = db.query(Location, Municipality).join(
            Municipality, Location.municipality_id == Municipality.municipality_id
        ).filter(Location.location_id == location_id).first()

        if not location_result:
            return jsonify({"message": "Ubicación no encontrada"}), 404

        location_obj, muni_obj = location_result
        has_visited = False

        if user_id is not None:
            visit = db.query(UserLocationVisit).filter_by(
                user_id=user_id,
                location_id=location_id
            ).first()
            has_visited = visit is not None

        return jsonify({
            "location_id": location_obj.location_id,
            "name": location_obj.name,
            "description": location_obj.description,
            "latitude": location_obj.latitude,
            "longitude": location_obj.longitude,
            "municipality_id": location_obj.municipality_id,
            "municipality_name": muni_obj.name,
            "difficulty": location_obj.difficulty,
            "is_natural": location_obj.is_natural,
            "best_season": location_obj.best_season,
            "best_time_of_day": location_obj.best_time_of_day,
            "main_image_url": location_obj.main_image_url,
            "unlocked_content_url": (
                location_obj.unlocked_content_url if has_visited else None
            )
        }), 200


@app.route('/checkin', methods=['POST'])
def checkin_location_route():
    """Procesa un check-in de un usuario en una ubicación."""
    data = request.get_json()
    if not data:
        return jsonify({"message": "Petición sin datos JSON."}), 400

    try:
        user_lat = float(data['latitude'])
        user_lng = float(data['longitude'])
        user_id = int(data['user_id'])
        location_id = int(data['location_id'])

        # Validar coordenadas
        _validate_coordinates(user_lat, user_lng)
    except KeyError as e:
        return jsonify({"message": f"Campo faltante: {e}"}), 400
    except ValueError as e:
        return jsonify({"message": f"Datos inválidos: {e}"}), 400
    except TypeError:
        return jsonify({"message": "Tipos de datos inválidos."}), 400

    with get_db() as db:
        location = db.query(Location).filter(
            Location.location_id == location_id
        ).first()
        if not location:
            return jsonify({
                "message": f"Ubicación ID {location_id} no encontrada."
            }), 404

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({
                "message": f"Usuario ID {user_id} no encontrado."
            }), 404

        user_coords = (user_lat, user_lng)
        location_coords = (location.latitude, location.longitude)
        distance_in_meters = geodesic(user_coords, location_coords).meters

        if distance_in_meters > CHECKIN_RADIUS_METERS:
            return jsonify({
                "message": (
                    f"Estás demasiado lejos de {location.name} "
                    f"({distance_in_meters:.0f}m). "
                    f"Debes estar a menos de {CHECKIN_RADIUS_METERS}m."
                ),
                "visit_recorded": False,
                "distancia_metros": round(distance_in_meters, 0)
            }), 200

        # Verificar si ya existe la visita
        existing_visit = db.query(UserLocationVisit).filter_by(
            user_id=user_id,
            location_id=location_id
        ).first()

        new_visit_created = False
        if not existing_visit:
            new_visit = UserLocationVisit(
                user_id=user_id,
                location_id=location_id
            )
            db.add(new_visit)
            db.flush()  # Flush para que la visita esté disponible para queries
            new_visit_created = True
            logger.info(
                f"Usuario {user_id} realizó check-in en ubicación {location_id}"
            )

        # Recalcular estadísticas después del flush
        user_stats = _get_user_stats(db, user_id)
        newly_unlocked = _check_and_award_achievements(db, user_id, user_stats)

        try:
            db.commit()
            return jsonify({
                "message": f"¡Check-in en {location.name} procesado!",
                "visit_recorded": True,
                "new_visit_created": new_visit_created,
                "unlocked_content_url": location.unlocked_content_url,
                "unlocked_achievements": newly_unlocked,
                "distancia_metros": round(distance_in_meters, 0)
            }), 200
        except Exception as e:
            db.rollback()
            logger.error(f"Error al guardar check-in: {e}")
            return jsonify({
                "message": "Error interno al guardar el check-in."
            }), 500


@app.route('/register', methods=['POST'])
def register_user_route():
    """Registra un nuevo usuario."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            "message": "Nombre de usuario y contraseña son requeridos."
        }), 400

    username = data['username'].strip()
    password = data['password']

    if not username or not password:
        return jsonify({
            "message": "Nombre de usuario y contraseña no pueden estar vacíos."
        }), 400

    with get_db() as db:
        if db.query(User).filter(User.username == username).first():
            return jsonify({
                "message": "El nombre de usuario ya existe."
            }), 409

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password)
        )
        db.add(new_user)

        try:
            db.commit()
            db.refresh(new_user)
            logger.info(f"Usuario registrado: {username}")
            return jsonify({
                "message": "Usuario registrado exitosamente.",
                "user_id": new_user.user_id
            }), 201
        except Exception as e:
            db.rollback()
            logger.error(f"Error al registrar usuario: {e}")
            return jsonify({
                "message": "Error interno al registrar usuario."
            }), 500


@app.route('/login', methods=['POST'])
def login_user_route():
    """Autentica un usuario."""
    data = request.get_json()
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            "message": "Nombre de usuario y contraseña son requeridos."
        }), 400

    username = data['username']
    password = data['password']

    with get_db() as db:
        user = db.query(User).filter(User.username == username).first()

        if user and check_password_hash(user.password_hash, password):
            logger.info(f"Usuario autenticado: {username}")
            return jsonify({
                "message": "Inicio de sesión exitoso.",
                "user_id": user.user_id
            }), 200
        else:
            logger.warning(f"Intento de login fallido para usuario: {username}")
            return jsonify({
                "message": "Nombre de usuario o contraseña incorrectos."
            }), 401


@app.route('/users/<int:user_id>/visits', methods=['GET'])
def get_user_visits_and_progress_route(user_id):
    """Obtiene las visitas y progreso de un usuario."""
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({
                "message": f"Usuario con ID {user_id} no encontrado."
            }), 404

        distinct_location_ids = [
            item[0]
            for item in db.query(distinct(UserLocationVisit.location_id))
            .filter(UserLocationVisit.user_id == user_id).all()
        ]

        visited_locations_objects = []
        if distinct_location_ids:
            visited_locations_objects = db.query(Location).options(
                joinedload(Location.municipality)
            ).filter(
                Location.location_id.in_(distinct_location_ids)
            ).order_by(Location.name).all()

        visited_locations_list = []
        for loc_obj in visited_locations_objects:
            muni_name = (
                loc_obj.municipality.name
                if loc_obj.municipality else "Desconocido"
            )
            visited_locations_list.append({
                "location_id": loc_obj.location_id,
                "name": loc_obj.name,
                "description": loc_obj.description,
                "latitude": loc_obj.latitude,
                "longitude": loc_obj.longitude,
                "difficulty": loc_obj.difficulty,
                "is_natural": loc_obj.is_natural,
                "best_season": loc_obj.best_season,
                "best_time_of_day": loc_obj.best_time_of_day,
                "main_image_url": loc_obj.main_image_url,
                "municipality_name": muni_name,
            })

        user_stats = _get_user_stats(db, user_id)
        total_available_locations = db.query(
            func.count(Location.location_id)
        ).scalar() or 0

        progress_by_municipality_query = db.query(
            Municipality.name,
            func.count(distinct(UserLocationVisit.location_id))
        ).join(
            Location, Municipality.municipality_id == Location.municipality_id
        ).join(
            UserLocationVisit,
            Location.location_id == UserLocationVisit.location_id
        ).filter(
            UserLocationVisit.user_id == user_id
        ).group_by(Municipality.name).all()

        progress_by_municipality_list = [
            {"municipality_name": name, "visited_count": count}
            for name, count in progress_by_municipality_query
        ]

        return jsonify({
            "total_visits": user_stats["unique_visits_count"],
            "visited_locations": visited_locations_list,
            "total_locations": total_available_locations,
            "progress_by_municipality": progress_by_municipality_list
        }), 200


@app.route('/users/<int:user_id>/achievements', methods=['GET'])
def get_user_achievements_earned_route(user_id):
    """Obtiene los logros desbloqueados por un usuario."""
    with get_db() as db:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({
                "message": f"Usuario con ID {user_id} no encontrado."
            }), 404

        earned_db_achievements = db.query(Achievement).join(
            UserAchievement,
            Achievement.achievement_id == UserAchievement.achievement_id
        ).filter(UserAchievement.user_id == user_id).all()

        achievements_list = [{
            "id": ach.achievement_id,
            "name": ach.name,
            "description": ach.description
        } for ach in earned_db_achievements]

        return jsonify(achievements_list), 200


# Ejecutar la Aplicación
if __name__ == '__main__':
    logger.info("Iniciando la aplicación Flask...")
    db_url = getattr(models, 'DATABASE_URL', None)
    if db_url:
        logger.info(f"Database URL configurada: {db_url}")
    else:
        logger.warning("DATABASE_URL no configurada en models.py")

    logger.info(f"Radio de Check-in configurado: {CHECKIN_RADIUS_METERS} metros")
    app.run(debug=True, host='0.0.0.0', port=5000)
