# aegis_daemon.py
import time
import os
import sys
import subprocess
from AegisCore import AegisCore
from AegisML import AegisWatcher

os.environ["QT_QPA_PLATFORM"] = "offscreen"
os.environ["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/dev/null"
os.environ["DISPLAY"] = ":0"

def apply_fixed_profile(mode):
    """Aplica la configuración exacta para asegurar la persistencia."""
    try:
        if mode == "btn_gaming":
            # 1. Usamos 'ondemand' o 'schedutil' para permitir variabilidad
            # Si 'ondemand' no está disponible, usa 'powersave' (que en AMD escala bien)
            subprocess.run("echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True, capture_output=True)
            
            # 2. Definimos el RANGO dinámico
            subprocess.run("echo 1800000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq", shell=True, capture_output=True)
            subprocess.run("echo 2000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq", shell=True, capture_output=True)
            
            # 3. Mantener el Boost apagado para que no ignore el techo de 2.0
            subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True, capture_output=True)
            
            # 4. Aplicar el voltaje (MSR)
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003F09"], capture_output=True)
            
        elif mode == "btn_office":
            # 1.6 GHz Fijo
            subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True)
            subprocess.run("echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
            subprocess.run("echo 1600000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq", shell=True)
            subprocess.run("echo 1600000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq", shell=True)
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003009"])

        elif mode == "btn_eco":
            # 1.0 GHz Fijo
            subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True)
            subprocess.run("echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
            subprocess.run("echo 1000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq", shell=True)
            subprocess.run("echo 1000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq", shell=True)
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100004D09"])
    except Exception as e:
        print(f"Error en persistencia: {e}")

def run_service():
    core = AegisCore()
    watcher = AegisWatcher(core)
    path_config = "/home/aegisproject/Desktop/SuiteAegis/last_mode.txt"
    
    print("🛡️ Aegis Daemon: Iniciando protección en segundo plano con persistencia...")
    
    while True:
        try:
            # 1. Leer el modo deseado por el usuario
            current_mode = "btn_office"
            if os.path.exists(path_config):
                with open(path_config, "r") as f:
                    current_mode = f.read().strip()
            
            # 2. Reforzar el perfil seleccionado
            apply_fixed_profile(current_mode)
            
            # 3. El Watcher sigue analizando por seguridad (ej. Emergencia Térmica)
            watcher.analyze_and_run()
            
            time.sleep(5)
        except Exception as e:
            with open("daemon_errors.log", "a") as f:
                f.write(f"{time.ctime()}: {str(e)}\n")
            time.sleep(10)

if __name__ == "__main__":
    run_service()