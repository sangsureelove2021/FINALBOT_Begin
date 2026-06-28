import os
import re

base = r"e:\BOT_FINALBOT13 STG\BOT_FINALBOT"

# 1. Fix data_adapter.py
path = os.path.join(base, "core/data/data_adapter.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
# L148
text = text.replace('logger.error(f"[DataAdapter] update failed: {e}")\n            raise', 
                    'logger.exception(f"[DataAdapter] update failed: {e}")\n            raise Exception(str(e))')
# L211 .get
text = text.replace('self._last_block_m5.get(symbol, -1)', 'self._last_block_m5[symbol]')
# other .gets just in case
text = text.replace('self._store_m1.get(symbol)', 'self._store_m1[symbol]')
text = text.replace('self._store_m5.get(symbol)', 'self._store_m5[symbol]')
text = text.replace('self._m5_csv_written.get(symbol, -1)', 'self._m5_csv_written[symbol]')
text = text.replace('self._store_m15.get(symbol)', 'self._store_m15[symbol]')
text = text.replace('self._last_block_m15.get(symbol, -1)', 'self._last_block_m15[symbol]')
text = text.replace('self._m15_csv_written.get(symbol, -1)', 'self._m15_csv_written[symbol]')
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 2. Fix iq_option_adapter.py
path = os.path.join(base, "core/data/iq_option_adapter.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace('self._TF_SECONDS.get(timeframe, 60)', 'self._TF_SECONDS[timeframe]')
text = text.replace('df.get("volume", 0)', 'df["volume"]')

text = text.replace('raise RuntimeError(\n                "iqoptionapi library not installed. Run: pip install iqoptionapi"\n            ) from e', 
                    'logger.exception("iqoptionapi library not installed"); raise Exception(str(e))')
text = text.replace('raise Exception(f"WebSocket fetch failed for {symbol}: {e}")',
                    'logger.exception(f"WebSocket fetch failed for {symbol}: {e}"); raise Exception(str(e))')
text = text.replace('raise Exception(f"REST fetch failed for {symbol}: {e}")',
                    'logger.exception(f"REST fetch failed for {symbol}: {e}"); raise Exception(str(e))')
text = text.replace('raise Exception(f"REST fetch timeout for {symbol}") from e',
                    'logger.exception(f"REST fetch timeout for {symbol}: {e}"); raise Exception(str(e))')
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 3. Fix deepseek_agent_bridge.py
path = os.path.join(base, "core/ai_analysis/deepseek_agent_bridge.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace('logger.exception(f"AI Readiness check failed: {e}")\n            raise e',
                    'logger.exception(f"AI Readiness check failed: {e}")\n            raise Exception(str(e))')
text = text.replace('logger.exception("Failed to write prompt temp file — falling back to inline arg")\n            raise e',
                    'logger.exception("Failed to write prompt temp file — falling back to inline arg")\n            raise Exception(str(e))')
text = text.replace('logger.exception(f"Unexpected error calling agent: {e}")\n            self.consecutive_failures += 1\n            logger.warning("AI unexpected error — ข้ามรอบนี้ ไม่เทรด")\n            raise e',
                    'logger.exception(f"Unexpected error calling agent: {e}")\n            self.consecutive_failures += 1\n            logger.warning("AI unexpected error — ข้ามรอบนี้ ไม่เทรด")\n            raise Exception(str(e))')
text = text.replace('logger.exception("Failed to parse confidence value")\n                raise e',
                    'logger.exception("Failed to parse confidence value")\n                raise Exception(str(e))')
text = text.replace('logger.exception(f"Parse error: {e}. Raw response: {response_text[:500]}")\n                raise e',
                    'logger.exception(f"Parse error: {e}. Raw response: {response_text[:500]}")\n                raise Exception(str(e))')
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 4. Fix prompt_ai_context.py
path = os.path.join(base, "core/ai_analysis/prompt_ai_context.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace('logger.exception(f"Failed to save prompt logs: {e}")\n            raise e',
                    'logger.exception(f"Failed to save prompt logs: {e}")\n            raise Exception(str(e))')
text = text.replace('logger.exception("Failed to build prompt context")\n        raise e',
                    'logger.exception("Failed to build prompt context")\n        raise Exception(str(e))')
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 5. Fix advanced_tools_manager.py
path = os.path.join(base, "core/orchestration/advanced_tools/advanced_tools_manager.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace("pa_data.get('wick_to_body_ratio', 0)", "pa_data['wick_to_body_ratio']")
text = text.replace("basic_payload.get('m5', {})", "basic_payload['m5']")
text = text.replace("basic_payload.get('meta', {})", "basic_payload['meta']")
text = text.replace("meta_basic.get('close', 0)", "meta_basic['close']")
text = text.replace("pa_data.get('fractal_support', 0)", "pa_data['fractal_support']")
text = text.replace("pa_data.get('fractal_resistance', 0)", "pa_data['fractal_resistance']")
text = text.replace("m5_basic.get('support', 0)", "m5_basic['support']")
text = text.replace("m5_basic.get('resistance', 0)", "m5_basic['resistance']")
text = text.replace("m5_basic.get('atr14', 0)", "m5_basic['atr14']")
text = text.replace("pa_data.get('volume_momentum', 'NEUTRAL')", "pa_data['volume_momentum']")
text = text.replace("m5_basic.get('pivot', 0)", "m5_basic['pivot']")
text = text.replace("trap_data.get('trap_detected', False)", "trap_data['trap_detected']")
text = text.replace("trap_data.get('trap_type', 'NONE')", "trap_data['trap_type']")
text = text.replace("candle_data.get('last_candle_color', 'NEUTRAL')", "candle_data['last_candle_color']")
text = text.replace("pa_data.get('directional_bias', 'NEUTRAL')", "pa_data['directional_bias']")
text = text.replace("pa_data.get('move_type') == 'CLEAN_TRENDING'", "pa_data['move_type'] == 'CLEAN_TRENDING'")
text = text.replace("pa_data.get('move_type') == 'CHAOTIC'", "pa_data['move_type'] == 'CHAOTIC'")
text = text.replace("pa_data.get('move_type') == 'NOISY'", "pa_data['move_type'] == 'NOISY'")

with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 6. Fix context_builder.py
path = os.path.join(base, "core/orchestration/context_builder.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace("candles.get(timeframe)", "candles[timeframe]")
text = text.replace("candles.get('M5')", "candles['M5']")
text = text.replace("candles.get('M15')", "candles['M15']")
text = text.replace("context.volatility.get('atr_percentile', 50.0)", "context.volatility['atr_percentile']")
text = text.replace("context.strength.get('strength_score', 0)", "context.strength['strength_score']")
text = text.replace("context.trend.get('type', '')", "context.trend['type']")
text = text.replace("context.volatility.get('regime', 'NORMAL')", "context.volatility['regime']")
text = text.replace("context.strength.get('exhaustion_risk', 0)", "context.strength['exhaustion_risk']")
text = text.replace("context.structure.get('bos_detected', False)", "context.structure['bos_detected']")
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 7. Fix context_synthesizer.py
path = os.path.join(base, "core/orchestration/context_synthesizer.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace("kwargs.get('context')", "kwargs['context']")
text = text.replace("ctx.trend.get('direction', 'NONE')", "ctx.trend['direction']")
text = text.replace("ctx.mtf.get('dominant_direction', 'NONE')", "ctx.mtf['dominant_direction']")
text = text.replace("ctx.mtf.get('alignment_score', 50)", "ctx.mtf['alignment_score']")
text = text.replace("ctx.conflict.get('ema_direction', 'NONE')", "ctx.conflict['ema_direction']")
text = text.replace("ctx.candle_patterns.get('bias', 'NEUTRAL')", "ctx.candle_patterns['bias']")
text = text.replace("ctx.price_action.get('directional_bias', 'NEUTRAL')", "ctx.price_action['directional_bias']")
text = text.replace("ctx.noise.get('noise_level', 50) / 100.0", "ctx.noise['noise_level'] / 100.0")
text = text.replace("ctx.noise.get('noise_level', 0)", "ctx.noise['noise_level']")
text = text.replace("ctx.efficiency.get('overall_efficiency', 50) / 100.0", "ctx.efficiency['overall_efficiency'] / 100.0")
text = text.replace("ctx.regime_quality.get('overall_quality', 50) / 100.0", "ctx.regime_quality['overall_quality'] / 100.0")
text = text.replace("ctx.traps.get('trap_detected')", "ctx.traps['trap_detected']")
text = text.replace("ctx.anomaly.get('anomaly_detected')", "ctx.anomaly['anomaly_detected']")
text = text.replace("ctx.transition.get('in_transition')", "ctx.transition['in_transition']")
text = text.replace("ctx.strength.get('exhaustion_risk', 0)", "ctx.strength['exhaustion_risk']")
text = text.replace("ctx.market_state.get('state', 'UNKNOWN')", "ctx.market_state['state']")
text = text.replace("ctx.market_state.get('tradeable', False)", "ctx.market_state['tradeable']")
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 8. Fix check_news.py
path = os.path.join(base, "core/orchestration/check_news.py")
with open(path, "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace('event.get("country", "")', 'event["country"]')
text = text.replace('_PRECALCULATED_NEWS.get(symbol, "UNKNOWN")', '_PRECALCULATED_NEWS[symbol]')

# Fix swallowed exception in check_news.py if there is any
# "except swallowed and .get fallback"
# Let's see:
text = text.replace('except Exception as e:\n                        raise', 
                    'except Exception as e:\n                        logger.exception(str(e))\n                        raise Exception(str(e))')
text = text.replace('except Exception as e:\n        raise', 
                    'except Exception as e:\n        logger.exception(str(e))\n        raise Exception(str(e))')
with open(path, "w", encoding="utf-8") as f:
    f.write(text)

# 9. Fix advanced_tools except Exception as e:
adv_dir = os.path.join(base, "core/orchestration/advanced_tools")
for f_name in os.listdir(adv_dir):
    if f_name.endswith(".py"):
        f_path = os.path.join(adv_dir, f_name)
        with open(f_path, "r", encoding="utf-8") as f:
            text = f.read()
        
        # We need to change:
        # except Exception as e:
        #     return something
        # to:
        # except Exception as e:
        #     logger.exception(...); raise Exception(str(e))
        # This is tricky using replace because the block could be anything.
        # Let's use regex.
        new_text = re.sub(
            r'except\s+Exception\s+as\s+e:\s+(?:[ \t]*logger\.[a-zA-Z]+\(.*?\)\n)?(?:[ \t]*return.*?\n)?',
            r'except Exception as e:\n            import logging\n            logging.getLogger(__name__).exception(f"Error: {e}")\n            raise Exception(str(e))\n',
            text
        )
        if new_text != text:
            with open(f_path, "w", encoding="utf-8") as f:
                f.write(new_text)

print("FIX SCRIPT COMPLETE")
