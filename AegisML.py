import psutil, subprocess, os

class AegisWatcher:
    def __init__(self, core):
        self.core = core
        self.gaming_apps = {"steam", "retroarch", "wine", "mgba"}
        self.eco_apps = {"chrome", "firefox", "vlc", "mpv", "brave"}
        self.config_path = "/home/aegisproject/Desktop/SuiteAegis/last_mode.txt"

    def analyze_and_run(self):
        # --- PRIORIDAD 1: SEGURIDAD FÍSICA (Emergencia Térmica) ---
        # Esto se ejecuta SIEMPRE, incluso en modo manual.
        temp = self.core.get_temp()
        if temp > 88: # Umbral de pánico (ajustable)
            # Forzamos enfriamiento inmediato
            subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True, capture_output=True)
            # Perfil 2 (ECO/Mínimo) a 1000MHz
            self.core.apply_profile(2, 45, 1000) 
            return "🚨 EMERGENCIA: CPU a {temp}°C. Bajando potencia para enfriar."

        # --- PRIORIDAD 2: COMPROBAR MODO MANUAL ---
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, "r") as f:
                    last_mode = f.read().strip()
                
                if last_mode in ["btn_gaming", "btn_office", "btn_eco"]:
                    # Reforzamos Boost OFF por seguridad
                    subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True, capture_output=True)
                    return f"MODO MANUAL ({last_mode}) - Temp: {temp}°C OK"
        except:
            pass

        # 2. LÓGICA DE EMERGENCIA
        temp = self.core.get_temp()
        if temp > 85:
            subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True, capture_output=True)
            self.core.apply_profile(2, 40, 1000)
            return "MODO EMERGENCIA"

        # 3. LÓGICA AUTOMÁTICA (Solo si no hay archivo de persistencia)
        current_procs = {p.info['name'].lower() for p in psutil.process_iter(['name'])}
        
        # Desactivamos boost antes de cualquier cambio automático
        subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True, capture_output=True)

        if not current_procs.isdisjoint(self.gaming_apps):
            # Cambiado de 2200 a 2000 para evitar spikes
            self.core.apply_profile(1, 30, 2000)
            return "MODO GAMING AUTO"

        if not current_procs.isdisjoint(self.eco_apps):
            # Cambiado de 1600 a 1000 para que sea ECO real
            self.core.apply_profile(2, 38, 1000)
            return "MODO ECO AUTO"

        # Por defecto Office (Limitado a 1.6 para estabilidad)
        self.core.apply_profile(0, 22, 1600)
        return "MODO OFFICE AUTO"