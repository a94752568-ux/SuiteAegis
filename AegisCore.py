import subprocess, os, pathlib, re

class AegisCore:
    def __init__(self):
        # Localiza el binario amdctl en la misma carpeta
        self.bin_path = pathlib.Path(__file__).parent.resolve() / "amdctl"
        self.temp_path = self._find_temp_sensor()
    
    def _find_temp_sensor(self):
        """Busca dinámicamente el sensor k10temp o similar."""
        for path in pathlib.Path("/sys/class/hwmon/").glob("hwmon*/name"):
            try:
                with open(path, "r") as f:
                    content = f.read()
                    if "k10temp" in content or "fam15h" in content:
                        return path.parent / "temp1_input"
            except:
                continue
        return None

    def apply_profile(self, p_state, vid, freq_mhz):
        """
        Aplica el perfil de energía equilibrando CPU y GPU.
        Evita el estancamiento en 1.0 GHz.
        """
        try:
            # Forzar
            os.system("echo 1 | sudo tee /sys/module/processor/parameters/ignore_ppc")

            # 1. GPU: Usamos 'auto' para que el firmware permita subir la frecuencia del CPU.
            # El modo 'high' forzado es lo que asfixia al procesador a 1.0 GHz.
            gpu_level = "/sys/class/drm/card0/device/power_dpm_force_performance_level"
            if os.path.exists(gpu_level):
                os.system("echo auto | sudo tee " + gpu_level)

            # 2. Hardware: Aplicar P-State y Voltaje (Tu binario amdctl)
            subprocess.run(["sudo", str(self.bin_path), f"-p{p_state}", f"-v{vid}"], check=True)

            # 3. Gobernador: Forzar modo performance nativo
            os.system("echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")

            # 4. CPU Frecuencia: Destrabar el límite de 1.0 GHz
            target_khz = str(freq_mhz * 1000)
            # Reseteamos el techo al máximo teórico (2.5GHz) para despertar al driver
            os.system("echo 2500000 | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq")
            # Fijamos el rango exacto solicitado
            os.system(f"echo {target_khz} | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_min_freq")
            os.system(f"echo {target_khz} | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_max_freq")
        
            return True
        except Exception as e:
            print(f"Error en apply_profile: {e}")
            return False
        
    def get_temp(self):
        """Obtiene la temperatura del CPU en Celsius."""
        if self.temp_path and self.temp_path.exists():
            with open(self.temp_path, "r") as f:
                return int(f.read()) / 1000.0
        return 0.0
    
    def get_current_vid(self):
        """Traduce el valor hexadecimal del MSR a voltaje real."""
        try:
            # Leemos el valor en hexadecimal
            res = subprocess.check_output(["sudo", "rdmsr", "-x", "0xC0010064"]).decode().strip()
            # Extrae los dígitos del VID
            raw_hex = res[-4:-2] 
            vid_dec = int(raw_hex, 16)
            # Fórmula estándar AMD: 1.55V - (0.00625 * VID)
            voltage = 1.5500 - (0.00625 * vid_dec)
            return f"{voltage:.4f} V"
        except:
            return "--- V"

    def stress_test(self, seconds=45):
        """Usa stress-ng para una carga real y pesada."""
        try:
            # --cpu 4: Usa todos los núcleos
            # --cpu-method matrixprod: Cálculo de matrices, muy sensible al voltaje
            res = subprocess.run(
                ["stress-ng", "--cpu", "4", "--cpu-method", "matrixprod", "--timeout", f"{seconds}s"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            return res.returncode == 0
        except:
            # Si stress-ng no está, cae de vuelta a un bucle infinito de Python (emergencia)
            return False

    def get_all_cpu_freqs(self):
        """Lee la frecuencia actual de cada núcleo."""
        freqs = []
        try:
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "cpu MHz" in line:
                        freqs.append(float(line.split(":")[1].strip()))
            return freqs[:4]
        except:
            return [0.0, 0.0, 0.0, 0.0]

    def get_gpu_freq(self):
        """Lee la frecuencia de la GPU desde amdgpu_pm_info."""
        try:
            path = "/sys/kernel/debug/dri/0000:00:01.0/amdgpu_pm_info"
            output = subprocess.check_output(["sudo", "cat", path]).decode()
            for line in output.split('\n'):
                if "sclk:" in line:
                    raw_value = line.split("sclk:")[1].strip().split()[0]
                    mhz = int(raw_value) // 100 
                    return f"{mhz} MHz"
            return "--- MHz"
        except:
            return "OFF"

    def get_detailed_temps(self):
        """Diferencia entre temperatura de CPU y GPU para el dashboard."""
        temps = {"package": 0, "gpu": 0}
        raw_values = []
        try:
            cmd = "find /sys/class/hwmon/hwmon*/ -name 'temp*_input'"
            paths = subprocess.check_output(cmd, shell=True).decode().splitlines()
            for p in paths:
                try:
                    with open(p, "r") as f:
                        val = int(f.read().strip()) / 1000
                        if 20 < val < 110:
                            raw_values.append(val)
                except: continue
            if raw_values:
                temps["package"] = max(raw_values)
                others = [v for v in raw_values if v != temps["package"]]
                temps["gpu"] = others[0] if others else temps["package"]
        except:
            pass
        return temps
    
    def get_ram_usage(self):
        """Uso de RAM en GB directamente del kernel."""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            mem_data = {}
            for line in lines:
                parts = line.split()
                mem_data[parts[0].replace(':', '')] = int(parts[1])
            total = mem_data['MemTotal'] / 1048576
            free = mem_data['MemAvailable'] / 1048576
            used = total - free
            return {
                "total": total,
                "used": used,
                "free": free,
                "percent": (used / total) * 100
            }
        except:
            return {"total": 0, "used": 0, "free": 0, "percent": 0}

    def set_turbo_boost(self, enable: bool):
        """Control del Turbo Core mediante registros MSR."""
        try:
            value = "0x01000000" if not enable else "0x00000000"
            subprocess.run(["sudo", "wrmsr", "-a", "0xc0010015", value], check=True)
            return True
        except:
            return False

    def set_intelligent_eco(self):
        """Modo eco: Ondemand y voltaje ajustado."""
        try:
            os.system("echo ondemand | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor")
            subprocess.run(["sudo", "wrmsr", "-a", "0xC0010064", "0x8000012100003F09"])
            return True
        except:
            return False