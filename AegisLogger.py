import csv
import time
from datetime import datetime
import os

class AegisLogger:
    def __init__(self, filename="aegis_training_data.csv"):
        self.filename = filename
        # Creamos el encabezado si el archivo no existe
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["timestamp", "cpu_temp", "gpu_temp", "ram_used", "cpu_freq_avg", "vid", "label"])

    def log_session(self, cpu_t, gpu_t, ram_u, freq_avg, vid, label):
        """Guarda una instantánea del estado del sistema."""
        try:
            with open(self.filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    cpu_t, gpu_t, ram_u, freq_avg, vid, label
                ])
        except Exception as e:
            print(f"Error en Logger: {e}")