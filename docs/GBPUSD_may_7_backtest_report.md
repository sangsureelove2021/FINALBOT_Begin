# REPORT: GBPUSD 1-Day Backtest (07/05/2026)
Generated at: 2026-06-07 04:03:19

## Executive Summary
- **Total Trades Executed**: 12
- **Wins**: 6
- **Losses**: 6
- **Win Rate**: 50.00%
- **Total PnL**: -31.50 THB
- **Ending Balance**: 1968.50 THB

## 1. Market State Transitions & Strategy Eligibility
Below is the log of every market state transition detected, along with the strategies that were eligible for that state:

| Time (ICT Thai) | Old State | New State | Eligible Strategies |
| :--- | :--- | :--- | :--- |
| 2026-05-07 00:00:00 | None | DISTRIBUTION | ema_crossover |
| 2026-05-07 01:00:00 | DISTRIBUTION | TRENDING_WEAK | ema_crossover |
| 2026-05-07 02:15:00 | TRENDING_WEAK | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 02:30:00 | CHOPPY_UNCERTAIN | TRENDING_WEAK | ema_crossover |
| 2026-05-07 04:30:00 | TRENDING_WEAK | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 04:45:00 | CHOPPY_UNCERTAIN | ACCUMULATION | ema_crossover |
| 2026-05-07 07:45:00 | ACCUMULATION | TRENDING_WEAK | ema_crossover |
| 2026-05-07 08:00:00 | TRENDING_WEAK | ACCUMULATION | ema_crossover |
| 2026-05-07 08:15:00 | ACCUMULATION | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 08:45:00 | CHOPPY_UNCERTAIN | TRENDING_WEAK | ema_crossover |
| 2026-05-07 10:45:00 | TRENDING_WEAK | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 11:30:00 | CHOPPY_UNCERTAIN | TRENDING_WEAK | ema_crossover |
| 2026-05-07 12:00:00 | TRENDING_WEAK | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 12:15:00 | CHOPPY_UNCERTAIN | TRENDING_WEAK | ema_crossover |
| 2026-05-07 12:30:00 | TRENDING_WEAK | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 12:45:00 | CHOPPY_UNCERTAIN | ACCUMULATION | ema_crossover |
| 2026-05-07 13:00:00 | ACCUMULATION | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 13:30:00 | CHOPPY_UNCERTAIN | TRENDING_WEAK | ema_crossover |
| 2026-05-07 18:15:00 | TRENDING_WEAK | CHOPPY_UNCERTAIN | ema_crossover |
| 2026-05-07 19:00:00 | CHOPPY_UNCERTAIN | TRENDING_WEAK | ema_crossover |
| 2026-05-07 21:00:00 | TRENDING_WEAK | DISTRIBUTION | ema_crossover |
| 2026-05-07 21:15:00 | DISTRIBUTION | TRENDING_WEAK | ema_crossover |
| 2026-05-07 21:45:00 | TRENDING_WEAK | DISTRIBUTION | ema_crossover |
| 2026-05-07 22:00:00 | DISTRIBUTION | TRENDING_WEAK | ema_crossover |
| 2026-05-07 22:30:00 | TRENDING_WEAK | DISTRIBUTION | ema_crossover |
| 2026-05-08 00:00:00 | DISTRIBUTION | TRENDING_WEAK | ema_crossover |

## 2. Detailed CALL/PUT Signals & Outcomes
Detailed logs of every signal check that yielded a pattern setup or signal:

