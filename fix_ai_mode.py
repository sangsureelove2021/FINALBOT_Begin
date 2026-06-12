import re

# Read the file
with open('runner.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the old else block (AI mode) - exact as in file
old_block = r"""            else:
                #  AI MODE (default): Write full JSON, return AI_EVAL 
                all_strategy_results = [
                    {'strategy': s['strategy'], 'signal': s['signal'], 'confidence': s['confidence'], 'reason': s['reason'][:12]}
                    for s in triggered_signals
                ] + [
                    {'strategy': s.STRATEGY_NAME, 'signal': 'BLOCKED', 'confidence': 0, 'reason': 'Inactive strategy'}
                    for s in []
                ]

                if not all_strategy_results:
                    all_strategy_results = [{'strategy': 'none', 'signal': 'NO_SIGNAL', 'confidence': 0, 'reason': 'No trigger'}]

                return {
                    'symbol': symbol,
                    'signal': first_signal['signal'] if first_signal else 'NO_SIGNAL',
                    'confidence': first_signal['confidence'] if first_signal else 0,
                    'reason': first_signal['reason'] if first_signal else 'No strategy triggered — waiting for AI evaluation',
                    'executed': False,
                    'simulated': True,
                    'market_state': state_str,
                    'current_price': current_price,
                    'strategy': first_signal['strategy'] if first_signal else 'none',
                    'all_strategies': all_strategy_results
                }"""

# Define the new block
new_block = r"""            else:
                #  AI MODE (default): Write pending signals JSON for external AI, then return AI_EVAL
                all_strategy_results = [
                    {'strategy': s['strategy'], 'signal': s['signal'], 'confidence': s['confidence'], 'reason': s['reason'][:12]}
                    for s in triggered_signals
                ] + [
                    {'strategy': s.STRATEGY_NAME, 'signal': 'BLOCKED', 'confidence': 0, 'reason': 'Inactive strategy'}
                    for s in []
                ]

                if not all_strategy_results:
                    all_strategy_results = [{'strategy': 'none', 'signal': 'NO_SIGNAL', 'confidence': 0, 'reason': 'No trigger'}]

                # Write pending signal for external AI consumption (Ai_BOT mode)
                if first_signal:
                    sig_action = first_signal['signal']
                    sig_strategy = first_signal['strategy']
                    sig_reason = first_signal['reason']
                    sig_conf = first_signal['confidence']
                    
                    # Compute timestamp and auxiliary data
                    _now_dt = self.data_adapter.simulated_time if (hasattr(self.data_adapter, 'simulated_time') and self.data_adapter.simulated_time) else datetime.now(timezone.utc)
                    _utc_hour = _now_dt.hour
                    _hour_gmt7 = (_utc_hour + 7) % 24
                    _session = get_session(_utc_hour)
                    
                    pending_path = os.path.join("logs", "pending_signals.json")
                    try:
                        # Ensure logs directory exists
                        os.makedirs(os.path.dirname(pending_path), exist_ok=True)
                        
                        existing_pending = []
                        if os.path.exists(pending_path):
                            try:
                                with open(pending_path, "r", encoding="utf-8") as f_pend:
                                    existing_pending = json.load(f_pend)
                                    if not isinstance(existing_pending, list):
                                        existing_pending = []
                            except:
                                existing_pending = []
                        
                        new_signal = {
                            'timestamp': market_state_data['timestamp'],
                            'symbol': symbol,
                            'direction': sig_action,
                            'confidence': sig_conf,
                            'size': float(self.position_sizer.calculate(
                                confidence=sig_conf
                            )) if hasattr(self, 'position_sizer') else 30.0,
                            'state': state_str,
                            'session': _session,
                            'hour_gmt7': _hour_gmt7,
                            'reason': sig_reason,
                            'strategy': sig_strategy,
                            'indicators': market_state_data['indicators'],
                            'candles': market_state_data['candles'],
                            'candle_count': len(market_state_data['candles']),
                            'processed': False,
                            'ai_action': 'AI_PENDING',   # Distinguish from HYBRID's 'PENDING'
                            'trade_outcome': None
                        }
                        existing_pending.append(new_signal)
                        with open(pending_path, "w", encoding="utf-8") as f_pend:
                            json.dump(existing_pending, f_pend, indent=2, ensure_ascii=False)
                        logger.debug(f"[AI MODE] Signal written to {pending_path} for external AI consumption")
                    except Exception as e:
                        logger.error(f"[AI MODE ERR] Failed to write pending signal: {e}")

                return {
                    'symbol': symbol,
                    'signal': first_signal['signal'] if first_signal else 'NO_SIGNAL',
                    'confidence': first_signal['confidence'] if first_signal else 0,
                    'reason': first_signal['reason'] if first_signal else 'No strategy triggered — waiting for AI evaluation',
                    'executed': False,
                    'simulated': True,
                    'market_state': state_str,
                    'current_price': current_price,
                    'strategy': first_signal['strategy'] if first_signal else 'none',
                    'all_strategies': all_strategy_results
                }"""

# Replace
if old_block in content:
    new_content = content.replace(old_block, new_block)
    with open('runner.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("SUCCESS: Replaced AI mode block with signal writing code.")
else:
    print("ERROR: Could not find the exact old block. Checking for variations...")
    # Try to find with regex
    pattern = r"            else:\n                #  AI MODE \(default\): Write full JSON, return AI_EVAL \n                all_strategy_results = \[.*?\]\n\n                if not all_strategy_results:\n                    all_strategy_results = \[.*?\]\n\n                return \{[^}]*\}"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print("Found via regex, but exact string mismatch. Manual fix required.")
    else:
        print("No match found.")
