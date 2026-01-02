import sqlite3, pathlib
class AegisDB:
    def __init__(self):
        self.db_path = pathlib.Path(__file__).parent.resolve() / "aegis_vault.db"
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS telemetry (timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, temp REAL, mode TEXT)")
        defaults = [
    ('gaming', 1, 30, 1600),
    ('office', 0, 22, 2500),
    ('eco', 2, 38, 1000), # Nuevo modo Eco: 1.0GHz con VID alto (voltaje bajo)
    ('emergency', 2, 40, 800)
]
        