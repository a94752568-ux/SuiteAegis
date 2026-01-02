import sys
import os
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QColor

class AegisMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # Timer para actualizar cada 1 segundo (como watch -n 1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def init_ui(self):
        # Window Flags: Sin bordes, siempre arriba, no aparece en la barra de tareas
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        layout = QVBoxLayout()
        self.label = QLabel("🛡️ AEGIS MONITOR\nIniciando...")
        
        # Estilo minimalista con bordes redondeados y transparencia
        self.label.setStyleSheet("""
            background-color: rgba(15, 15, 15, 200);
            color: #00FF41; /* Verde Matrix */
            border: 1px solid #00FF41;
            border-radius: 8px;
            padding: 10px;
        """)
        
        # Fuente monoespaciada para que los números no bailen
        self.label.setFont(QFont("Monospace", 10, QFont.Bold))
        layout.addWidget(self.label)
        self.setLayout(layout)
        
        # Posicionamiento: Esquina superior derecha
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - 220, 30)
        self.show()

    def get_cpu_mhz(self):
        """Replica exacta de grep MHz /proc/cpuinfo"""
        freqs = []
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "cpu MHz" in line:
                        mhz = float(line.split(":")[1].strip())
                        freqs.append(f"{mhz:.0f} MHz")
            return freqs
        except:
            return ["---"]

    def get_temp(self):
        """Lectura rápida de temperatura térmica"""
        try:
            # Buscamos el sensor k10temp (común en AMD A8)
            with open("/sys/class/hwmon/hwmon1/temp1_input", "r") as f:
                return f"{int(f.read()) / 1000:.1f}°C"
        except:
            return "??°C"

    def update_stats(self):
        freqs = self.get_cpu_mhz()
        temp = self.get_temp()
        
        text = f"🌡️ CPU: {temp}\n"
        text += "------------------\n"
        for i, f in enumerate(freqs):
            text += f"Core {i}: {f}\n"
        
        self.label.setText(text)
        self.adjustSize()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    monitor = AegisMonitor()
    sys.exit(app.exec())