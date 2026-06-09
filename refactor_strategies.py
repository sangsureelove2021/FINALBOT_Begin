import sys, re

def update_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Rename evaluate to evaluate_base
    content = content.replace('def evaluate(self, context: MarketContext) -> Dict[str, Any]:', 'def evaluate_base(self, context: MarketContext, tf: str) -> Dict[str, Any]:')

    # Data block
    content = re.sub(r"df_m5\s*=\s*context\.candles\.get\(['\"]M5['\"]\).*?if df_m5 is None.*?:", 
    """df = context.candles.get(tf)
        
        if df is None or len(df) < 30:""", content, flags=re.DOTALL)
        
    # Standardize _m5 suffixes and series names to not have _m5
    content = content.replace('close_m5', 'close_p').replace('open_m5', 'open_p').replace('high_m5', 'high_p').replace('low_m5', 'low_p').replace('volume_m5', 'volume_p')
    content = content.replace('atr_m5', 'atr_series')
    content = content.replace('tr_m5', 'tr')
    content = content.replace('avg_volume_m5', 'avg_volume').replace('curr_vol_m5', 'curr_vol').replace('curr_close_m5', 'curr_close')
    content = content.replace('prev_close_m5', 'prev_close')
    
    # Specific M1 logic replacements
    if 'rsi_extreme_bounce' in filepath:
        content = content.replace('rsi3_m5', 'rsi3')
        match = re.search(r'# Asynchronous M1 Conditions \(Candle Bounce Confirmation\).*?if not has_valid_bounce:', content, re.DOTALL)
        if match:
            m1_block = match.group(0)
            m1_replacement = """# Candle Bounce Confirmation
            has_valid_bounce = False
            c_open = float(open_p.iloc[-1])
            c_close = float(close_p.iloc[-1])
            body_size = abs(c_close - c_open)
            
            is_body_valid = body_size > 0.10 * atr_val
            if is_body_valid:
                if action == 'CALL' and c_close > c_open:
                    has_valid_bounce = True
                elif action == 'PUT' and c_close < c_open:
                    has_valid_bounce = True

            if not has_valid_bounce:"""
            content = content.replace(m1_block, m1_replacement)

    elif 'rsi_reversal' in filepath:
        content = content.replace('rsi7_m5', 'rsi7')
        match = re.search(r'# Asynchronous M1 Conditions \(Level Touch\).*?if not has_level_touch:', content, re.DOTALL)
        if match:
            m1_block = match.group(0)
            m1_replacement = """# Synchronous Level Touch
            has_level_touch = False
            c_low = float(low_p.iloc[-1])
            c_high = float(high_p.iloc[-1])
            
            if action == 'CALL' and c_low <= local_support * 1.0002:
                has_level_touch = True
            if action == 'PUT' and c_high >= local_resistance * 0.9998:
                has_level_touch = True

            if not has_level_touch:"""
            content = content.replace(m1_block, m1_replacement)
        
    elif 'engulfing_scalper' in filepath:
        match = re.search(r'# Asynchronous M1 Conditions \(Engulfing Pattern\).*?if not has_engulfing:', content, re.DOTALL)
        if match:
            m1_block = match.group(0)
            m1_replacement = """# Engulfing Pattern
            has_engulfing = False
            c_curr_open = float(open_p.iloc[-1])
            c_curr_close = float(close_p.iloc[-1])
            c_prev_open = float(open_p.iloc[-2])
            c_prev_close = float(close_p.iloc[-2])
            
            if action == 'CALL':
                prev_is_bear = c_prev_close < c_prev_open
                curr_is_bull = c_curr_close > c_curr_open
                engulfs = c_curr_close > c_prev_open and c_curr_open <= c_prev_close
                if prev_is_bear and curr_is_bull and engulfs:
                    has_engulfing = True
            elif action == 'PUT':
                prev_is_bull = c_prev_close > c_prev_open
                curr_is_bear = c_curr_close < c_curr_open
                engulfs = c_curr_close < c_prev_open and c_curr_open >= c_prev_close
                if prev_is_bull and curr_is_bear and engulfs:
                    has_engulfing = True

            if not has_engulfing:"""
            content = content.replace(m1_block, m1_replacement)

    elif 'stochastic_crossover' in filepath:
        match = re.search(r'# Asynchronous M1 Conditions \(Candle Body Size >= 0.05 \* ATR_M5\).*?if not has_valid_body:', content, re.DOTALL)
        if match:
            m1_block = match.group(0)
            m1_replacement = """# Candle Body Size Confirmation
            has_valid_body = False
            c_open = float(open_p.iloc[-1])
            c_close = float(close_p.iloc[-1])
            body_size = abs(c_close - c_open)
            
            if body_size >= 0.05 * atr_val:
                if action == 'CALL' and c_close > c_open:
                    has_valid_body = True
                elif action == 'PUT' and c_close < c_open:
                    has_valid_body = True

            if not has_valid_body:"""
            content = content.replace(m1_block, m1_replacement)
        content = content.replace('body_size_m5', 'body_size_current')
        
    # Replace body_size_m5 logic at block score section
    content = content.replace('body_size_m5', 'body_size').replace('upper_wick_m5', 'upper_wick').replace('lower_wick_m5', 'lower_wick')

    # Add evaluate method at the end
    eval_method = """
    def evaluate(self, context: MarketContext) -> Dict[str, Any]:
        audit_id = str(uuid.uuid4())
        
        if not self.is_eligible(context):
            return self._build_no_setup(audit_id, "MARKET_STATE_BLOCKED")

        df_m1 = context.candles.get('M1')
        if df_m1 is None or len(df_m1) == 0:
            return self._build_no_setup(audit_id, "INSUFFICIENT_DATA")
            
        latest_time = df_m1.index[-1]
        if latest_time.minute % 5 != 4:
            return self._build_no_setup(audit_id, "WAITING_FOR_M5_BOUNDARY")

        m1_result = self.evaluate_base(context, 'M1')
        m5_result = self.evaluate_base(context, 'M5')
        
        action_m5 = m5_result.get('action', 'NO_SETUP')
        action_m1 = m1_result.get('action', 'NO_SETUP')
        
        # Confluence logic: M5 must trigger a valid trade, AND M1 must NOT conflict (i.e. not be the opposite).
        if action_m5 in ['CALL', 'PUT']:
            opposite_action = 'PUT' if action_m5 == 'CALL' else 'CALL'
            if action_m1 != opposite_action:
                # M1 agrees or is NO_SETUP (neutral/non-conflicting)
                if 'details' not in m5_result:
                    m5_result['details'] = {}
                m5_result['details']['confluence'] = f"M5_{action_m5}_M1_{action_m1}"
                return m5_result
            else:
                # Conflict (M1 is opposite direction)
                return self._build_no_setup(audit_id, "M1_M5_CONFLICT", {"m5_action": action_m5, "m1_action": action_m1})
                
        return m5_result
"""
    if 'def evaluate(' not in content:
        content += eval_method
    else:
        # It's already there, replace the evaluate with the new one
        content = re.sub(r'    def evaluate\(self, context: MarketContext\) -> Dict\[str, Any\]:.*', eval_method, content, flags=re.DOTALL)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

files = [
    'strategy/reversal_strategy/bb_rsi_confluence.py',
    'strategy/reversal_strategy/rsi_extreme_bounce.py',
    'strategy/reversal_strategy/rsi_reversal.py',
    'strategy/reversal_strategy/engulfing_scalper.py',
    'strategy/reversal_strategy/stochastic_crossover.py'
]

for f in files:
    update_file(f)
    print(f + ' updated.')
