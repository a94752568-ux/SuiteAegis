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

class AegisApp(App):
    CSS_PATH = "aegis.css"
    BINDINGS = [("g", "set_mode('gaming')", "Gaming"), ("o", "set_mode('office')", "Office"), ("q", "quit", "Salir")]
    
    def __init__(self):
        super().__init__()
        self.max_temp_seen = 0  # <--- Inicializamos el récord
        self.pico_anunciado = False

    def compose(self) -> ComposeResult:
        yield Header()
        # Este es el contenedor PADRE que on_resize y el CSS necesitan
        with Container(id="main_container"): 
            
            # PANEL IZQUIERDO (Botones)
            with Vertical(id="sidebar"): 
                yield Label("🎮 CONTROLES", id="sidebar_title")
                yield Button("📊 BENCHMARK", id="btn_bench")
                yield Button("🎮 GAMING", id="btn_gaming")
                yield Button("🌱 ECO", id="btn_eco")
                yield Button("📁 OFFICE", id="btn_office")
            
            # PANEL DERECHO (Sensores)
            with Vertical(id="monitor_area"):
                yield Label("📊 MONITOR DE SISTEMA", id="title_stats")
                
                # Tarjetas de temperatura
                with Horizontal(id="temp_cards"):
                    yield Static("🌡️ CPU: -- °C", id="temp_pkg", classes="card")
                    yield Static("🔥 GPU: -- °C", id="temp_gpu", classes="card")
                
                # Cuadrícula de núcleos
                with Container(id="freq_grid"):
                    yield Static("C0: --", id="cpu0", classes="freq_tile")
                    yield Static("C1: --", id="cpu1", classes="freq_tile")
                    yield Static("C2: --", id="cpu2", classes="freq_tile")
                    yield Static("C3: --", id="cpu3", classes="freq_tile")
                
                yield Static("⚡ VID: --", id="vid_display")
                yield Static("🎮 GPU: -- MHz", id="gpu_freq")
                yield Label("⚙️ SERVICIO: --", id="service_status", classes="info_label")
                yield Static("🧠 RAM: -- / -- GB", id="ram_stats", classes="card")
                yield Log(id="main_log")
                
        yield Footer()

    def save_last_mode(self, mode_id):
        """Guarda el modo y fuerza permisos 666 para que el servicio lo lea."""
        try:
            path = "/home/aegisproject/Desktop/SuiteAegis/last_mode.txt"
            with open(path, "w") as f:
                f.write(mode_id)
            # Forzamos permisos para que el sistema (root) y tú puedan usarlo
            import os
            os.chmod(path, 0o666)
        except Exception as e:
            self.query_one("#main_log").write_line(f"⚠️ Error al guardar modo: {e}")
   
    def on_mount(self):
        self.core, self.db = AegisCore(), AegisDB()
        self.bench = AegisBench(self.core, self.db, self.query_one("#main_log").write_line)
        self.set_interval(1, self.update_dashboard)
        self.logger = AegisLogger()
        self.set_interval(10, self.record_training_data)
        # --- LÓGICA DE PERSISTENCIA ---
        last_mode = self.load_last_mode()
        self.query_one("#main_log").write_line(f"🔄 Restaurando último perfil: {last_mode}")
        
        # Simulamos el clic del botón guardado
        # Esto disparará toda la lógica de MSR y Performance automáticamente
        self.post_message(Button.Pressed(self.query_one(f"#{last_mode}")))
        path = "/home/aegisproject/Desktop/SuiteAegis/last_mode.txt"
        if not os.path.exists(path):
            self.save_last_mode("btn_office")
        
        # Ahora cargamos el modo con total seguridad
        last_mode = self.load_last_mode()
    
    def on_resize(self, event):
        """Esta función ajusta el diseño cuando cambias el tamaño de la ventana"""
        try:
            # Intentamos buscar los elementos
            # Asegúrate que en tu método compose usaste id="main_container"
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
        except Exception:
            # Si aún no existen los IDs, no hacemos nada y el programa sigue
            pass

    def update_dashboard(self):
    
        # 1. Extracción de Telemetría
        temps = self.core.get_detailed_temps()
        vid_real = self.core.get_current_vid()
        freqs = self.core.get_all_cpu_freqs()
        gpu_mhz = self.core.get_gpu_freq()
        ram = self.core.get_ram_usage()

        # 2. Lógica Térmica (Fallback Inteligente)
        t_cpu = temps.get('package', 0)
        t_gpu = temps.get('gpu', 0)
        if t_gpu == 0: t_gpu = t_cpu  # Sin miedo al éxito

        # 3. Actualización de Texto en Pantalla
        self.query_one("#temp_pkg").update(f"🔥 CPU: {t_cpu:.1f} °C")
        self.query_one("#temp_gpu").update(f"🎮 GPU: {t_gpu:.1f} °C")
        self.query_one("#ram_stats").update(f"💾 RAM: {ram['used']:.1f} / {ram['total']:.1f} GB")
        self.query_one("#vid_display").update(f"⚡ VID: {vid_real}")
        self.query_one("#gpu_freq").update(f"🎮 Reloj GPU: {gpu_mhz}")
        ram_widget = self.query_one("#ram_stats")
        ram_widget.update(f"🧠 RAM: {ram['used']:.1f} / {ram['total']:.1f} GB")
        # Estética de alerta: Si queda menos de 1GB libre, avisamos en amarillo
        if ram['free'] < 1.0:
            ram_widget.styles.color = "yellow"
        else:
            ram_widget.styles.color = "white"
        # 4. Cuadrícula de Núcleos
        for i, f in enumerate(freqs):
            try:
                self.query_one(f"#cpu{i}").update(f"⚡ C{i}: {f:.0f} MHz")
            except: pass

        # 5. Alerta "Sin Miedo al Éxito"
        log = self.query_one("#main_log")
        if t_cpu > 90:
            self.query_one("#temp_pkg").styles.color = "red"
            if not getattr(self, "pico_anunciado", False):
                log.write_line("🔥 [ALERTA]: ¡90°C detectados! Manteniendo potencia...")
                log.write_line("🚀 [AEGIS]: ¡SIN MIEDO AL ÉXITO!")
                self.pico_anunciado = True
        elif t_cpu < 85:
            self.query_one("#temp_pkg").styles.color = "white"
            self.pico_anunciado = False
        try:
            import subprocess
            # Consultamos a systemd si el servicio existe y está habilitado
            check = subprocess.run(["systemctl", "is-enabled", "aegis-init.service"], 
                                   capture_output=True, text=True)
            status_widget = self.query_one("#service_status")
            
            if "enabled" in check.stdout:
                status_widget.update("⚙️ SERVICIO: [green]ACTIVO (AUTOMÁTICO)[/]")
            else:
                status_widget.update("⚙️ SERVICIO: [yellow]MANUAL[/]")
        except:
            pass
    def record_training_data(self):
     # Extraemos los datos actuales que ya calculamos en update_dashboard
     temps = self.core.get_detailed_temps()
     ram = self.core.get_ram_usage()
     freqs = self.core.get_all_cpu_freqs()
     avg_freq = sum(freqs) / len(freqs) if freqs else 0
     vid = self.core.get_current_vid()

     # El 'label' es el modo que TÚ tienes activo ahora (Gaming, Eco, etc.)
     # Esto es lo que la IA usará para aprender qué modo prefieres en qué estado.
     current_label = getattr(self, "current_active_mode", "office")

     self.logger.log_session(
         temps.get('package', 0),
         temps.get('gpu', 0),
         ram['used'],
         avg_freq,
         vid,
         current_label
     )
    def auto_monitor_ml(self):
        # Esta función puede correr en un intervalo más largo (ej. 10 seg)
        res = self.watcher.analyze_and_run()
        self.query_one("#main_log").write_line(f"[ML] {res}")

    def update_stats(self):
        # Actualiza la UI con datos frescos
        temp = self.core.get_temp()
        vid = self.core.get_current_vid()
        
        self.query_one("#temp_display").update(f"🌡️ Temp: {temp:.1f} °C")
        self.query_one("#vid_display").update(f"⚡ VID Actual: {vid}")
        
        # Ejecuta el monitor de ML (cada 10 seg aprox usando un contador interno o manteniendo el otro intervalo)
        res = self.watcher.analyze_and_run()
        if res: self.query_one("#main_log").write_line(f"[ML] {res}")

    def auto_monitor(self):
        res = self.watcher.analyze_and_run()
        self.query_one("#main_log").write_line(f"[ML] {res} | Temp: {self.core.get_temp()}°C")

    def action_set_mode(self, mode):
        if mode == "gaming": self.core.apply_profile(1, 30, 1600)
        else: self.core.apply_profile(0, 22, 2500)
        self.query_one("#main_log").write_line(f"🚀 Manual: {mode.upper()}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        import subprocess  # Aseguramos que esté disponible
        log_widget = self.query_one("#main_log")
        btn_id = event.button.id
         
        # 1. MODO BENCHMARK
        if btn_id == "btn_bench":
            log_widget.write_line("🚀 Lanzando estrés de núcleos (AegisBench)...")
            threading.Thread(target=self.bench.run_full_test, daemon=True).start()

        # 2. MODO GAMING (Cambiado a elif para mantener la cadena)
        elif btn_id == "btn_gaming":
            log_widget.write_line("⚔️ PREPARANDO CAMPO DE BATALLA...")
            try:
                # 1. Limpieza de Memoria RAM (Caché de Linux)
                # El valor '3' libera PageCache, dentries e inodes.
                subprocess.run("sync; echo 3 | sudo tee /proc/sys/vm/drop_caches", shell=True, check=True)
                log_widget.write_line("🧹 RAM purgada y lista para Albion.")

                # 2. Undervolt y Performance
                subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003809"], check=True)
                self.core.force_max_performance()
                
                log_widget.write_line("🚀 Frecuencias al MAX | Voltaje 1.2000V")
                log_widget.write_line("🛡️  ¡SIN MIEDO AL ÉXITO, MAURICIO!")
                
                self.save_last_mode("btn_gaming")
            except Exception as e:
                log_widget.write_line(f"❌ Fallo en despliegue: {e}")

        # 3. MODO ECO
        elif btn_id == "btn_eco":
            log_widget.write_line("🍃 MODO INTELIGENTE: Maximizando eficiencia...")
            try:
                if self.core.set_intelligent_eco():
                    log_widget.write_line("✅ Escala dinámica activa + Undervolt 1.15V")
                    log_widget.write_line("❄️ El ventilador debería reducir su velocidad pronto.")
            except Exception as e:
                log_widget.write_line(f"❌ Error ECO: {e}")

        # 4. MODO OFFICE
        elif btn_id == "btn_office":
            log_widget.write_line("💼 MODO OFFICE: Buscando el equilibrio térmico...")
            try:
                # Voltaje equilibrado 1.2500V (VID 0x30)
                subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003009"], check=True)
                subprocess.run("echo powersave | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True, check=True)
                log_widget.write_line("✅ Perfil equilibrado aplicado.")
            except Exception as e:
                log_widget.write_line(f"❌ Error en Office: {e}")
    def save_last_mode(self, mode_id):
        """Guarda el modo y asegura permisos universales."""
        path = "last_mode.txt" # Se crea en la misma carpeta del script
        try:
            with open(path, "w") as f:
                f.write(mode_id)
            os.chmod(path, 0o666) # Permisos de lectura/escritura para todos
        except Exception as e:
            self.query_one("#main_log").write_line(f"⚠️ Error persistencia: {e}")

    def load_last_mode(self):
        """Lee el último modo guardado."""
        if os.path.exists("last_mode.txt"):
            with open("last_mode.txt", "r") as f:
                return f.read().strip()
        return "btn_office" # Modo por defecto
if __name__ == "__main__":
    # Si ejecutamos 'python main.py --apply', solo aplica el último perfil y sale
    if len(sys.argv) > 1 and sys.argv[1] == "--apply":
        app = AegisApp()
        core = AegisCore()
        last_mode = app.load_last_mode()
        
        # Diccionario de comandos rápidos según el modo guardado
        if last_mode == "btn_gaming":
            import subprocess
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003809"])
            core.force_max_performance()
        elif last_mode == "btn_office":
            core.set_intelligent_eco() # O el comando que prefieras para office
            
        print(f"🛡️ Aegis: Perfil '{last_mode}' aplicado automáticamente.")
    else:
        # Si no hay argumentos, abre la interfaz normal para jugar
        AegisApp().run()
