# src/modules/data_manager.py

import logging
import mt5
import pandas as pd
from ta.trend import EMAIndicator

class DataManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("smc_lit_bot.data")
        self.volume_lookback = config['smc_params']['volume_lookback_period']
        self.liquidity_threshold = config['lit_params']['liquidity_zone_threshold']
        self.symbol = config['mt5']['symbol']
        self.timeframe = config['mt5']['timeframe']

    def _connect_to_mt5(self):
        """Conecta a MetaTrader 5 usando la nueva API mt5 (PythonMetaTrader5)."""
        try:
            mt5.initialize()
            from MetaTrader5 import Broker
            self.broker = Broker(
                log=self.config['mt5']['login'],
                password=self.config['mt5']['password'],
                server=self.config['mt5']['server']
            )
            self.logger.info("Conexión exitosa a MT5 (broker creado)")
            return True
        except Exception as e:
            self.logger.error(f"Fallo de conexión con MT5: {e}")
            return False

    def _fetch_raw_data(self):
        """Obtiene datos de mercado desde MT5"""
        if not self._connect_to_mt5():
            return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de fallo

        self.logger.info(f"Obteniendo datos de mercado para {self.symbol} en {self.timeframe}")
        try:
            # Suponiendo que la API Broker tiene un método get_rates o similar
            if hasattr(self.broker, 'get_rates'):
                rates = self.broker.get_rates(self.symbol, self.timeframe, 1000)
                df = pd.DataFrame(rates)
                # Adaptar el procesamiento de columnas según la estructura recibida
                if 'time' in df.columns:
                    df['datetime'] = pd.to_datetime(df['time'], unit='s')
                self.logger.info(f"Columnas disponibles en los datos: {df.columns}")
                return df
            else:
                self.logger.error("La API Broker no tiene un método get_rates. Adapta este bloque según la documentación de la librería mt5/PythonMetaTrader5.")
                return pd.DataFrame()
        except Exception as e:
            self.logger.error(f"Error al obtener datos de mercado: {e}")
            return pd.DataFrame()

    def calculate_volume_profile(self, df):
        """Calcula perfiles de volumen usando un indicador técnico de la librería ta (EMA)."""
        ema = EMAIndicator(close=df['real_volume'], window=self.volume_lookback)
        df['volume_profile'] = ema.ema_indicator()
        return df

    def detect_order_blocks(self, df):
        """Detecta bloques de orden institucional usando velas de absorción"""
        df['bullish_block'] = (df['close'] > df['open']) & \
                            (df['real_volume'] > 1.5 * df['volume_profile'])
        df['bearish_block'] = (df['close'] < df['open']) & \
                            (df['real_volume'] > 1.5 * df['volume_profile'])
        return df

    def get_market_data(self):
        """Obtiene datos y aplica procesamiento SMC+LIT"""
        raw_data = self._fetch_raw_data()
        processed = self.calculate_volume_profile(raw_data)
        processed = self.identify_liquidity_pools(processed)
        return self.detect_order_blocks(processed)

    def identify_liquidity_pools(self, df):
        """Identifica zonas de liquidez usando niveles de precios y volumen"""
        df['liquidity_zone'] = (df['high'].rolling(5).max() - df['low'].rolling(5).min()) * \
                             df['volume_profile'] > self.liquidity_threshold
        return df