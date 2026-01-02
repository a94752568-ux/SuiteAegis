import time
import subprocess
import os

class AegisBench:
    def __init__(self, core, db, log_callback):
        self.core = core
        self.db = db
        self.log = log_callback
        # Archivo para saber dónde falló tras un reinicio inesperado
        self.recovery_file = "/home/aegisproject/Desktop/SuiteAegis/last_bench_attempt.txt"

    def find_sweet_spot(self, profile_name="gaming"):
        self.log(f"🧪 [BENCH] Iniciando Análisis Quirúrgico: {profile_name.upper()}")
        
        # Obtener valores base
        p_state, current_vid, freq = self.db.get_profile(profile_name)
        stable_vid = current_vid

        # Rango de exploración (AMD: +VID = -Voltaje)
        for test_vid in range(current_vid, current_vid + 15):
            # 1. Registro preventivo (Por si hay CRASH)
            with open(self.recovery_file, "w") as f:
                f.write(f"PROBANDO_VID:{test_vid}\nESTADO:EJECUTANDO")

            self.log(f"⚡ Probando VID {test_vid}...")
            
            # 2. Aplicar y asentar
            self.core.apply_profile(p_state, test_vid, freq)
            time.sleep(3)

            # 3. Monitoreo de seguridad ANTES del estrés
            temp_pre = self.core.get_temp()
            if temp_pre > 85:
                self.log(f"🛑 Cancelado: Temp inicial muy alta ({temp_pre}°C)")
                break

            # 4. Prueba de fuego
            self.log(f"🔥 Estresando sistema (45s)...")
            success = self.core.stress_test(45) 
            
            if success:
                temp_post = self.core.get_temp()
                # Si sobrevivió pero está hirviendo, paramos aquí
                if temp_post > 90:
                    self.log(f"✅ Estable pero límite térmico alcanzado ({temp_post}°C)")
                    stable_vid = test_vid
                    self.db.update_vid(profile_name, stable_vid)
                    break
                
                self.log(f"✅ ESTABLE a VID {test_vid} | Temp: {temp_post}°C")
                stable_vid = test_vid
                self.db.update_vid(profile_name, stable_vid)
            else:
                self.log(f"❌ Inestabilidad o Error. Límite: VID {stable_vid}")
                break

        # Limpieza
        if os.path.exists(self.recovery_file):
            os.remove(self.recovery_file)
            
        self.log(f"🎯 Sweet Spot final para {profile_name}: VID {stable_vid}")
        self.core.apply_profile(p_state, stable_vid, freq)