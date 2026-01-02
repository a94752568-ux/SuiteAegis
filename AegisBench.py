import time

class AegisBench:
    def __init__(self, core, db, log_callback):
        self.core = core
        self.db = db
        self.log = log_callback

    def find_sweet_spot(self, profile_name="gaming"):
        self.log(f"🚀 Iniciando búsqueda de Sweet Spot para: {profile_name.upper()}")
        
        # Recuperamos la config actual de la DB
        p_state, current_vid, freq = self.db.get_profile(profile_name)
        
        stable_vid = current_vid
        
        # En AMD, subir el VID = Bajar el voltaje real.
        # Probaremos subir 10 puntos de VID para buscar el ahorro máximo.
        for test_vid in range(current_vid, current_vid + 10):
            self.log(f"🧪 Probando estabilidad: VID {test_vid}...")
            
            # Aplicamos el voltaje de prueba
            self.core.apply_profile(p_state, test_vid, freq)
            time.sleep(2)
            
            # Prueba de fuego: Estresar el CPU
            if self.core.stress_test(15):
                self.log(f"✅ ESTABLE a VID {test_vid}")
                stable_vid = test_vid
                # Guardamos este éxito en la base de datos inmediatamente
                self.db.update_vid(profile_name, stable_vid)
            else:
                # Si el comando de estrés falla o hay un error de sistema
                self.log(f"❌ Inestabilidad detectada en VID {test_vid}. Revirtiendo...")
                break
        
        self.log(f"🎯 Sweet Spot hallado: Perfil {profile_name} optimizado a VID {stable_vid}")
        self.core.apply_profile(p_state, stable_vid, freq)