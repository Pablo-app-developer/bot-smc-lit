# src/modules/config_loader.py

import yaml
import os
import logging

def load_config(config_path="../../config/config.yaml"):
    """Carga la configuración desde un archivo YAML."""
    absolute_config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), config_path))
    try:
        with open(absolute_config_path, 'r') as f:
            config = yaml.safe_load(f)
        logging.getLogger("smc_lit_bot").info(f"Configuración cargada desde {absolute_config_path}")
        return config
    except FileNotFoundError:
        logging.getLogger("smc_lit_bot").error(f"Archivo de configuración no encontrado en {absolute_config_path}")
        return None
    except Exception as e:
        logging.getLogger("smc_lit_bot").error(f"Error al cargar la configuración desde {absolute_config_path}: {e}")
        return None