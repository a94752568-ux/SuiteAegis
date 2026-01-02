# aegis_daemon.py
import time
from AegisCore import AegisCore
from AegisML import AegisWatcher

def run_service():
    core = AegisCore()
    watcher = AegisWatcher(core)
    while True:
        try:
            # Ejecuta la lógica de auto-ajuste cada 15 segundos
            watcher.analyze_and_run()
            time.sleep(15)
        except Exception as e:
            # Si hay un error, espera y reintenta para evitar crash
            time.sleep(5)
            continue

if __name__ == "__main__":
    run_service()