#!/bin/bash
# setup.sh - Configuración de privilegios de Suite Aegis

FOLDER="/home/aegisproject/Desktop/SuiteAegis"

echo "🛡️ Configurando privilegios de Suite Aegis..."

# 1. Asegurar que amdctl sea propiedad de root
sudo chown root:root "$FOLDER/amdctl"

# 2. Activar el bit SUID (Permite ejecutar como root sin pedir clave)
sudo chmod +s "$FOLDER/amdctl"

# 3. Cargar el módulo MSR del kernel (necesario para AMD A8)
sudo modprobe msr
echo "msr" | sudo tee -a /etc/modules

echo "✅ Listo. Ya puedes iniciar la Suite desde el icono o con python3 main.py"
