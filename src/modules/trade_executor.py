# src/modules/trade_executor.py

import logging
from datetime import datetime

class TradeExecutor:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("smc_lit_bot")

    def backtest(self, data):
        """Ejecuta backtesting de estrategia SMC+LIT"""
        results = {
            'total_trades': 0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0
        }
        
        signals = data['signals']
        market_data = data['market_data']
        
        # Procesamos las señales filtradas
        for signal_type, is_active in signals.items():
            if is_active and signal_type in ['BOS', 'LIT_confirmation']:
                results['total_trades'] += 1
                # Lógica de ejecución simulada
        
        # Calculamos métricas si tenemos los métodos implementados
        try:
            results['win_rate'] = self.calculate_win_rate(signals)
            results['profit_factor'] = self.calculate_profit_factor(signals)
            results['max_drawdown'] = self.calculate_max_drawdown(market_data['close'].tolist())
        except Exception as e:
            self.logger.warning(f"No se pudieron calcular algunas métricas: {e}")
            
        return results

    def calculate_sharpe_ratio(self, returns):
        """Calcula ratio de Sharpe para evaluación de riesgo"""
        try:
            risk_free_rate = self.config['risk'].get('risk_free_rate', 0.01)
            excess_returns = returns - risk_free_rate
            return excess_returns.mean() / excess_returns.std()
        except Exception as e:
            self.logger.warning(f"Error al calcular Sharpe ratio: {e}")
            return 0.0
            
    def calculate_win_rate(self, signals):
        """Calcula la tasa de acierto de las señales"""
        try:
            # Si no hay operaciones, devolvemos 0
            if not signals:
                return 0.0
                
            # Para señales booleanas simples
            if isinstance(signals.get('BOS'), bool):
                return 1.0 if signals.get('BOS') and signals.get('LIT_confirmation') else 0.0
                
            # Para análisis más detallado necesitaríamos un historial de operaciones
            # Este es un placeholder que debería ser implementado con datos reales
            return 0.5  # Valor por defecto del 50%
        except Exception as e:
            self.logger.warning(f"Error al calcular win rate: {e}")
            return 0.0
            
    def calculate_profit_factor(self, signals):
        """Calcula el factor de beneficio (ganancias brutas / pérdidas brutas)"""
        try:
            # Si no hay operaciones, devolvemos 0
            if not signals:
                return 0.0
                
            # Para señales booleanas simples no podemos calcular un profit factor real
            # Este es un placeholder que debería ser implementado con datos reales
            return 1.0  # Valor neutral por defecto
        except Exception as e:
            self.logger.warning(f"Error al calcular profit factor: {e}")
            return 0.0

    def calculate_max_drawdown(self, equity_curve):
        """Calcula máxima pérdida consecutiva"""
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd

    def execute(self, data):
        """Ejecuta operaciones reales o backtesting según configuración"""
        if self.config['mode'] == 'backtest':
            return self.backtest(data)
            
        # Modo live trading
        import MetaTrader5 as mt5  # Importamos aquí para evitar errores en modo backtest
        
        # Intentar conectar a MT5 con reintentos
        max_retries = 3
        retry_count = 0
        connected = False
        
        while retry_count < max_retries and not connected:
            self.logger.info(f"Conectando a MetaTrader 5 (intento {retry_count + 1}/{max_retries})...")
            if mt5.initialize():
                connected = True
                self.logger.info("Conexión a MetaTrader 5 establecida correctamente.")
            else:
                retry_count += 1
                error = mt5.last_error()
                self.logger.warning(f"Intento {retry_count}: Fallo de conexión con MT5: {error}")
                if retry_count < max_retries:
                    self.logger.info("Reintentando en 5 segundos...")
                    import time
                    time.sleep(5)
        
        if not connected:
            self.logger.error(f"No se pudo conectar a MetaTrader 5 después de {max_retries} intentos. Abortando ejecución.")
            return {
                'status': 'error',
                'message': f"Fallo de conexión con MT5 después de {max_retries} intentos",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        signals = data['signals']
        market_data = data['market_data']
        
        try:
            self.logger.info("Ejecutando operaciones en vivo...")
            # Verificamos si hay señales activas
            if signals.get('BOS') and signals.get('LIT_confirmation'):
                result = self._execute_mt5_order(signals)
                execution_result = {
                    'status': 'success',
                    'action': 'trade_executed',
                    'details': result,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                self.logger.info("No hay señales activas para ejecutar operaciones.")
                execution_result = {
                    'status': 'success',
                    'action': 'no_signals',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
        except Exception as e:
            self.logger.exception(f"Error durante la ejecución de operaciones: {e}")
            execution_result = {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        finally:
            # Cerramos la conexión con MT5
            mt5.shutdown()
            self.logger.info("Conexión con MetaTrader 5 cerrada.")
            
        return execution_result

    def _execute_mt5_order(self, signal):
        """Ejecuta orden en MT5 según señal recibida"""
        symbol = self.config['mt5']['symbol']
        
        # Verificamos si existe el método para calcular lotaje
        try:
            lotaje = self._calcular_lotaje()
        except AttributeError:
            # Si no existe, usamos un valor predeterminado basado en la configuración de riesgo
            lotaje = 0.01  # Valor mínimo por defecto
            self.logger.warning("Método _calcular_lotaje no implementado, usando valor por defecto: 0.01")
        
        # Determinamos la dirección de la operación
        is_buy = True  # Por defecto asumimos compra
        if isinstance(signal.get('BOS'), str):
            is_buy = signal['BOS'] == 'bullish'
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lotaje,
            "type": mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(symbol).ask if is_buy else mt5.symbol_info_tick(symbol).bid,
            "deviation": 20,
            "magic": 234000,
            "comment": "SMC+LIT Bot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK
        }
        
        order_result = {
            "success": False,
            "order_type": "BUY" if is_buy else "SELL",
            "symbol": symbol,
            "volume": lotaje,
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "details": {}
        }
        
        try:
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                self.logger.error("Fallo en ejecución de orden: %s", result.comment)
                order_result["details"] = {
                    "retcode": result.retcode,
                    "comment": result.comment
                }
            else:
                self.logger.info("Orden ejecutada: %s", result)
                order_result["success"] = True
                order_result["details"] = {
                    "order_id": result.order,
                    "price": result.price,
                    "volume": result.volume
                }
        except Exception as e:
            self.logger.exception("Error crítico en ejecución: %s", e)
            order_result["details"] = {"error": str(e)}
            
        return order_result