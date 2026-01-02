import subprocess, os, pathlib, re
class AegisCore:
    def __init__(self):
        self.bin_path = pathlib.Path(__file__).parent.resolve() / "amdctl"
        self.temp_path = self._find_temp_sensor()
    
    def _find_temp_sensor(self):
        """Busca dinámicamente el sensor k10temp o similar."""
        for path in pathlib.Path("/sys/class/hwmon/").glob("hwmon*/name"):
            with open(path, "r") as f:
                if "k10temp" in f.read() or "fam15h" in f.read():
                    return path.parent / "temp1_input"
        return None

    def apply_profile(self, p_state, vid, freq_mhz):
        try:
            freq_str = f"{freq_mhz}MHz"
            for i in range(4):
                subprocess.run(["sudo", "cpufreq-set", "-c", str(i), "-g", "performance"], check=True)
            subprocess.run(["sudo", str(self.bin_path), f"-p{p_state}", f"-v{vid}"], check=True)
            for i in range(4):
                subprocess.run(["sudo", "cpufreq-set", "-c", str(i), "-u", freq_str], check=True)
            return True
        except: return False
        
    def get_temp(self):
        if self.temp_path and self.temp_path.exists():
            with open(self.temp_path, "r") as f:
                return int(f.read()) / 1000.0
        return 0.0
    
    def get_current_vid(self):
        """Traduce el valor hexadecimal del MSR a voltaje real."""
        try:
            import subprocess
            # Leemos el valor en hexadecimal
            res = subprocess.check_output(["sudo", "rdmsr", "-x", "0xC0010064"]).decode().strip()
            
            # En tu procesador (8000012100002c09), el VID está en la posición derecha
            # El valor '2c' (hex) es 44 (decimal)
            raw_hex = res[-4:-2] # Extrae los dígitos correctos
            vid_dec = int(raw_hex, 16)
            
            # Fórmula estándar AMD: 1.55V - (0.00625 * VID)
            voltage = 1.5500 - (0.00625 * vid_dec)
            return f"{voltage:.4f} V"
        except Exception as e:
            return "--- V"

    def stress_test(self, seconds=10):
        """Genera una carga sintética para probar la estabilidad del voltaje."""
        try:
            # Usamos 'openssl' porque viene en Lubuntu y estresa mucho los hilos del CPU
            subprocess.run(["timeout", str(seconds), "openssl", "speed", "-multi", "4"], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except:
            return False
    def get_all_cpu_freqs(self):
        """Lee la frecuencia actual de cada uno de los 4 núcleos."""
        freqs = []
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "cpu MHz" in line:
                        freqs.append(float(line.split(":")[1].strip()))
            return freqs
        except:
            return [0.0, 0.0, 0.0, 0.0]

    def get_gpu_freq(self):
        """Lee la frecuencia directamente desde el debugfs que confirmamos."""
        try:
            import subprocess
            path = "/sys/kernel/debug/dri/0000:00:01.0/amdgpu_pm_info"
            # Usamos sudo porque debugfs suele estar protegido
            output = subprocess.check_output(["sudo", "cat", path]).decode()
            
            for line in output.split('\n'):
                if "sclk:" in line:
                    # Dividimos por 'sclk:', tomamos la parte derecha, y luego el primer número
                    # 'power level 0    sclk: 30000 vddc: 4200' -> ' 30000 vddc' -> '30000'
                    raw_value = line.split("sclk:")[1].strip().split()[0]
                    mhz = int(raw_value) // 100 
                    return f"{mhz} MHz"
            return "--- MHz"
        except:
            return "OFF"

    def get_detailed_temps(self):
        """Busca cualquier dato térmico disponible para llenar el dashboard."""
        temps = {"package": 0, "gpu": 0}
        raw_values = []
        try:
            import subprocess
            # Usamos 'find' directamente en el sistema para no fallar con las rutas
            cmd = "find /sys/class/hwmon/hwmon*/ -name 'temp*_input'"
            paths = subprocess.check_output(cmd, shell=True).decode().splitlines()

            for p in paths:
                try:
                    with open(p, "r") as f:
                        val = int(f.read().strip()) / 1000
                        if 20 < val < 110: # Solo valores realistas
                            raw_values.append(val)
                except: continue

            if raw_values:
                # El valor más alto siempre será el CPU Package
                temps["package"] = max(raw_values)
                # El segundo valor (si existe) será la GPU. 
                # Si no hay segundo, usamos el mismo del CPU para que no se vea vacío.
                if len(raw_values) > 1:
                    # Buscamos un valor que sea distinto al máximo
                    others = [v for v in raw_values if v != temps["package"]]
                    temps["gpu"] = others[0] if others else temps["package"]
                else:
                    temps["gpu"] = temps["package"]

        except Exception as e:
            print(f"Error crítico en sensores: {e}")
            
        return temps
    
    def get_ram_usage(self):
        """Obtiene estadísticas de RAM en GB directamente del kernel."""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem_data = {}
            for line in lines:
                parts = line.split()
                # Guardamos en KB
                mem_data[parts[0].replace(':', '')] = int(parts[1])
            
            total = mem_data['MemTotal'] / (1024 * 1024) # Convertir a GB
            free = mem_data['MemAvailable'] / (1024 * 1024)
            used = total - free
            percent = (used / total) * 100
            
            return {
                "total": total,
                "used": used,
                "free": free,
                "percent": percent
            }
        except:
            return {"total": 0, "used": 0, "free": 0, "percent": 0}
    
    def force_max_performance(self):
        try:
            # La 'r' al principio evita el SyntaxWarning
            cmd = r"sudo sh -c 'for i in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do echo performance > $i; done'"
            subprocess.run(cmd, shell=True, check=True)
            return True
        except Exception as e:
            print(f"Error en force_max: {e}")
            return False
        
    def set_intelligent_eco(self):
        """Configura escala dinámica agresiva para máxima eficiencia."""
        try:
            import subprocess
            # 1. Usamos 'ondemand' para que la frecuencia sea dinámica (sube y baja según carga)
            # Si tu sistema usa intel_pstate/amd_pstate, se usa 'powersave' que es dinámico ahí.
            subprocess.run("echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor", shell=True)
            
            # 2. Seteamos un voltaje de reposo ultra bajo (VID 0x3F = ~1.15V)
            # Esto hará que incluso a 1.6GHz el calor generado sea mínimo
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003F09"])
            
            # 3. Ajustamos el 'up_threshold' para que el CPU solo suba de frecuencia 
            # cuando la carga sea realmente alta (>85%)
            subprocess.run("echo 85 | sudo tee /sys/devices/system/cpu/cpufreq/ondemand/up_threshold", shell=True)
            
            return True
        except:
            return False