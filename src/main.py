# src/main.py

import logging
import time
import signal
import sys
import os
import json
from datetime import datetime
from modules.config_loader import load_config
from modules.data_manager import DataManager
from modules.signal_generator import SignalGenerator
from modules.risk_manager import RiskManager
from modules.trade_executor import TradeExecutor
from modules.logger import setup_logger


# Variable global para controlar la ejecución del bot
running = True

# Manejador de señales para detener el bot de forma segura
def signal_handler(sig, frame):
    global running
    print('\nDeteniendo el bot de forma segura. Por favor espere...')
    running = False

# Función para guardar el estado del bot
def save_bot_state(state, filename='bot_state.json'):
    state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    try:
        with open(state_path, 'w') as f:
            json.dump(state, f)
        return True
    except Exception as e:
        logging.error(f"Error al guardar el estado del bot: {e}")
        return False

# Función para cargar el estado del bot
def load_bot_state(filename='bot_state.json'):
    state_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', filename)
    if not os.path.exists(state_path):
        return {}
    try:
        with open(state_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error al cargar el estado del bot: {e}")
        return {}

def main():
    global running
    
    # Registrar manejadores de señales
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Señal de terminación
    
    # Configuración de logging
    setup_logger()
    logger = logging.getLogger("smc_lit_bot")
    logger.info("Iniciando bot SMC + LIT en modo continuo...")

    # Cargar configuración
    config = load_config()
    if not config:
        logger.error("No se pudo cargar la configuración. Abortando.")
        return
    
    # Cargar estado anterior si existe
    bot_state = load_bot_state()
    logger.info(f"Estado anterior cargado: {bot_state if bot_state else 'No hay estado previo'}")

    # Inicializar módulos
    data_manager = DataManager(config)
    signal_generator = SignalGenerator(config)
    risk_manager = RiskManager(config)
    trade_executor = TradeExecutor(config)
    
    # Configurar intervalo de ejecución (en segundos)
    interval = config.get('execution', {}).get('interval', 300)  # 5 minutos por defecto

    # Contador de ciclos
    cycle_count = 0
    last_execution_time = 0
    
    # Bucle principal del bot
    logger.info(f"Bot iniciado. Ejecutando ciclos cada {interval} segundos. Presiona Ctrl+C para detener.")
    
    while running:
        current_time = time.time()
        
        # Verificar si es momento de ejecutar un nuevo ciclo
        if current_time - last_execution_time >= interval:
            cycle_count += 1
            last_execution_time = current_time
            
            logger.info(f"\n{'='*50}\nIniciando ciclo #{cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}")
            
            # Flujo principal del bot
            try:
                logger.info("Descargando y preparando datos de mercado...")
                market_data = data_manager.get_market_data()
                market_data = data_manager.calculate_volume_profile(market_data)
                market_data = data_manager.identify_liquidity_pools(market_data)
                market_data = data_manager.detect_order_blocks(market_data)

                logger.info("Generando señales SMC+LIT...")
                signals = signal_generator.generate_signals(market_data)

                logger.info("Analizando zonas de liquidez y gestionando riesgo...")
                market_data = risk_manager.analyze_liquidity_zones(market_data)
                market_data = risk_manager.validate_order_blocks(market_data)
                filtered_signals = risk_manager.filter_signals(signals)

                logger.info("Ejecutando estrategia...")
                results = trade_executor.execute({
                    'signals': filtered_signals,
                    'market_data': market_data
                })
                
                # Guardar estado del bot
                bot_state = {
                    'last_cycle': cycle_count,
                    'last_execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'last_results': results
                }
                save_bot_state(bot_state)
                
                logger.info(f"Resultado del ciclo #{cycle_count}: {results}")
                logger.info(f"Ciclo #{cycle_count} completado correctamente.")
                
            except Exception as e:
                logger.exception(f"Error crítico en ciclo #{cycle_count}: {e}")
        
        # Pequeña pausa para no consumir demasiados recursos
        time.sleep(1)
    
    logger.info("Bot detenido correctamente.")

if __name__ == "__main__":
    main()