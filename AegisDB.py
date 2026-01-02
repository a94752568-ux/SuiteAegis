import sqlite3, pathlib

class AegisDB:
    def __init__(self, db_path, core):
        self.db_path = db_path
        self.core = core
        self.max_temp_seen = 0
        self._bootstrap()

    def _bootstrap(self):
        """Crea las tablas y carga valores por defecto si no existen."""
        with sqlite3.connect(self.db_path) as conn:
            # Tabla de logs
            conn.execute("CREATE TABLE IF NOT EXISTS telemetry (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, temp REAL, mode TEXT, max_temp REAL)")
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
   
    def insert_reading(self, temp, mode, max_temp):
        """Inserta datos para el entrenamiento del ML."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO telemetry (temp, mode, max_temp) VALUES (?, ?, ?)",
                    (temp, mode, max_temp)
                )
        except Exception as e:
            print(f"Error DB: {e}")
    
    def record_training_data(self):
        temps = self.core.get_detailed_temps()
        t_cpu = temps.get('package', 0)
        current_label = getattr(self, "current_active_mode", "office")

        # Guardamos en la base de datos para el entrenamiento futuro
        # Asegúrate que AegisDB tenga el método insert_reading(temp, modo, max_temp)
        try:
            self.db.insert_reading(t_cpu, current_label, self.max_temp_seen)
        except:
            # Si tu DB aún no tiene max_temp, usamos el logger viejo por ahora
            ram = self.core.get_ram_usage()
            freqs = self.core.get_all_cpu_freqs()
            avg_freq = sum(freqs) / len(freqs) if freqs else 0
            self.logger.log_session(t_cpu, temps.get('gpu', 0), ram['used'], avg_freq, self.core.get_current_vid(), current_label)
