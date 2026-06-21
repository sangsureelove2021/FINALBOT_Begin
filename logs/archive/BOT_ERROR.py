Python 3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.

==== RESTART: C:\Users\Administrator\Documents\GitHub\BOT_FINALBOT\runner.py ===
2026-06-16 11:43:11,242 | INFO     | [CONN] Connecting to IQ Option (PRACTICE) as venuz20152565@gmail.com...
2026-06-16 11:43:14,515 | INFO     | [CONN] IQ Option connected (DEMO)
2026-06-16 11:43:14,524 | INFO     | [OK] Executor reusing IQ Option connection from adapter
2026-06-16 11:43:14,543 | INFO     | DeepSeek Agent found at: C:\Users\Administrator\AppData\Roaming\npm\deepseek-agent.CMD
11:43:14 - 🚀 Pure AI Bot initialized. Account: PRACTICE | Stake: 35 | Symbols: ['EURJPY-OTC', 'EURUSD-OTC', 'GBPUSD-OTC', 'EURGBP-OTC']
11:43:15 - 📈 Market State for EURJPY-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:43:15 - 📊 Sending M5 indicators for EURJPY-OTC to DeepSeek: Price=183.93896, RSI=39.71, MACD=-0.003255, EMA20=184.09103
Exception in thread Thread-2 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:43:17,750 | ERROR    | Agent error (code 1)
11:43:17 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:43:18 - 📈 Market State for EURUSD-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:43:18 - 📊 Sending M5 indicators for EURUSD-OTC to DeepSeek: Price=1.17477, RSI=53.47, MACD=0.000073, EMA20=1.17426
Exception in thread Thread-5 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:43:21,077 | ERROR    | Agent error (code 1)
11:43:21 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:43:21 - 📈 Market State for GBPUSD-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:43:21 - 📊 Sending M5 indicators for GBPUSD-OTC to DeepSeek: Price=1.34113, RSI=30.69, MACD=-0.000765, EMA20=1.34545
Exception in thread Thread-8 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:43:24,822 | ERROR    | Agent error (code 1)
11:43:24 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:43:25 - 📈 Market State for EURGBP-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:43:25 - 📊 Sending M5 indicators for EURGBP-OTC to DeepSeek: Price=0.86442, RSI=47.59, MACD=0.000041, EMA20=0.86451
Exception in thread Thread-11 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:43:28,356 | ERROR    | Agent error (code 1)
11:43:28 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:45:07 - 📈 Market State for EURJPY-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:45:07 - 📊 Sending M5 indicators for EURJPY-OTC to DeepSeek: Price=184.17192, RSI=50.63, MACD=0.015448, EMA20=184.09874
Exception in thread Thread-14 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:45:10,332 | ERROR    | Agent error (code 1)
11:45:10 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:45:10 - 📈 Market State for EURUSD-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:45:11 - 📊 Sending M5 indicators for EURUSD-OTC to DeepSeek: Price=1.17494, RSI=54.21, MACD=0.000055, EMA20=1.17432
Exception in thread Thread-17 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:45:13,474 | ERROR    | Agent error (code 1)
11:45:13 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:45:14 - 📈 Market State for GBPUSD-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:45:14 - 📊 Sending M5 indicators for GBPUSD-OTC to DeepSeek: Price=1.34045, RSI=29.15, MACD=-0.000692, EMA20=1.34498
Exception in thread Thread-20 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:45:16,845 | ERROR    | Agent error (code 1)
11:45:16 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
11:45:17 - 📈 Market State for EURGBP-OTC: LIQUIDITY_VOID (conf=85, qual=10, tradeable=False)
11:45:17 - 📊 Sending M5 indicators for EURGBP-OTC to DeepSeek: Price=0.86496, RSI=52.91, MACD=0.000089, EMA20=0.86455
Exception in thread Thread-23 (_readerthread):
Traceback (most recent call last):
  File "C:\Python314\Lib\threading.py", line 1082, in _bootstrap_inner
    self._context.run(self.run)
    ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "C:\Python314\Lib\threading.py", line 1024, in run
    self._target(*self._args, **self._kwargs)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Python314\Lib\subprocess.py", line 1614, in _readerthread
    buffer.append(fh.read())
                  ~~~~~~~^^
  File "C:\Python314\Lib\encodings\cp874.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x90 in position 11: character maps to <undefined>
2026-06-16 11:45:19,656 | ERROR    | Agent error (code 1)
11:45:19 - 🧠 DeepSeek Decision: NO_TRADE | Confidence: 0% | Expiry Chosen: 5m | Reason: Fallback to NO_TRADE
