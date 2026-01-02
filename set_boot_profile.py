import subprocess
import os

# Configuración de voltajes (VID) para tu A8-7410
VOLTAGES = {
    "gaming": "0x14", # 1.200V aprox
    "office": "0x1E", # Voltaje intermedio
    "eco": "0x25"     # Voltaje bajo
}

def apply_undervolt(vid_hex):
    try:
        # Cargar módulo MSR por si acaso
        subprocess.run(["modprobe", "msr"], check=True)
        # Aplicar a todos los núcleos (P-state 0)
        # El registro 0xc0010064 es común en la arquitectura Beema
        cmd = f"wrmsr -a 0xc0010064 0x800000000000{vid_hex}68"
        os.system(cmd)
        print(f"✅ Undervolt aplicado con éxito: {vid_hex}")
    except Exception as e:
        print(f"❌ Error al aplicar undervolt: {e}")

def main():
    # Intentar leer el último modo guardado por la Suite Aegis
    # Si no existe, por defecto usa 'office' por seguridad
    mode_file = "/home/tu_usuario/Desktop/SuiteAegis/last_mode.txt" # AJUSTA TU RUTA
    
    mode = "office"
    if os.path.exists(mode_file):
        with open(mode_file, "r") as f:
            mode = f.read().strip()

    vid = VOLTAGES.get(mode, "0x1E")
    apply_undervolt(vid)

if __name__ == "__main__":
    main()
