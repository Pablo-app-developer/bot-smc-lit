# run_bot_service.py

import os
import sys
import time
import logging
import subprocess
import signal
import psutil
from datetime import datetime

# Configuración de logging
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'bot_service.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('bot_service')

# Ruta al script principal
MAIN_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'main.py')

# Archivo para guardar el PID del proceso
PID_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot.pid')

def is_bot_running():
    """Verifica si el bot ya está en ejecución"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            # Verificar si el proceso existe
            if psutil.pid_exists(pid):
                process = psutil.Process(pid)
                # Verificar si es un proceso de Python
                if 'python' in process.name().lower():
                    return True
        except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied):
            # El PID no es válido o el proceso ya no existe
            pass
        # Eliminar el archivo PID si el proceso no existe
        os.remove(PID_FILE)
    return False

def save_pid(pid):
    """Guarda el PID del proceso en ejecución"""
    with open(PID_FILE, 'w') as f:
        f.write(str(pid))

def start_bot():
    """Inicia el bot como un proceso separado"""
    if is_bot_running():
        logger.warning("El bot ya está en ejecución. No se iniciará una nueva instancia.")
        return
    
    logger.info("Iniciando el bot SMC+LIT...")
    try:
        # Iniciar el proceso del bot
        process = subprocess.Popen(
            [sys.executable, MAIN_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Guardar el PID
        save_pid(process.pid)
        
        logger.info(f"Bot iniciado con PID: {process.pid}")
        logger.info("El bot está ejecutándose en segundo plano. Usa 'python run_bot_service.py stop' para detenerlo.")
    except Exception as e:
        logger.error(f"Error al iniciar el bot: {e}")

def stop_bot():
    """Detiene el bot si está en ejecución"""
    if not os.path.exists(PID_FILE):
        logger.warning("No se encontró el archivo PID. El bot no parece estar en ejecución.")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        if psutil.pid_exists(pid):
            logger.info(f"Deteniendo el bot (PID: {pid})...")
            process = psutil.Process(pid)
            
            # Enviar señal de terminación
            process.send_signal(signal.SIGTERM)
            
            # Esperar a que el proceso termine (máximo 10 segundos)
            timeout = 10
            start_time = time.time()
            while process.is_running() and time.time() - start_time < timeout:
                time.sleep(0.5)
            
            # Si el proceso sigue en ejecución, forzar terminación
            if process.is_running():
                logger.warning("El bot no respondió a la señal de terminación. Forzando cierre...")
                process.kill()
            
            logger.info("Bot detenido correctamente.")
        else:
            logger.warning(f"No se encontró un proceso con PID {pid}. El bot no parece estar en ejecución.")
    except (ValueError, psutil.NoSuchProcess, psutil.AccessDenied) as e:
        logger.error(f"Error al detener el bot: {e}")
    finally:
        # Eliminar el archivo PID
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

def status_bot():
    """Muestra el estado actual del bot"""
    if is_bot_running():
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        process = psutil.Process(pid)
        create_time = datetime.fromtimestamp(process.create_time()).strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"El bot está en ejecución:")
        logger.info(f"  - PID: {pid}")
        logger.info(f"  - Iniciado: {create_time}")
        logger.info(f"  - Tiempo de ejecución: {datetime.now() - datetime.fromtimestamp(process.create_time())}")
        
        # Intentar leer el estado del bot
        bot_state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'bot_state.json')
        if os.path.exists(bot_state_path):
            import json
            try:
                with open(bot_state_path, 'r') as f:
                    state = json.load(f)
                logger.info(f"  - Último ciclo: {state.get('last_cycle', 'N/A')}")
                logger.info(f"  - Última ejecución: {state.get('last_execution_time', 'N/A')}")
            except Exception as e:
                logger.error(f"Error al leer el estado del bot: {e}")
    else:
        logger.info("El bot no está en ejecución actualmente.")

def print_usage():
    """Muestra las opciones de uso del script"""
    print("\nUso: python run_bot_service.py [comando]")
    print("Comandos disponibles:")
    print("  start   - Inicia el bot en segundo plano")
    print("  stop    - Detiene el bot si está en ejecución")
    print("  restart - Reinicia el bot")
    print("  status  - Muestra el estado actual del bot")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start_bot()
    elif command == "stop":
        stop_bot()
    elif command == "restart":
        stop_bot()
        time.sleep(2)  # Esperar un poco antes de reiniciar
        start_bot()
    elif command == "status":
        status_bot()
    else:
        print(f"Comando desconocido: {command}")
        print_usage()
        sys.exit(1)