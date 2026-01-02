import sqlite3, pathlib

class AegisDB:
    def __init__(self):
        self.db_path = pathlib.Path(__file__).parent.resolve() / "aegis_vault.db"
        self._bootstrap()

    def _bootstrap(self):
        """Crea las tablas y carga valores por defecto si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de logs
            conn.execute("CREATE TABLE IF NOT EXISTS telemetry (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, temp REAL, mode TEXT)")
            # Tabla de configuración de perfiles
            conn.execute("CREATE TABLE IF NOT EXISTS telemetry_config (mode TEXT PRIMARY KEY, pstate INTEGER, vid INTEGER, freq INTEGER)")
            
            # Verificar si ya hay datos, si no, insertar defaults
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM telemetry_config")
            if cursor.fetchone()[0] == 0:
                defaults = [
                    ('office', 0, 16, 2500),
                    ('gaming', 1, 24, 2196),
                    ('eco', 2, 34, 1400),
                    ('emergency', 2, 45, 800)
                ]
                conn.executemany("INSERT INTO telemetry_config VALUES (?, ?, ?, ?)", defaults)

    def update_profile_logic(self, mode, new_pstate, new_vid, new_freq):
        """Actualiza los valores de un perfil específico."""
        query = "UPDATE telemetry_config SET pstate = ?, vid = ?, freq = ? WHERE mode = ?"
        with sqlite3.connect(self.db_path) as conn:
           conn.execute(query, (new_pstate, new_vid, new_freq, mode))
        print(f"✅ Perfil {mode.upper()} optimizado: VID {new_vid} | {new_freq}MHz")

    def get_profile(self, mode):
        """Recupera la configuración para aplicarla al CPU."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT pstate, vid, freq FROM telemetry_config WHERE mode = ?", (mode,))
            return cursor.fetchone()