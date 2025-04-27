# src/modules/risk_manager.py

import logging

class RiskManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("smc_lit_bot.risk")
        self.liquidity_pool_threshold = config['lit_params']['liquidity_zone_threshold']
        # Cambia 'smc_params' a 'smc_lit_params' para acceder a la clave correcta
        self.order_block_validation = config['smc_lit_params']['order_block_validation_window']

    def analyze_liquidity_zones(self, df):
        """Evalúa zonas de liquidez usando perfiles de volumen y price action"""
        df['liquidity_strength'] = df['volume_profile'] * df['liquidity_zone'].astype(int)
        return df

    def validate_order_blocks(self, df):
        """Confirma bloques de orden con acción del precio y volumen"""
        df['valid_bullish_block'] = df['bullish_block'] & (df['liquidity_strength'] > self.liquidity_pool_threshold)
        df['valid_bearish_block'] = df['bearish_block'] & (df['liquidity_strength'] > self.liquidity_pool_threshold)
        return df

    def filter_signals(self, signals):
        """Aplica filtros SMC+LIT para gestión de riesgo"""
        filtered = {
            'BOS': signals.get('BOS') and signals.get('LIT_confirmation'),
            'CHoCH': signals.get('CHoCH') and signals.get('volume_profile') > self.liquidity_pool_threshold,
            'Liquidity_Zone': signals.get('liquidity_strength', 0) > self.liquidity_pool_threshold
        }
        return {k: v for k, v in filtered.items() if v}