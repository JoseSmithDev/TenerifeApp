# poblacion_db/main_populate.py (o setup_db/main_populate.py)

# Importación ABSOLUTA desde el paquete setup_db/ (o poblacion_db/)
# Asume que la carpeta 'TenerifeApp' está en el sys.path de Python.
# El nombre 'setup_db' debe coincidir con el nombre de la carpeta.
from poblacion_db.session_setup import get_session # O from poblacion_db.session_setup import get_session

# El resto de importaciones desde otros archivos dentro de setup_db/ también deben ser absolutas
from poblacion_db.crear_continente_pais_comunidad import populate_base_hierarchy
# ... y así con los demás scripts de crear_...
from poblacion_db.crear_provincias_islas_municipios import populate_provinces_islands_municipalities
from poblacion_db.crear_ubicaciones import populate_locations
from poblacion_db.crear_niveles import populate_levels
from poblacion_db.crear_logros import populate_achievements

# Importaciones desde models.py también son absolutas desde la raíz
from models import Base, engine # Si decides llamarla aquí

def run_population():
     # --- PASOS PARA BORRAR Y RECREAR TABLAS ---
    print("Borrando todas las tablas existentes...")
    Base.metadata.drop_all(bind=engine) # <-- Esta línea borra todas las tablas
    print("Tablas borradas.")

    print("Creando todas las tablas...")
    Base.metadata.create_all(bind=engine) # <-- Esta línea crea todas las tablas de nuevo
    print("Tablas creadas.")


    session = get_session()
    print("Iniciando proceso de poblamiento completo...")
    try:
        # Llama a las funciones en el orden correcto de dependencia
        populate_base_hierarchy(session)
        # Necesitarás IDs de los pasos anteriores para el siguiente.
        # Una forma es pasar los objetos creados, otra es consultarlos.
        # Si haces session.flush() después de cada paso de creación de jerarquía,
        # los objetos creados tendrán ID antes del commit final.

        # Ejemplo asumiendo que populate_base_hierarchy hizo flush o puedes consultar
        # espana_obj = session.query(Country).filter_by(name="España").first()
        # canarias_obj = session.query(AutonomousCommunity).filter_by(name="Canarias").first()
        # ... y pasarlos o usarlos en la siguiente función ...

        populate_provinces_islands_municipalities(session)
        populate_locations(session) # populate_locations necesitará IDs de municipios
        populate_levels(session)
        populate_achievements(session) # populate_achievements necesitará IDs de jerarquía/ubicaciones

        # Confirma todos los cambios al final
        session.commit()
        print("Proceso de poblamiento completado exitosamente.")

    except Exception as e:
        session.rollback() # Revierte todos los cambios si algo falla
        print(f"Error durante el poblamiento. Revirtiendo cambios: {e}")
    finally:
        session.close()
        print("Sesión de base de datos cerrada.")

if __name__ == "__main__":
    # Asegúrate de que las tablas ya existan antes de poblar
    # Puedes importar create_database_tables de models.py y llamarla aquí si quieres
    # from models import create_database_tables
    # create_database_tables()

    run_population()