| Time (ICT) | Strategy | Action | Entry Score | Block Score | Confidence | Execution | Outcome | PnL | Fail Reason | details |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 2026-05-07 00:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3585955667310825, "ema20": 1.359227368557631} |
| 2026-05-07 00:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3588003778207218, "ema20": 1.3592257144092852} |
| 2026-05-07 00:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3590252518804813, "ema20": 1.359249455894115} |
| 2026-05-07 00:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359175167920321, "ema20": 1.3592709362851516} |
| 2026-05-07 00:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592934452802141, "ema20": 1.3592956090198989} |
| 2026-05-07 00:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594756301868094, "ema20": 1.3593474557799086} |
| 2026-05-07 00:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595170867912063, "ema20": 1.3593715076103934} |
| 2026-05-07 00:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593580578608042, "ema20": 1.3593399354570226} |
| 2026-05-07 00:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592003719072028, "ema20": 1.3592966082706395} |
| 2026-05-07 00:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3590602479381353, "ema20": 1.3592474074829595} |
| 2026-05-07 00:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.358941831958757, "ema20": 1.3591957496274394} |
| 2026-05-07 00:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3589295546391713, "ema20": 1.359168059186731} |
| 2026-05-07 01:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3590247030927811, "ema20": 1.3591725297403756} |
| 2026-05-07 01:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3590331353951874, "ema20": 1.3591608602412921} |
| 2026-05-07 01:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3590554235967915, "ema20": 1.3591550640278358} |
| 2026-05-07 01:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359070282397861, "ema20": 1.3591498198347085} |
| 2026-05-07 01:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591268549319075, "ema20": 1.359158408421879} |
| 2026-05-07 01:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359121236621272, "ema20": 1.3591537980959858} |
| 2026-05-07 01:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591241577475146, "ema20": 1.3591515316106537} |
| 2026-05-07 01:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591227718316765, "ema20": 1.3591485286001153} |
| 2026-05-07 01:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | INSUFFICIENT_VOLUME | {"ema5": 1.3591601812211178, "ema20": 1.359156763971533, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5"} |
| 2026-05-07 01:45:00 | ema_crossover | PUT | 34.6 | 0.0 | 0.55 | Yes | LOSS | -35.00 | None | {"ema5": 1.3591417874807452, "ema20": 1.3591518340694824, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_PUT"} |
| 2026-05-07 01:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591011916538303, "ema20": 1.3591392784438172} |
| 2026-05-07 01:55:00 | ema_crossover | CALL | 70.0 | 0.0 | 0.69 | Yes | WIN | +29.75 | None | {"ema5": 1.3591641277692204, "ema20": 1.3591536328777394, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5", "confluence": "M5_CALL_M1_NO_SETUP"} |
| 2026-05-07 02:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3592460851794803, "ema20": 1.3591780487941452} |
| 2026-05-07 02:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593273901196536, "ema20": 1.359207758432798} |
| 2026-05-07 02:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593965934131025, "ema20": 1.3592389242963412} |
| 2026-05-07 02:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594777289420683, "ema20": 1.3592771219824038} |
| 2026-05-07 02:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595968192947123, "ema20": 1.3593302532221747} |
| 2026-05-07 02:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3596678795298083, "ema20": 1.3593759433914914} |
| 2026-05-07 02:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3596435863532057, "ema20": 1.359396805925635} |
| 2026-05-07 02:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3595707242354704, "ema20": 1.3593994910755745} |
| 2026-05-07 02:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3595471494903135, "ema20": 1.3594090633540912} |
| 2026-05-07 02:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3594514329935423, "ema20": 1.3593948668441778} |
| 2026-05-07 02:50:00 | ema_crossover | PUT | 54.9 | 0.0 | 0.50 | Yes | LOSS | -35.00 | None | {"ema5": 1.3593759553290283, "ema20": 1.3593786890494943, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_NO_SETUP"} |
| 2026-05-07 02:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593589702193523, "ema20": 1.3593735758066854} |
| 2026-05-07 03:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593526468129016, "ema20": 1.3593703781108106} |
| 2026-05-07 03:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593167645419344, "ema20": 1.3593584373383525} |
| 2026-05-07 03:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593145096946229, "ema20": 1.3593538242585095} |
| 2026-05-07 03:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593596731297486, "ema20": 1.3593629838529373} |
| 2026-05-07 03:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | CANDLE_BODY_TOO_SMALL | {"ema5": 1.3593831154198324, "ema20": 1.3593693663431337, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5"} |
| 2026-05-07 03:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3594337436132216, "ema20": 1.359385140977121} |
| 2026-05-07 03:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3594241624088146, "ema20": 1.3593870323126331} |
| 2026-05-07 03:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593844416058765, "ema20": 1.35937921971143} |
| 2026-05-07 03:40:00 | ema_crossover | PUT | 81.9 | 0.0 | 0.80 | Yes | WIN | +29.75 | None | {"ema5": 1.3593079610705843, "ema20": 1.3593578654531986, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_NO_SETUP"} |
| 2026-05-07 03:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3592169740470563, "ema20": 1.3593271163624179} |
| 2026-05-07 03:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591796493647044, "ema20": 1.35930596242314} |
| 2026-05-07 03:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591497662431364, "ema20": 1.3592853945733172} |
| 2026-05-07 04:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3592081774954243, "ema20": 1.3592891665187155} |
| 2026-05-07 04:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359247118330283, "ema20": 1.3592925792312187} |
| 2026-05-07 04:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | INSUFFICIENT_VOLUME | {"ema5": 1.3593147455535222, "ema20": 1.3593075716853882, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5"} |
| 2026-05-07 04:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3593581637023482, "ema20": 1.3593206600963035} |
| 2026-05-07 04:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3594221091348988, "ema20": 1.3593425019918937} |
| 2026-05-07 04:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3595030727565993, "ema20": 1.3593732160879037} |
| 2026-05-07 04:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359500381837733, "ema20": 1.3593848145557226} |
| 2026-05-07 04:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594852545584888, "ema20": 1.359391498883749} |
| 2026-05-07 04:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594051697056593, "ema20": 1.3593775466091063} |
| 2026-05-07 04:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359366779803773, "ema20": 1.3593692088368103} |
| 2026-05-07 04:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359354519869182, "ema20": 1.359365474661876} |
| 2026-05-07 04:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593580132461214, "ema20": 1.359365429455983} |
| 2026-05-07 05:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593186754974143, "ema20": 1.3593534837935084} |
| 2026-05-07 05:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593024503316096, "ema20": 1.3593455329560316} |
| 2026-05-07 05:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592999668877397, "ema20": 1.3593407202935524} |
| 2026-05-07 05:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593416445918267, "ema20": 1.3593487469322616} |
| 2026-05-07 05:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593744297278845, "ema20": 1.3593574377006177} |
| 2026-05-07 05:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593912864852564, "ema20": 1.3593638722053207} |
| 2026-05-07 05:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593608576568377, "ema20": 1.3593577891381474} |
| 2026-05-07 05:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593805717712253, "ema20": 1.3593637139821335} |
| 2026-05-07 05:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593853811808168, "ema20": 1.3593666936028828} |
| 2026-05-07 05:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594052541205446, "ema20": 1.359374151354989} |
| 2026-05-07 05:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359406836080363, "ema20": 1.359377565511657} |
| 2026-05-07 05:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359409557386909, "ema20": 1.359381130701023} |
| 2026-05-07 06:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359434704924606, "ema20": 1.3593910230152113} |
| 2026-05-07 06:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359494803283071, "ema20": 1.3594123541566199} |
| 2026-05-07 06:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359543202188714, "ema20": 1.3594340347131322} |
| 2026-05-07 06:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359572134792476, "ema20": 1.3594526980737862} |
| 2026-05-07 06:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595247565283175, "ema20": 1.3594505363524731} |
| 2026-05-07 06:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594631710188785, "ema20": 1.3594400090808092} |
| 2026-05-07 06:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594237806792524, "ema20": 1.3594309605969226} |
| 2026-05-07 06:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594108537861684, "ema20": 1.3594265833972157} |
| 2026-05-07 06:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593822358574457, "ema20": 1.359416908787957} |
| 2026-05-07 06:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593864905716306, "ema20": 1.359414822236723} |
| 2026-05-07 06:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593676603810871, "ema20": 1.3594067439284638} |
| 2026-05-07 06:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593167735873917, "ema20": 1.3593884826019433} |
| 2026-05-07 07:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592511823915947, "ema20": 1.3593629128303297} |
| 2026-05-07 07:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592557882610632, "ema20": 1.3593535877988698} |
| 2026-05-07 07:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592721921740423, "ema20": 1.3593489603894537} |
| 2026-05-07 07:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594864614493616, "ema20": 1.3594028689237914} |
| 2026-05-07 07:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594959742995745, "ema20": 1.3594135480739065} |
| 2026-05-07 07:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594723161997164, "ema20": 1.3594146387335344} |
| 2026-05-07 07:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359373210799811, "ema20": 1.3593918159970073} |
| 2026-05-07 07:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3593138071998743, "ema20": 1.35937307161634} |
| 2026-05-07 07:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359245871466583, "ema20": 1.3593480171766885} |
| 2026-05-07 07:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359225580977722, "ema20": 1.3593324917312897} |
| 2026-05-07 07:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3591987206518148, "ema20": 1.359314635375929} |
| 2026-05-07 07:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.35919414710121, "ema20": 1.35930228914965} |
| 2026-05-07 08:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592044314008067, "ema20": 1.359294928278255} |
| 2026-05-07 08:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3592346209338713, "ema20": 1.3592949351088972} |
| 2026-05-07 08:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359268080622581, "ema20": 1.3592987508128118} |
| 2026-05-07 08:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595120537483876, "ema20": 1.359365536449687} |
| 2026-05-07 08:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597597024989252, "ema20": 1.3594502472640024} |
| 2026-05-07 08:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359946468332617, "ema20": 1.3595330808579071} |
| 2026-05-07 08:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3600976455550782, "ema20": 1.3596156445857255} |
| 2026-05-07 08:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3602167637033855, "ema20": 1.3596955831966087} |
| 2026-05-07 08:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.360312842468924, "ema20": 1.3597726705112172} |
| 2026-05-07 08:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3604518949792825, "ema20": 1.3598638447482445} |
| 2026-05-07 08:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3605079299861884, "ema20": 1.359935859534126} |
| 2026-05-07 08:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3605419533241259, "ema20": 1.3600000633880187} |
| 2026-05-07 09:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3605279688827507, "ema20": 1.3600476763986835} |
| 2026-05-07 09:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3604936459218337, "ema20": 1.3600836119797615} |
| 2026-05-07 09:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3604207639478894, "ema20": 1.3601018394102604} |
| 2026-05-07 09:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603438426319263, "ema20": 1.3601102356569021} |
| 2026-05-07 09:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.360300895087951, "ema20": 1.3601202132133876} |
| 2026-05-07 09:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603039300586341, "ema20": 1.360138288145446} |
| 2026-05-07 09:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603076200390896, "ema20": 1.3601551178458797} |
| 2026-05-07 09:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.360348413359393, "ema20": 1.360181297098653} |
| 2026-05-07 09:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603006089062621, "ema20": 1.360183554517829} |
| 2026-05-07 09:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603087392708415, "ema20": 1.3601970255161309} |
| 2026-05-07 09:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603491595138943, "ema20": 1.3602192135622138} |
| 2026-05-07 09:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3603461063425963, "ema20": 1.3602307170324792} |
| 2026-05-07 10:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.360350737561731, "ema20": 1.3602430296960526} |
| 2026-05-07 10:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3602821583744873, "ema20": 1.3602336935345236} |
| 2026-05-07 10:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.360226438916325, "ema20": 1.3602223893883787} |
| 2026-05-07 10:15:00 | ema_crossover | PUT | 88.6 | 0.0 | 0.85 | Yes | LOSS | -35.00 | None | {"ema5": 1.3601309592775501, "ema20": 1.360195495160914, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_NO_SETUP"} |
| 2026-05-07 10:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3601339728517001, "ema20": 1.3601902099074934} |
| 2026-05-07 10:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3600743152344668, "ema20": 1.3601678089639226} |
| 2026-05-07 10:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3600345434896446, "ema20": 1.360147541443549} |
| 2026-05-07 10:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3599730289930965, "ema20": 1.360119204163211} |
| 2026-05-07 10:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359892019328731, "ema20": 1.3600821371000482} |
| 2026-05-07 10:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359836346219154, "ema20": 1.3600481240429008} |
| 2026-05-07 10:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597325641461029, "ema20": 1.3599983027054816} |
| 2026-05-07 10:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3596500427640688, "ema20": 1.3599494167335309} |
| 2026-05-07 11:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595283618427128, "ema20": 1.359886138949385} |
| 2026-05-07 11:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359487241228475, "ema20": 1.3598403161923007} |
| 2026-05-07 11:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595114941523168, "ema20": 1.3598136194120816} |
| 2026-05-07 11:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595209961015446, "ema20": 1.3597875604204548} |
| 2026-05-07 11:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3596023307343632, "ema20": 1.359785411808983} |
| 2026-05-07 11:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3596765538229088, "ema20": 1.3597891821128893} |
| 2026-05-07 11:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3597293692152725, "ema20": 1.3597935457211856} |
| 2026-05-07 11:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3597595794768484, "ema20": 1.3597960651763108} |
| 2026-05-07 11:40:00 | ema_crossover | CALL | 92.6 | 0.0 | 0.95 | Yes | LOSS | -35.00 | None | {"ema5": 1.3598780529845658, "ema20": 1.3598264399214242, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5", "confluence": "M5_CALL_M1_NO_SETUP"} |
| 2026-05-07 11:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359887035323044, "ema20": 1.3598339218336695} |
| 2026-05-07 11:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.359888023548696, "ema20": 1.3598392626114153} |
| 2026-05-07 11:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3598536823657974, "ema20": 1.3598340947436613} |
| 2026-05-07 12:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3598191215771984, "ema20": 1.3598260857204554} |
| 2026-05-07 12:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3598477477181323, "ema20": 1.3598336013661263} |
| 2026-05-07 12:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3598301651454217, "ema20": 1.3598299250455428} |
| 2026-05-07 12:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3598717767636146, "ema20": 1.3598418369459675} |
| 2026-05-07 12:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3598595178424098, "ema20": 1.3598411858082562} |
| 2026-05-07 12:25:00 | ema_crossover | PUT | 76.9 | 0.0 | 0.87 | Yes | LOSS | -35.00 | None | {"ema5": 1.3597830118949399, "ema20": 1.3598210728741364, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_NO_SETUP"} |
| 2026-05-07 12:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597303412632935, "ema20": 1.3598023992670758} |
| 2026-05-07 12:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597235608421956, "ema20": 1.3597935993368782} |
| 2026-05-07 12:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597257072281304, "ema20": 1.3597875422571755} |
| 2026-05-07 12:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359722138152087, "ema20": 1.3597806334707778} |
| 2026-05-07 12:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597180921013914, "ema20": 1.3597739064735608} |
| 2026-05-07 12:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359690394734261, "ema20": 1.3597606772856026} |
| 2026-05-07 13:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3596235964895074, "ema20": 1.3597348984964976} |
| 2026-05-07 13:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595923976596715, "ema20": 1.359715384353974} |
| 2026-05-07 13:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594732651064478, "ema20": 1.3596696334631193} |
| 2026-05-07 13:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3594355100709654, "ema20": 1.3596401445618698} |
| 2026-05-07 13:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3595253400473104, "ema20": 1.3596463212702632} |
| 2026-05-07 13:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.359565226698207, "ema20": 1.3596461954349999} |
| 2026-05-07 13:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3594784844654715, "ema20": 1.3596137006316666} |
| 2026-05-07 13:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3595506563103146, "ema20": 1.3596214434286509} |
| 2026-05-07 13:40:00 | ema_crossover | CALL | 72.8 | 30.0 | 0.41 | Yes | WIN | +29.75 | None | {"ema5": 1.3596421042068765, "ema20": 1.3596408297687794, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5", "confluence": "M5_CALL_M1_NO_SETUP"} |
| 2026-05-07 13:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3600280694712512, "ema20": 1.3597512269336576} |
| 2026-05-07 13:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3600887129808341, "ema20": 1.3597949196066426} |
| 2026-05-07 13:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3600608086538895, "ema20": 1.3598149272631528} |
| 2026-05-07 14:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3600438724359263, "ema20": 1.359833505619043} |
| 2026-05-07 14:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3602642482906178, "ema20": 1.359916505083896} |
| 2026-05-07 14:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3606678321937453, "ema20": 1.360064933171144} |
| 2026-05-07 14:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3611668881291636, "ema20": 1.360264939535797} |
| 2026-05-07 14:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3612929254194426, "ema20": 1.3603868500561975} |
| 2026-05-07 14:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361533616946295, "ema20": 1.360541911955607} |
| 2026-05-07 14:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3616640779641969, "ema20": 1.360673634626502} |
| 2026-05-07 14:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3616443853094646, "ema20": 1.3607623360906447} |
| 2026-05-07 14:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3617345902063098, "ema20": 1.3608721136058213} |
| 2026-05-07 14:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3617347268042066, "ema20": 1.3609542932624097} |
| 2026-05-07 14:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361731484536138, "ema20": 1.3610276939040848} |
| 2026-05-07 14:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3617609896907588, "ema20": 1.3611031516275052} |
| 2026-05-07 15:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361872326460506, "ema20": 1.3611976133772667} |
| 2026-05-07 15:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361999884307004, "ema20": 1.3612983168651462} |
| 2026-05-07 15:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362076589538003, "ema20": 1.3613870485922752} |
| 2026-05-07 15:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620977263586687, "ema20": 1.3614587582501538} |
| 2026-05-07 15:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361906817572446, "ema20": 1.3614650669882344} |
| 2026-05-07 15:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3619645450482973, "ema20": 1.361523632036974} |
| 2026-05-07 15:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361984696698865, "ema20": 1.361571381366786} |
| 2026-05-07 15:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3619881311325768, "ema20": 1.3616117259985208} |
| 2026-05-07 15:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3619904207550513, "ema20": 1.3616482282843758} |
| 2026-05-07 15:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620052805033676, "ema20": 1.3616850636858637} |
| 2026-05-07 15:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362065187002245, "ema20": 1.3617326766681623} |
| 2026-05-07 15:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620984580014968, "ema20": 1.3617738503188135} |
| 2026-05-07 16:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362138972000998, "ema20": 1.3618163407646409} |
| 2026-05-07 16:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621159813339987, "ema20": 1.361840498787056} |
| 2026-05-07 16:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362075654222666, "ema20": 1.3618552131882888} |
| 2026-05-07 16:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620871028151107, "ema20": 1.361879478598928} |
| 2026-05-07 16:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621347352100739, "ema20": 1.3619128615895066} |
| 2026-05-07 16:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362093156806716, "ema20": 1.3619221128666963} |
| 2026-05-07 16:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620537712044773, "ema20": 1.3619271497365348} |
| 2026-05-07 16:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621425141363184, "ema20": 1.361964564047341} |
| 2026-05-07 16:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621633427575457, "ema20": 1.3619874627094992} |
| 2026-05-07 16:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362175561838364, "ema20": 1.3620077043562135} |
| 2026-05-07 16:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362207041225576, "ema20": 1.362032684893717} |
| 2026-05-07 16:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362109694150384, "ema20": 1.3620214768086012} |
| 2026-05-07 17:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620397961002562, "ema20": 1.3620099075887344} |
| 2026-05-07 17:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | CANDLE_BODY_TOO_SMALL | {"ema5": 1.3619998640668376, "ema20": 1.3620013449612358, "crossover_type": "DEAD_CROSS", "timeframe": "M5"} |
| 2026-05-07 17:10:00 | ema_crossover | CALL | 70.4 | 0.0 | 0.92 | Yes | WIN | +29.75 | None | {"ema5": 1.3621015760445585, "ema20": 1.3620302644887372, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5", "confluence": "M5_CALL_M1_NO_SETUP"} |
| 2026-05-07 17:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621943840297057, "ema20": 1.362063572632667} |
| 2026-05-07 17:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3623762560198038, "ema20": 1.3621279942866988} |
| 2026-05-07 17:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362500837346536, "ema20": 1.3621872329260607} |
| 2026-05-07 17:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3626338915643574, "ema20": 1.362255115504531} |
| 2026-05-07 17:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3626325943762385, "ema20": 1.3622908187898137} |
| 2026-05-07 17:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362696729584159, "ema20": 1.3623416931907837} |
| 2026-05-07 17:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3627311530561061, "ema20": 1.3623853414583282} |
| 2026-05-07 17:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3625591020374042, "ema20": 1.362369118462297} |
| 2026-05-07 17:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3625094013582695, "ema20": 1.3623730119420783} |
| 2026-05-07 18:00:00 | ema_crossover | PUT | 96.1 | 0.0 | 0.60 | Yes | WIN | +29.75 | None | {"ema5": 1.3623362675721797, "ema20": 1.3623365346142613, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_NO_SETUP"} |
| 2026-05-07 18:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3623141783814532, "ema20": 1.3623301979843316} |
| 2026-05-07 18:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621827855876356, "ema20": 1.3622911315096333} |
| 2026-05-07 18:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3618901903917573, "ema20": 1.3621972142230014} |
| 2026-05-07 18:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.361621793594505, "ema20": 1.362091289058906} |
| 2026-05-07 18:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3615295290630034, "ema20": 1.3620202139104387} |
| 2026-05-07 18:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3613896860420023, "ema20": 1.3619335268713493} |
| 2026-05-07 18:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3613731240280016, "ema20": 1.3618770005026493} |
| 2026-05-07 18:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.361513749352001, "ema20": 1.3618691909309684} |
| 2026-05-07 18:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3614741662346674, "ema20": 1.3618240298899242} |
| 2026-05-07 18:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.361409444156445, "ema20": 1.3617722175194549} |
| 2026-05-07 18:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.36142462943763, "ema20": 1.3617420063271257} |
| 2026-05-07 19:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3615414196250868, "ema20": 1.3617451485816852} |
| 2026-05-07 19:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3617926130833913, "ema20": 1.3617975153834294} |
| 2026-05-07 19:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | CANDLE_BODY_TOO_SMALL | {"ema5": 1.3618967420555943, "ema20": 1.361826799632627, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5"} |
| 2026-05-07 19:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620244947037297, "ema20": 1.3618699615723764} |
| 2026-05-07 19:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.36208966313582, "ema20": 1.3619032985654835} |
| 2026-05-07 19:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.36203977542388, "ema20": 1.3619067939401994} |
| 2026-05-07 19:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3621498502825866, "ema20": 1.3619509088030377} |
| 2026-05-07 19:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3622165668550577, "ema20": 1.3619889174884627} |
| 2026-05-07 19:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3622810445700386, "ema20": 1.3620290205847996} |
| 2026-05-07 19:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3624506963800258, "ema20": 1.3621014948148185} |
| 2026-05-07 19:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3625671309200174, "ema20": 1.362168019118169} |
| 2026-05-07 19:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3625530872800118, "ema20": 1.3622020172973912} |
| 2026-05-07 20:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362480391520008, "ema20": 1.3622146823166874} |
| 2026-05-07 20:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3623269276800056, "ema20": 1.3621961411436696} |
| 2026-05-07 20:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3623496184533372, "ema20": 1.3622150800823676} |
| 2026-05-07 20:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3623114123022249, "ema20": 1.3622169772173802} |
| 2026-05-07 20:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3623759415348167, "ema20": 1.362244407958582} |
| 2026-05-07 20:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3624222943565445, "ema20": 1.362270178629193} |
| 2026-05-07 20:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3624881962376965, "ema20": 1.3623034949502222} |
| 2026-05-07 20:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362577130825131, "ema20": 1.3623464954311535} |
| 2026-05-07 20:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3624580872167542, "ema20": 1.3623344482472342} |
| 2026-05-07 20:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3625670581445029, "ema20": 1.3623773579379737} |
| 2026-05-07 20:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362548038763002, "ema20": 1.3623899905153094} |
| 2026-05-07 20:55:00 | ema_crossover | PUT | 77.7 | 0.0 | 0.94 | Yes | WIN | +29.75 | None | {"ema5": 1.362268692508668, "ema20": 1.3623252295138515, "crossover_type": "DEAD_CROSS", "timeframe": "M5", "confluence": "M5_PUT_M1_NO_SETUP"} |
| 2026-05-07 21:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3621474616724454, "ema20": 1.3622852076553895} |
| 2026-05-07 21:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3619466411149637, "ema20": 1.3622147116882095} |
| 2026-05-07 21:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3618810940766424, "ema20": 1.3621704534321897} |
| 2026-05-07 21:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.361987396051095, "ema20": 1.3621732673910287} |
| 2026-05-07 21:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3619832640340634, "ema20": 1.3621543847823592} |
| 2026-05-07 21:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3619955093560425, "ema20": 1.3621415862316584} |
| 2026-05-07 21:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3620320062373619, "ema20": 1.3621381018286434} |
| 2026-05-07 21:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3619830041582413, "ema20": 1.362113996892582} |
| 2026-05-07 21:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3618953361054942, "ema20": 1.3620764733790027} |
| 2026-05-07 21:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3618685574036629, "ema20": 1.362051571152431} |
| 2026-05-07 21:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3619707049357752, "ema20": 1.362063326280771} |
| 2026-05-07 21:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3620221366238503, "ema20": 1.3620691999683165} |
| 2026-05-07 22:00:00 | ema_crossover | CALL | 96.0 | 0.0 | 0.97 | Yes | LOSS | -35.00 | None | {"ema5": 1.3623514244159003, "ema20": 1.362158799971334, "crossover_type": "GOLDEN_CROSS", "timeframe": "M5", "confluence": "M5_CALL_M1_NO_SETUP"} |
| 2026-05-07 22:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3624942829439335, "ema20": 1.362217961878826} |
| 2026-05-07 22:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.362611188629289, "ema20": 1.3622776797951281} |
| 2026-05-07 22:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3625891257528595, "ema20": 1.3623031388622588} |
| 2026-05-07 22:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3626360838352398, "ema20": 1.3623437923039485} |
| 2026-05-07 22:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | NO_CROSSOVER_DETECTED | {"ema5": 1.3624573892234932, "ema20": 1.3623205739892867} |
| 2026-05-07 22:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3620715928156621, "ema20": 1.3622233764664977} |
| 2026-05-07 22:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3620077285437748, "ema20": 1.362190673945879} |
| 2026-05-07 22:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3619251523625167, "ema20": 1.3621496573796048} |
| 2026-05-07 22:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3618184349083444, "ema20": 1.3620977852482137} |
| 2026-05-07 22:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3616406232722298, "ema20": 1.3620203771293362} |
| 2026-05-07 22:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.36152541551482, "ema20": 1.361951293593209} |
| 2026-05-07 23:00:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3612802770098802, "ema20": 1.3618406942033796} |
| 2026-05-07 23:05:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3610151846732537, "ema20": 1.3617115804697244} |
| 2026-05-07 23:10:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3608001231155025, "ema20": 1.361583810901179} |
| 2026-05-07 23:15:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3605817487436684, "ema20": 1.361446781291543} |
| 2026-05-07 23:20:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3603078324957791, "ema20": 1.3612861354542534} |
| 2026-05-07 23:25:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3603068883305196, "ema20": 1.36119269398242} |
| 2026-05-07 23:30:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3603662588870131, "ema20": 1.3611252945555228} |
| 2026-05-07 23:35:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.360369172591342, "ema20": 1.3610538379311872} |
| 2026-05-07 23:40:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.360179448394228, "ema20": 1.3609344247948836} |
| 2026-05-07 23:45:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3600212989294853, "ema20": 1.3608173367191805} |
| 2026-05-07 23:50:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597858659529902, "ema20": 1.3606742570316395} |
| 2026-05-07 23:55:00 | ema_crossover | NO_SETUP | 0.0 | 100.0 | 0.00 | No (Blocked/Cooldown) | N/A | 0.00 | MARKET_STATE_BLOCKED | {"ema5": 1.3597255773019934, "ema20": 1.3605724230286262} |
