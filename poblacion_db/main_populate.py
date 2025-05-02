# poblacion_db/main_populate.py (o setup_db/main_populate.py)

# Importación ABSOLUTA desde el paquete setup_db/ (o poblacion_db/)
# Asume que la carpeta 'TenerifeApp' está en el sys.path de Python.
# El nombre 'setup_db' debe coincidir con el nombre de la carpeta.
from poblacion_db.session_setup import SessionLocal  # O from poblacion_db.session_setup import get_session
from poblacion_db.populate_base_hierarchy import populate_base_hierarchy
# El resto de importaciones desde otros archivos dentro de setup_db/ también deben ser absolutas
from poblacion_db.crear_continente_pais_comunidad import populate_base_hierarchy
# ... y así con los demás scripts de crear_...
from poblacion_db.crear_provincias_islas_municipios import populate_provinces_islands_municipalities
from poblacion_db.crear_ubicaciones import populate_locations
from poblacion_db.crear_niveles import populate_levels
from poblacion_db.crear_logros import populate_achievements
from poblacion_db.populate_base_hierarchy import populate_base_hierarchy



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


    session = SessionLocal() # Obtiene la factory de sesión

    # Usar un bloque try...finally para asegurar que la sesión se cierre
    try:
        # --- Secuencia CORREGIDA de llamadas a scripts de poblamiento ---
        populate_base_hierarchy(session) # <-- ¡Llamar primero a la jerarquía base!
        populate_provinces_islands_municipalities(session) # Luego crear provincias/islas/municipios
        populate_locations(session) # Finalmente crear ubicaciones

        # Confirmar los cambios en la base de datos
        session.commit()
        print("Poblamiento completado. Cambios confirmados.")

    except Exception as e:
        # Si ocurre un error en cualquier script, revierte los cambios
        session.rollback()
        print(f"Error durante el poblamiento. Revirtiendo cambios: {e}")
        # Opcional: Imprimir la traza completa del error para debug
        # import traceback
        # traceback.print_exc()
        # Puedes re-lanzar la excepción si quieres que el programa termine con error
        # raise e
    finally:
        # Asegurarse de que la sesión se cierra
        session.close()
        print("Sesión de base de datos cerrada.")

if __name__ == "__main__":
    # Asegúrate de que las tablas ya existan antes de poblar
    # Puedes importar create_database_tables de models.py y llamarla aquí si quieres
    # from models import create_database_tables
    # create_database_tables()

    run_population()