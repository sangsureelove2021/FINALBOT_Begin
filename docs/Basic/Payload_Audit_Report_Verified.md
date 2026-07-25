# Payload Audit Report Verified

| เลขลำดับ | รายการในเอกสาร | บอทใช้วิธีใด เพื่อให้ได้ข้อมูลมา | มีโค๊ดคำนวณจริงอยู่ที่ใด | ใช้ข้อมูลจริงมาคำนวณ | ใช้วิธีวิเคราะห์แบบสากล |
|---|---|---|---|---|---|
| 1 | ID: | สร้างจากการนำชื่อ symbol มาต่อกับ timestamp แบบตัดปีออก (MMDDHHMMSS) | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestrator.py _save_txt_payload line 676 | Yes | Yes |
| meta: |  |  |  |  |  |
| 2 | timestamp: | ดึงเวลาปัจจุบันของระบบผ่าน datetime.now().isoformat() | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestrator.py process_cycle line 137 | Yes | Yes |
| 3 | symbol: | รับค่ามาเป็นพารามิเตอร์ (Argument) จากฟังก์ชัน process_cycle | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestrator.py process_cycle line 136 | Yes | Yes |
| 4 | session: | Derived from local UTC time and mapped to fixed hour blocks (if not provided in meta) | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestrator.py line 325-332 _derive_session() | Yes | No (Hardcoded UTC hours ignore DST) |
| 5 | m1_open: | Extracted from the 'open' price of the most recent row in the M1 DataFrame | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_feed\data_adapter.py line 185 | Yes | Yes |
| 6 | m1_age: | Calculated as millisecond difference between broker epoch and candle timestamp | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_feed\data_adapter.py line 186 | Yes | Yes |
| 7 | m1_quality: | กำหนดค่าตายตัวเป็น 'STALE' เนื่องจากไม่ได้รับ forming_data (Hardcoded fallback) | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestration\indicator_store\indicator_store.py บรรทัดที่ 216 | No | No |
| 8 | m5_open: | ดึงราคาเปิด (open) ของแท่งเทียน M5 ล่าสุดจาก DataFrame (df_m5.iloc[-1]['open']) | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestration\indicator_store\indicator_store.py บรรทัดที่ 217 | Yes | Yes |
| 9 | m5_age: | กำหนดค่าตายตัวเป็น 0 เนื่องจากไม่ได้รับ forming_data (Hardcoded fallback) | e:\BOT_FINALBOT13 STG\BOT_FINALBOT_NEW\data_evaluate\orchestration\indicator_store\indicator_store.py บรรทัดที่ 218 | No | No |
| 10 | m5_quality: |  |  |  |  |
| market_context: |  |  |  |  |  |
| 11 | state: |  |  |  |  |
| 12 | description: |  |  |  |  |
| 13 | volatility_regime: |  |  |  |  |
| 14 | news_impact: |  |  |  |  |
| 15 | expected_volatility_%: |  |  |  |  |
| timeframes: |  |  |  |  |  |
| m1: |  |  |  |  |  |
| 16 | last_candle: |  |  |  |  |
| 17 | ema5: |  |  |  |  |
| 18 | ema20: |  |  |  |  |
| 19 | rsi: |  |  |  |  |
| 20 | stoch_k: |  |  |  |  |
| 21 | stoch_d: |  |  |  |  |
| 22 | macd: |  |  |  |  |
| 23 | macd_signal: |  |  |  |  |
| ohclv: |  |  |  |  |  |
| 24 | open: |  |  |  |  |
| 25 | high:  |  |  |  |  |
| 26 | low:  |  |  |  |  |
| 27 | close: |  |  |  |  |
| 28 | volume: |  |  |  |  |
| m5: |  |  |  |  |  |
| 29 | bias: |  |  |  |  |
| 30 | ema5: |  |  |  |  |
| 31 | ema10: |  |  |  |  |
| 32 | ema20: |  |  |  |  |
| 33 | ema50: |  |  |  |  |
| 34 | bb_upper: |  |  |  |  |
| 35 | bb_lower: |  |  |  |  |
| 36 | bb_width: |  |  |  |  |
| 37 | rsi: |  |  |  |  |
| 38 | stoch_k: |  |  |  |  |
| 39 | stoch_d: |  |  |  |  |
| 40 | macd: |  |  |  |  |
| 41 | macd_signal: |  |  |  |  |
| 42 | adx: |  |  |  |  |
| 43 | atr: |  |  |  |  |
| 44 | support: |  |  |  |  |
| 45 | resistance: |  |  |  |  |
| 46 | pivot: |  |  |  |  |
| ohclv: |  |  |  |  |  |
| 47 | open: |  |  |  |  |
| 48 | high:  |  |  |  |  |
| 49 | low:  |  |  |  |  |
| 50 | close: |  |  |  |  |
| 51 | volume: |  |  |  |  |
| m15: |  |  |  |  |  |
| 52 | bias: |  |  |  |  |
| price_action: |  |  |  |  |  |
| 53 | pattern: |  |  |  |  |
| 54 | last_candle_bias: |  |  |  |  |
| 55 | body_strength: |  |  |  |  |
| 56 | wick_dominance: |  |  |  |  |
| 57 | momentum_bias: |  |  |  |  |
| 58 | move_quality: |  |  |  |  |
| 59 | trap_alert: |  |  |  |  |
| 60 | sr_interaction: |  |  |  |  |
| volume: |  |  |  |  |  |
| 61 | tick_volume: |  |  |  |  |
| 62 | volume_momentum: |  |  |  |  |
| 63 | volume_vs_average: |  |  |  |  |
| analysis: |  |  |  |  |  |
| 64 | trend_direction: |  |  |  |  |
| 65 | trend_type: |  |  |  |  |
| 66 | trend_strength_score: |  |  |  |  |
| 67 | mtf_alignment_%: |  |  |  |  |
| 68 | compression_quality_%: |  |  |  |  |
| 69 | exhaustion_risk_%: |  |  |  |  |
| 70 | bos_detected: |  |  |  |  |
| decision_layer: |  |  |  |  |  |
| 71 | tradeable: |  |  |  |  |
| 72 | stability_score: |  |  |  |  |
| 73 | quality_score: |  |  |  |  |
| 74 | risk_level: |  |  |  |  |
| 75 | confidence_score: | รอการวิเคราะห์จาก AI |  |  |  |
| 76 | suggested_expiry_minutes: | รอการวิเคราะห์จาก AI |  |  |  |
| 77 | suggested_action: | รอการวิเคราะห์จาก AI |  |  |  |
| 78 | final_reason_th: | รอการวิเคราะห์จาก AI |  |  |  |
