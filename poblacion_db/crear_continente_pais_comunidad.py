# poblacion_db/crear_continente_pais_comunidad.py

# Importa los modelos necesarios
from models import Continent, Country, AutonomousCommunity

def populate_base_hierarchy(session): # Recibe la sesión
    print("Creando jerarquía base: Continente, País, CCAA...")

    europa = Continent(name="Europa")
    espana = Country(name="España", continent=europa)
    canarias = AutonomousCommunity(name="Canarias", country=espana)
    valencia = AutonomousCommunity(name="Valencia", country=espana)

    session.add_all([europa, espana, canarias, valencia])

    # --- Añade esta línea ---
    session.flush() # Fuerza la inserción para que los objetos tengan IDs y sean consultables

    print("Jerarquía base añadida a la sesión y flusheada.")

# Este script está diseñado para ser llamado por main_populate.py