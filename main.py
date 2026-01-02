from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Button, Static, Log, Label
from AegisML import AegisWatcher
from AegisDB import AegisDB
from AegisBench import AegisBench
from AegisCore import AegisCore
from AegisLogger import AegisLogger
import threading
import os
import sys
import pathlib
import subprocess
import subprocess
class AegisApp(App):
    CSS_PATH = "aegis.css"
    BINDINGS = [
        ("g", "set_mode('gaming')", "Gaming"), 
        ("o", "set_mode('office')", "Office"), 
        ("q", "quit", "Salir")
    ]
    
    def __init__(self):
        super().__init__()
        self.max_temp_seen = 0
        self.pico_anunciado = False
        self.current_active_mode = "office"
        # Ruta absoluta para evitar problemas con sudo
        self.path_config = "/home/aegisproject/Desktop/SuiteAegis/last_mode.txt"

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_container"): 
            # PANEL IZQUIERDO (Botones con sus IDs originales)
            with Vertical(id="sidebar"): 
                yield Label("🎮 CONTROLES", id="sidebar_title")
                yield Button(" 📊 BENCHMARK", id="btn_bench")
                yield Button(" 🎮 GAMING", id="btn_gaming")
                yield Button("⚡ ECO", id="btn_eco")
                yield Button(" ⚡ OFFICE", id="btn_office")
            
            # PANEL DERECHO (Monitor de Sistema)
            with Vertical(id="monitor_area"):
                yield Label("📊 MONITOR DE SISTEMA", id="title_stats")
                
                # Tarjetas de temperatura
                with Horizontal(id="temp_cards"):
                    yield Static("🎮 CPU: -- °C", id="temp_pkg", classes="card")
                    yield Static("🎮 GPU: -- °C", id="temp_gpu", classes="card")
                
                # Cuadrícula de núcleos
                with Container(id="freq_grid"):
                    yield Static("C0: --", id="cpu0", classes="freq_tile")
                    yield Static("C1: --", id="cpu1", classes="freq_tile")
                    yield Static("C2: --", id="cpu2", classes="freq_tile")
                    yield Static("C3: --", id="cpu3", classes="freq_tile")
                
                yield Static("⚡ VID: --", id="vid_display")
                yield Static("🎮 GPU: -- MHz", id="gpu_freq")
                yield Label("⚙️ SERVICIO: --", id="service_status", classes="info_label")
                yield Static("⚙️ RAM: -- / -- GB", id="ram_stats", classes="card")
                yield Log(id="main_log")
                
        yield Footer()

    def save_last_mode(self, mode_id):
        """Escribe el modo en un archivo para que AegisBoot lo lea al reiniciar."""
        try:
            with open(self.path_config, "w") as f:
                f.write(mode_id)
            os.chmod(self.path_config, 0o666)
        except Exception as e:
            try:
                self.query_one("#main_log").write_line(f"⚠️ Error persistencia: {e}")
            except: pass

    def load_last_mode(self):
        """Lee el último modo guardado."""
        try:
            if os.path.exists(self.path_config):
                with open(self.path_config, "r") as f:
                    return f.read().strip()
        except: pass
        return "btn_office"

    def on_mount(self):
        # Inicialización de Aegis Components
        self.core = AegisCore()
        
        # Base de Datos con ruta absoluta
        db_path = pathlib.Path(__file__).parent.resolve() / "aegis_telemetry.db"
        self.db = AegisDB(str(db_path), self.core)
        
        # Logger e IA
        self.logger = AegisLogger()
        self.bench = AegisBench(self.core, self.db, self.query_one("#main_log").write_line)
        
        # Restaurar perfil previo
        last_mode = self.load_last_mode()
        log = self.query_one("#main_log")
        log.write_line(f"🔄 Restaurando último perfil: {last_mode}")
        
        # Validar y aplicar el modo recuperado
        valid_modes = ["btn_gaming", "btn_eco", "btn_office", "btn_bench"]
        if last_mode not in valid_modes:
            last_mode = "btn_office"
            
        # Disparamos el clic automáticamente para activar toda la lógica de MSR
        self.call_after_refresh(self.restore_previous_button, last_mode)
        
        # Intervalos (Dashboard cada 1s, ML cada 10s)
        self.set_interval(1, self.update_dashboard)
        self.set_interval(10, self.record_training_data)

    def restore_previous_button(self, mode_id):
        """Dispara el clic del botón guardado con seguridad."""
        try:
            btn = self.query_one(f"#{mode_id}", Button)
            self.post_message(Button.Pressed(btn))
        except Exception as e:
            self.query_one("#main_log").write_line(f"⚠️ No se pudo restaurar botón: {e}")

    def on_resize(self, event):
        """Ajusta el diseño cuando cambias el tamaño de la ventana."""
        try:
            container = self.query_one("#main_container")
            sidebar = self.query_one("#sidebar")
            if event.size.width < 80:
                container.styles.layout = "vertical"
                sidebar.styles.width = "100%"
                sidebar.styles.height = "auto"
            else:
                container.styles.layout = "horizontal"
                sidebar.styles.width = "25%"
                sidebar.styles.height = "100%"
        except: pass

    def update_dashboard(self):
        # 1. Extracción de Telemetría Real
        temps = self.core.get_detailed_temps()
        vid_real = self.core.get_current_vid()
        freqs = self.core.get_all_cpu_freqs()
        gpu_mhz = self.core.get_gpu_freq()
        ram = self.core.get_ram_usage()

        # 2. Lógica Térmica (Fallback Inteligente original)
        t_cpu = temps.get('package', 0)
        t_gpu = temps.get('gpu', 0)
        if t_gpu == 0: t_gpu = t_cpu 
        
        if t_cpu > self.max_temp_seen:
            self.max_temp_seen = t_cpu

        # 3. Actualización de UI
        self.query_one("#temp_pkg").update(f"⚡ CPU: {t_cpu:.1f} °C [MAX: {self.max_temp_seen:.1f}]")
        self.query_one("#temp_gpu").update(f"🎮 GPU: {t_gpu:.1f} °C")
        
        # Estética de RAM original
        ram_widget = self.query_one("#ram_stats")
        ram_widget.update(f"💾 RAM: {ram['used']:.1f} / {ram['total']:.1f} GB")
        if ram['free'] < 1.0:
            ram_widget.styles.color = "yellow"
        else:
            ram_widget.styles.color = "white"

        self.query_one("#vid_display").update(f"⚡ VID: {vid_real}")
        self.query_one("#gpu_freq").update(f"🎮 Reloj GPU: {gpu_mhz} MHz")

        # Cuadrícula de Núcleos (Dinámica)
        for i, f in enumerate(freqs):
            try:
                self.query_one(f"#cpu{i}").update(f"⚡ C{i}: {f:.0f} MHz")
            except: pass

        # 4. Alerta "Sin Miedo al Éxito" (Lógica original)
        log = self.query_one("#main_log")
        if t_cpu > 90:
            self.query_one("#temp_pkg").styles.color = "red"
            if not self.pico_anunciado:
                log.write_line("🔥 [ALERTA]: ¡90°C detectados! Manteniendo potencia...")
                log.write_line("🚀 [AEGIS]: ¡SIN MIEDO AL ÉXITO!")
                self.pico_anunciado = True
        elif t_cpu < 85:
            self.query_one("#temp_pkg").styles.color = "white"
            self.pico_anunciado = False

        # 5. Estado del Servicio Systemd
        try:
            check = subprocess.run(["systemctl", "is-enabled", "aegis-init.service"], 
                                   capture_output=True, text=True)
            status_widget = self.query_one("#service_status")
            if "enabled" in check.stdout:
                status_widget.update("⚙️ SERVICIO: [green]ACTIVO (AUTOMÁTICO)[/]")
            else:
                status_widget.update("⚙️ SERVICIO: [yellow]MANUAL[/]")
        except: pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        log_widget = self.query_one("#main_log")
        btn_id = event.button.id
        self.current_active_mode = btn_id 
        self.save_last_mode(btn_id)

        try:
            # 1. MODO BENCHMARK
            if btn_id == "btn_bench":
                log_widget.write_line("🚀 Lanzando estrés de núcleos (AegisBench)...")
                threading.Thread(target=self.bench.find_sweet_spot, daemon=True).start()

            # 2. MODO GAMING: El "Sweet Spot" Dinámico (1.8 - 2.0 GHz)
            elif btn_id == "btn_gaming":
                log_widget.write_line("⚔️ MODO GAMING: Rango dinámico 1.8GHz - 2.0GHz...")
                # 1. Gobernador que permite escala
                subprocess.run("echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
                # 2. Definir Rango (1.8 a 2.0)
                subprocess.run("echo 1800000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq", shell=True)
                subprocess.run("echo 2000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq", shell=True)
                # 3. Boost OFF para evitar saltos a 2.2GHz
                subprocess.run("echo 0 | sudo tee /sys/devices/system/cpu/cpufreq/boost", shell=True)
                # 4. Voltaje inicial estable (1.15V)
                subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003F09"], check=True)
                subprocess.Popen(["./dist/AegisMonitor"])
                log_widget.write_line("✅ Rango 1.8-2.0GHz Activo | Voltaje: 1.15V")

            # 3. MODO ECO: Ahorro Real (1.0 GHz)
            elif btn_id == "btn_eco":
                log_widget.write_line("🍃 MODO ECO: Capando a 1.0GHz (Ahorro total)...")
                subprocess.run("echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
                # Forzamos el máximo a 1.0GHz para que no intente subir al turbo
                subprocess.run("echo 1000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq", shell=True)
                subprocess.run("echo 1000000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq", shell=True)
                # Voltaje de ultra-bajo consumo (VID 0x4D)
                subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100004D09"], check=True)
                log_widget.write_line("✅ Sistema limitado a 1.0GHz para evitar calor.")

            # 4. MODO OFFICE: Tu configuración estable de 1.6 GHz
            elif btn_id == "btn_office":
                log_widget.write_line("💼 MODO OFFICE: 1.6GHz estables | VID: 1.25V")
                subprocess.run("echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
                subprocess.run("echo 1600000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq", shell=True)
                subprocess.run("echo 1600000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq", shell=True)
                # Voltaje equilibrado (0x30 = ~1.25V)
                subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003009"], check=True)
                log_widget.write_line("✅ Perfil 1.6GHz aplicado.")

        except Exception as e:
            log_widget.write_line(f"❌ Error aplicando perfil {btn_id}: {e}")

    def record_training_data(self):
        """Registra datos para la IA cada 10 segundos."""
        try:
            temps = self.core.get_detailed_temps()
            ram = self.core.get_ram_usage()
            freqs = self.core.get_all_cpu_freqs()
            avg_freq = sum(freqs) / len(freqs) if freqs else 0
            vid = self.core.get_current_vid()
            current_label = self.current_active_mode

            self.logger.log_session(
                temps.get('package', 0),
                temps.get('gpu', 0),
                ram['used'],
                avg_freq,
                vid,
                current_label
            )
        except: pass

if __name__ == "__main__":
    # Soporte para --apply (AegisBoot)
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        app = AegisApp()
        last_mode = app.load_last_mode()
        
        if last_mode == "btn_gaming":
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003F09"])
            subprocess.run("echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
        elif last_mode == "btn_office":
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003009"])
            subprocess.run("echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
            
        print(f"🛡️ Aegis: Perfil '{last_mode}' aplicado automáticamente.")
    else:
        AegisApp().run()