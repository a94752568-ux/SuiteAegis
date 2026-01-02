import psutil, subprocess
class AegisWatcher:
    def __init__(self, core):
        self.core = core
        self.gaming_apps = {"steam", "retroarch", "wine", "mgba"}
        # Apps que activan el modo ECO (Navegadores, reproductores)
        self.eco_apps = {"chrome", "firefox", "vlc", "mpv", "brave"}
    def send_notification(self, mode_name, color="#00FF00"):
        """Envía una notificación visual al escritorio de Lubuntu."""
        msg = f"Modo {mode_name} Activado"
        subprocess.run(["notify-send", "-a", "Suite Aegis", "-i", "battery", "🛡️ Aegis System", msg])
    def analyze_and_run(self):
        temp = self.core.get_temp()
        current_procs = {p.info['name'].lower() for p in psutil.process_iter(['name'])}
        
        # Lógica de decisión
        if temp > 80:
            self.core.apply_profile(2, 40, 800)
            return "MODO EMERGENCIA"

        if not current_procs.isdisjoint(self.gaming_apps):
            self.core.apply_profile(1, 30, 1600)
            self.send_notification("GAMING")
            return "MODO GAMING"

        if not current_procs.isdisjoint(self.eco_apps):
            # 1.0GHz es suficiente para aceleración de video por hardware
            self.core.apply_profile(2, 38, 1000)
            self.send_notification("ECO FRIENDLY")
            return "MODO ECO FRIENDLY (Ahorro)"

        # Por defecto Office (Máximo Boost)
        self.core.apply_profile(0, 22, 2500)
        return "MODO OFFICE"
