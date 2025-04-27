# src/modules/data_manager.py

import logging
import MetaTrader5 as mt5
import pandas as pd

class DataManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("smc_lit_bot.data")
        self.volume_lookback = config['smc_params']['volume_lookback_period']
        self.liquidity_threshold = config['lit_params']['liquidity_zone_threshold']
        self.symbol = config['mt5']['symbol']
        self.timeframe = config['mt5']['timeframe']

    def _connect_to_mt5(self):
        """Conecta a MetaTrader 5 usando las credenciales del archivo de configuración"""
        if not mt5.initialize(login=self.config['mt5']['login'], password=self.config['mt5']['password'], server=self.config['mt5']['server']):
            self.logger.error("Fallo de conexión con MT5: %s", mt5.last_error())
            return False
        self.logger.info("Conexión exitosa a MT5")
        return True

    def _fetch_raw_data(self):
        """Obtiene datos de mercado desde MT5"""
        if not self._connect_to_mt5():
            return pd.DataFrame()  # Devuelve un DataFrame vacío en caso de fallo

        self.logger.info(f"Obteniendo datos de mercado para {self.symbol} en {self.timeframe}")
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, 1000)
        mt5.shutdown()

        if rates is None:
            self.logger.error("No se pudieron obtener los datos de mercado")
            return pd.DataFrame()

        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.rename(columns={'time': 'datetime'}, inplace=True)

        # Verifica las columnas disponibles
        self.logger.info(f"Columnas disponibles en los datos: {df.columns}")

        return df

    def calculate_volume_profile(self, df):
        """Calcula perfiles de volumen usando media móvil ponderada"""
        df['volume_profile'] = df['real_volume'].ewm(span=self.volume_lookback).mean()
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