# models.py

# Importar los tipos de datos de columnas y la base declarativa
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime


# Define la URL de conexión a tu base de datos.
# Para SQLite, es simplemente 'sqlite:///nombre_del_archivo.db'
DATABASE_URL = "sqlite:///./tnfbase.db" # Nombre del archivo de la base de datos SQLite


engine = create_engine(DATABASE_URL)


Base = declarative_base()


class Continent(Base):
    __tablename__ = 'continents'
    continent_id = Column(Integer, primary_key=True, index=True) 
    name = Column(String, unique=True, index=True, nullable=False)


    countries = relationship("Country", backref="continent")

class Country(Base):
    __tablename__ = 'countries'
    country_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    continent_id = Column(Integer, ForeignKey('continents.continent_id'), nullable=True) 

    autonomous_communities = relationship("AutonomousCommunity", backref="country")

class AutonomousCommunity(Base):
    __tablename__ = 'autonomous_communities'

    ac_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    country_id = Column(Integer, ForeignKey('countries.country_id'), nullable=False)


    provinces = relationship("Province", backref="autonomous_community")

class Province(Base):
    __tablename__ = 'provinces'

    province_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    ac_id = Column(Integer, ForeignKey('autonomous_communities.ac_id'), nullable=False)


    islands = relationship("Island", backref="province")

class Island(Base):
    __tablename__ = 'islands'
    island_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    province_id = Column(Integer, ForeignKey('provinces.province_id'), nullable=False)


class Municipality(Base):
    __tablename__ = 'municipalities'

    municipality_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False) 
    #island_id = Column(Integer, ForeignKey('islands.island_id'), nullable=False) 
    province_id = Column(Integer, ForeignKey('provinces.province_id'), nullable=False) 
    province = relationship("Province", backref="municipalities") 

    # Relación: Un municipio tiene muchas ubicaciones
    locations = relationship("Location", backref="municipality")



class Location(Base):
    __tablename__ = 'locations' # Nombre de la tabla en la base de datos

    # Columnas definidas en el esquema
    location_id = Column(Integer, primary_key=True, index=True) # Clave primaria auto-incremental
    name = Column(String, nullable=False) # Nombre del lugar
    description = Column(Text) # Descripción, usamos Text por si es largo
    latitude = Column(Float, nullable=False) # Coordenada de latitud
    longitude = Column(Float, nullable=False) # Coordenada de longitud
    main_image_url = Column(String, nullable=True) # O False si todas las ubicaciones tendrán una imagen principal
    unlocked_content_url = Column(String, nullable=True) # Este ya lo tenías
    difficulty = Column(String) # Dificultad (ej: 'Fácil', 'Media')
    is_natural = Column(Boolean, default=False, nullable=False) # Indica si es natural (True/False)
    best_season = Column(String) # Mejor época para visitar (ej: 'Verano', 'Todo el Año')
    best_time_of_day = Column(String) # Mejor momento del día (ej: 'Mañana', 'Atardecer')
    
    # Clave foránea que enlaza con la tabla 'municipalities'
    municipality_id = Column(Integer, ForeignKey('municipalities.municipality_id'), nullable=False)
    visits = relationship("UserLocationVisit", back_populates="location")

class User(Base):
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True) # Hacerlo unique es buena práctica, pero podría ser opcional
    password_hash = Column(String, nullable=False)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False) # Usar UTC es buena práctica
    total_visits = Column(Integer, default=0, nullable=False)
    visits = relationship("UserLocationVisit", back_populates="user")

    
class Review(Base):
    __tablename__ = 'reviews'

    review_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.location_id'), nullable=False)
    rating = Column(Integer, nullable=False) # Validar que esté entre 1 y 5 en la aplicación
    comment = Column(Text)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class Level(Base):
    __tablename__ = 'levels'

    level_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    visits_required = Column(Integer, unique=True, nullable=False)
    image_url = Column(String)

class Achievement(Base):
    __tablename__ = 'achievements'

    achievement_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(String, nullable=False) # Ej: 'total_count', 'municipality_complete'
    target_entity_type = Column(String) # Ej: 'municipality', 'island', 'total'
    target_entity_id = Column(Integer) # ID de la entidad objetivo si aplica (municipality_id, island_id, etc.)
    target_value = Column(Integer) # Valor numérico si aplica (ej: 5 para total_count)
    unlocked_image_url = Column(String)

class UserAchievement(Base):
    __tablename__ = 'user_achievements'

    user_achievement_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.achievement_id'), nullable=False)
    unlocked_timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class UserLocationVisit(Base):
    __tablename__ = 'user_location_visits'

    visit_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id')) # Clave foránea a la tabla users
    location_id = Column(Integer, ForeignKey('locations.location_id')) # Clave foránea a la tabla locations
    visit_timestamp = Column(DateTime, default=datetime.datetime.utcnow) # Fecha y hora de la visita

    # Opcional: Asegurarse de que un usuario no pueda tener múltiples visitas exactas en el mismo instante (no estrictamente necesario si cada llamada crea un nuevo registro válido)
    __table_args__ = (UniqueConstraint('user_id', 'location_id', 'visit_timestamp', name='_user_location_timestamp_uc'),)

    # Definir relaciones (opcional pero útil)
    user = relationship("User", back_populates="visits") # Asumiendo que tienes 'visits' en el modelo User
    location = relationship("Location", back_populates="visits") # Asumiendo que tienes 'visits' en el modelo Location

def create_database_tables():
    print("Creando tablas de la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas (o ya existentes).")

# Para ejecutar la creación de tablas (puedes hacerlo desde otro script o aquí para probar)
if __name__ == "__main__":
    create_database_tables()
    print(f"Base de datos SQLite creada en {DATABASE_URL}")
