# Bot de Trading Automático SMC + LIT

## Descripción
Este bot implementa una estrategia de trading automático basada en los conceptos de Smart Money Concepts (SMC) y Liquidity Imbalance Theory (LIT) para el par EUR/USD. El sistema está diseñado para ejecutarse de forma continua, monitoreando el mercado y ejecutando operaciones cuando se cumplen las condiciones de la estrategia.

## Características Principales
- Ejecución continua y automática
- Conexión con MetaTrader 5 para operaciones en vivo
- Análisis de zonas de liquidez y bloques de órdenes
- Gestión de riesgo integrada
- Persistencia de estado entre ejecuciones
- Manejo seguro de interrupciones

## Requisitos
- Python 3.8 o superior
- MetaTrader 5 instalado y configurado
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clona el repositorio:
```
git clone https://github.com/Pablo-app-developer/Bot-trading-autom-tico.git
cd Bot-trading-autom-tico
```

2. Crea y activa un entorno virtual:
```
python -m venv venv
venv\Scripts\activate
```

3. Instala las dependencias:
```
pip install -r requirements.txt
```

4. Configura tus credenciales y parámetros en `config/config.yaml`

## Uso

### Ejecución como Servicio
El bot puede ejecutarse como un servicio en segundo plano utilizando el script `run_bot_service.py`:

```
# Iniciar el bot
python run_bot_service.py start

# Verificar el estado del bot
python run_bot_service.py status

# Detener el bot
python run_bot_service.py stop

# Reiniciar el bot
python run_bot_service.py restart
```

### Ejecución Manual
También puedes ejecutar el bot directamente:

```
python src/main.py
```

## Configuración
La configuración del bot se realiza a través del archivo `config/config.yaml`. Los principales parámetros son:

```yaml
# Modo de operación
mode: "live"  # 'live' para trading real, 'backtest' para backtesting

# Configuración de ejecución continua
execution:
  interval: 300  # Intervalo en segundos entre ciclos de ejecución (5 minutos)
  mode: "live"   # Modo de ejecución: 'live' o 'backtest'

# Configuración de MetaTrader 5
mt5:
  server: "MetaQuotes-Demo"
  login: 92058594
  password: "@2LpLiDh"
  symbol: "EURUSD"
  timeframe: "M15"

# Configuración de riesgo
risk:
  max_daily_risk: 2.0
  trade_risk: 0.5
  rr_ratio: 1.5
```

## Estructura del Proyecto
```
├── config/              # Archivos de configuración
├── data/                # Datos de mercado y estado del bot
│   ├── market/          # Datos de mercado descargados
│   ├── model/           # Modelos entrenados
│   └── processed/       # Datos procesados
├── logs/                # Registros de ejecución
├── src/                 # Código fuente
│   ├── modules/         # Módulos del bot
│   └── main.py          # Punto de entrada principal
├── requirements.txt     # Dependencias
└── run_bot_service.py   # Script para ejecutar como servicio
```

## Persistencia y Recuperación
El bot guarda su estado en el archivo `data/bot_state.json` después de cada ciclo de ejecución. En caso de interrupción, el bot puede recuperar su estado anterior al reiniciarse.

## Logs
Los registros de ejecución se almacenan en el directorio `logs/`. Puedes consultar `logs/bot.log` para ver la actividad del bot y `logs/bot_service.log` para los registros del servicio.

## Seguridad
El bot implementa un manejo seguro de señales para garantizar que se detenga correctamente en caso de interrupción. Esto evita operaciones incompletas o estados inconsistentes.

## Soporte
Para cualquier problema o consulta, por favor abre un issue en el repositorio de GitHub.

## Licencia
Este proyecto está licenciado bajo los términos de la licencia MIT.