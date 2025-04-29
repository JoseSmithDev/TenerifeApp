# poblacion_db/crear_niveles.py

# Importación ABSOLUTA de models.py
from models import Level # <-- Esta línea parece correcta si models.py está en la raíz

# No necesitas importar la sesión directamente aquí.
# La recibiremos como argumento en la función.
# from setup_db.session_setup import get_session # <-- Comentado, lo cual está bien si recibes la sesión


def populate_levels(session): # <-- La función correctamente recibe la sesión como argumento
    print("Creando niveles...")
    niveles = [
        Level(name="Novato Explorador", visits_required=0, image_url="url_nivel_1.png"),
        Level(name="Visitante Local", visits_required=3, image_url="url_nivel_2.png"),
        Level(name="Conquistador de Tenerife", visits_required=10, image_url="url_nivel_3.png"),
        # Añade aquí más niveles según tu plan
        Level(name="Leyenda de Tenerife", visits_required=20, image_url="url_nivel_4.png"),
    ]
    session.add_all(niveles) # <-- Usa la variable 'session' recibida. Esto es correcto aquí.
    # session.flush() # Opcional: Si necesitas los IDs de nivel inmediatamente después

    print(f"Añadidos {len(niveles)} niveles a la sesión.")

# Este script está diseñado para ser llamado por main_populate.py