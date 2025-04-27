# src/modules/signal_generator.py

import logging

class SignalGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("smc_lit_bot.signal")
        self.bos_window = config['smc_params']['bos_validation_window']
        self.choch_volume_multiplier = config['smc_params']['choch_volume_multiplier']
        self.lit_confirmation_bars = config['lit_params']['confirmation_bars']

    def detect_bos(self, df):
        """Detecta Break of Structure (BOS) en los datos"""
        df['higher_high'] = df['high'].rolling(3).apply(lambda x: x.iloc[2] > x.iloc[1] > x.iloc[0] if len(x) == 3 else False, raw=False)
        df['lower_low'] = df['low'].rolling(3).apply(lambda x: x.iloc[2] < x.iloc[1] < x.iloc[0] if len(x) == 3 else False, raw=False)
        
        last_3 = df.iloc[-self.bos_window:]
        
        if last_3['higher_high'].iloc[-1] and last_3['close'].iloc[-1] > last_3['high'].iloc[-2]:
            return 'bullish'
        if last_3['lower_low'].iloc[-1] and last_3['close'].iloc[-1] < last_3['low'].iloc[-2]:
            return 'bearish'
        return None

    def identify_choch(self, df):
        """Identifica Change of Character usando perfiles de volumen"""
        df['volume_profile'] = df['real_volume'].rolling(5).mean()
        df['price_change'] = df['close'].pct_change()
        
        bull_cond = (df['close'].iloc[-1] > df['open'].iloc[-1]) & \
                    (df['volume_profile'].iloc[-1] > self.choch_volume_multiplier * df['volume_profile'].iloc[-2])
        
        bear_cond = (df['close'].iloc[-1] < df['open'].iloc[-1]) & \
                    (df['volume_profile'].iloc[-1] > self.choch_volume_multiplier * df['volume_profile'].iloc[-2])
        
        if bull_cond and df['price_change'].iloc[-1] > 0.0015:
            return 'bullish'
        if bear_cond and df['price_change'].iloc[-1] < -0.0015:
            return 'bearish'
        return None

    def generate_signals(self, df):
        """Genera señales combinando BOS y CHoCH con confirmación LIT"""
        signals = {
            'BOS': self.detect_bos(df),
            'CHoCH': self.identify_choch(df),
            'LIT_confirmation': df['real_volume'].iloc[-self.lit_confirmation_bars:].mean() > \
                               df['real_volume'].rolling(20).mean().iloc[-1]
        }
        return signals