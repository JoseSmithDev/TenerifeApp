# poblacion_db/populate_base_hierarchy.py

# Importaciones necesarias
# Importación ABSOLUTA de models.py
import models

# Importación correcta de session_setup (si la necesitas localmente para pruebas, si no, no)
# from .session_setup import get_session # o from poblacion_db.session_setup import get_session

# No importes la variable 'session' globalmente
# from session_setup import session # <-- ¡Incorrecto!

# La función debe recibir la sesión como argumento
def populate_base_hierarchy(session): # <-- Recibe la sesión
    print("Creando jerarquía base (País, Comunidades Autónomas)...")

    # --- Definir y crear los objetos base ---

    # 1. Crear País (España)
    espana_obj = models.Country(name="España") # Usamos models.Country porque importamos 'import models'
    session.add(espana_obj)
    # Flush para que España tenga ID antes de crear CCAA que la referencian
    session.flush()
    print("Añadido País 'España' y flusheado.")

    # 2. Crear Comunidades Autónomas
    # Si tu modelo AutonomousCommunity tiene un atributo 'country' que se enlaza a Country:
    canarias_obj = models.AutonomousCommunity(name="Canarias", country=espana_obj)
    valencia_ca_obj = models.AutonomousCommunity(name="Comunidad Valenciana", country=espana_obj) # <-- Nombre completo para Valencia CA

    session.add(canarias_obj)
    session.add(valencia_ca_obj)
    # Flush para que las CCAA tengan ID antes de que otros scripts las consulten o referencien
    session.flush()
    print("Añadidas CCAA 'Canarias' y 'Comunidad Valenciana' y flusheadas.")


    # No hagas session.commit() aquí. El commit final lo hace main_populate.py.


# Este script está diseñado para ser llamado por main_populate.py
# main_populate.py debe llamarlo PRIMERO.