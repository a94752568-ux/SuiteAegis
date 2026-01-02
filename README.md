# 🛡️ Suite Aegis: APU AMD Optimizer

**Suite Aegis** es una herramienta de gestión de hardware diseñada específicamente para exprimir el rendimiento de la APU **AMD A8-7410 (Beema)** bajo Linux, garantizando temperaturas seguras mediante Undervolt y optimización dinámica de recursos.

> "Diseñado para dominar en Albion Online, construido para la eficiencia cotidiana."

---

## 🚀 Características Principales

* **🎮 Modo Gaming:** Bloquea el voltaje a `1.2000V` (vía `msr-tools`) y libera la memoria caché de Linux para eliminar tirones (*stuttering*).
* **🌱 Modo Eco & Office:** Gestión inteligente de frecuencias para prolongar la vida útil del hardware.
* **🧠 AegisLogger (ML Ready):** Sistema de recolección de datos en tiempo real (temperaturas, RAM, carga) para el futuro entrenamiento de modelos de Inteligencia Artificial.
* **📊 Dashboard en Terminal:** Interfaz visual moderna construida con `Textual` y `Rich`.
* **⚙️ Systemd Integration:** Carga automática del último perfil configurado al arrancar el sistema operativo.

## 🛠️ Requisitos Técnicos

* **SO:** Linux (XFCE/Ubuntu recomendado).
* **Hardware:** AMD A8-7410 (Familia 16h, Modelo 30h).
* **Dependencias:**
    * `msr-tools` (para control de registros de CPU).
    * `Python 3.10+`.
    * `Textual`, `Rich` (interfaz de usuario).

## 📦 Instalación y Uso

1. **Clonar el repositorio:**
   ```bash
   git clone [https://github.com/a94752568-ux/SuiteAegis.git](https://github.com/a94752568-ux/SuiteAegis.git)
   cd SuiteAegis

Configurar el entorno:

Bash

python3 -m venv venv
source venv/bin/activate
pip install textual rich pandas scikit-learn
Ejecutar Suite Aegis: (Requiere permisos de superusuario para modificar registros MSR)

Bash

sudo ./venv/bin/python main.py
🛡️ Seguridad y Licencia
Este software interactúa con los voltajes del procesador. Se distribuye bajo la Licencia MIT. Úsalo bajo tu propio riesgo (aunque en esta arquitectura, bajar a 1.2000V es térmicamente preventivo y estable).

Desarrollado por a94752568-ux — Sin Miedo al Éxito.
