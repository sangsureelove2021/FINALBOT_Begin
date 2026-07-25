# 🔄 **การส่งข้อมูลและการบันทึกระหว่าง 9 ไฟล์ใน Data Feed**

## 🎯 **สถานะปัจจุบัน:**
- ✅ **การบันทึกใน RAM (In-Memory Storage)** - ใช้งานจริง
- ✅ **Non-blocking CSV Writing** - บันทึกข้อมูลลง Disk แบบ Async
- ✅ **Multi-timeframe Management** - จัดการ M1, M5, M15 พร้อมกัน
- ✅ **Thread-safe Processing** - ปลอดภัยต่อ concurrent access

---

## 🏗️ **โครงสร้างการส่งข้อมูล (Data Flow):**

### **📊 9 ไฟล์ใน Data Feed:**

1. **data_source.py** - Abstract Interface
2. **iq_option_adapter.py** - IQ API Integration
3. **data_adapter.py** - **👑 Data Controller & Storage Manager**
4. **timeframe_sync.py** - Timeframe Management
5. **candle_validator.py** - Data Quality Control
6. **csv_queue.py** - **🚀 Async Queue Controller**
7. **csv_writer.py** - **💾 Disk Writer**
8. **csv_manager.py** - **📁 File System Manager**
9. **data_monitor.py** - System Monitoring

---

## 🎮 **ใครควบคุมการส่งข้อมูล (Data Flow Controller):**

### **👑 DataAdapter (data_adapter.py) - ผู้ควบคุมหลัก**

```python
# DataAdapter คือศูนย์กลางของการส่งข้อมูล
class DataAdapter:
    def __init__(self):
        # 1. ติดต่อ Components
        self._iq = IQOptionAdapter()              # ข้อมูลจาก IQ Option
        self._csv_queue = CSVQueue()            # Queue สำหรับบันทึก
        self._csv_manager = CSVManager()        # จัดการไฟล์
        self._tf_sync = TimeframeSync()         # Sync timeframe
        self._data_monitor = DataMonitor()      # Monitor ระบบ
        
        # 2. In-Memory Storage
        self._store_m1: Dict[str, pd.DataFrame] = {}    # 💾 RAM Storage M1
        self._store_m5: Dict[str, pd.DataFrame] = {}    # 💾 RAM Storage M5
        self._store_m15: Dict[str, pd.DataFrame] = {}  # 💾 RAM Storage M15
```

#### **หน้าที่ของ DataAdapter:**
- **✅ รับข้อมูล** จาก IQ Option Adapter
- **✅ เก็บใน RAM** (In-Memory Storage)
- **✅ ประมวลผล** Timeframe Sync, Validation
- **✅ ควบคุม** CSV Queue
- **✅ ส่งข้อมูล** สำหรับบันทึก Disk

---

## 💾 **การบันทึกข้อมูล (Storage Methods):**

### **🔄 2 ระบบการบันทึกพร้อมกัน:**

#### **1. In-Memory Storage (หลัก) - การบันทึกใน RAM**
```python
# ใน DataAdapter._store_* (ใช้งานจริง)
self._store_m1: Dict[str, pd.DataFrame] = {}
self._store_m5: Dict[str, pd.DataFrame] = {}
self._store_m15: Dict[str, pd.DataFrame] = {}

# ข้อดี:
# ⚡ การเข้าถึงเร็ว (nanoseconds to access)
# 🔄 Real-time processing โดยตรง
# 🚀 No disk I/O blocking

# การใช้งาน:
data = self._store_m1[symbol]  # เข้าถึงจาก RAM
```

#### **2. Disk Storage (ย่อย) - การบันทึกลงไฟล์ CSV**
```python
# Non-blocking CSV Writing (ใช้งานจริง)
self._csv_queue.enqueue_write(completed_m1, file_path)
self._csv_queue.enqueue_write(completed_m5, file_path)
self._csv_queue.enqueue_write(completed_m15, file_path)

# ข้อดี:
# 💾 ข้อมูลยังคงอยู่หลังปิดโปรแกรม
# 📁 สามารถเปิดได้ด้วยเครื่องอื่น
# 🔄 Historical data สำหรับ backtesting
```

---

## 🔄 **กระบวนการส่งข้อมูลทีละขั้นตอน:**

### **Step 1: รับข้อมูลจาก IQ Option**
```python
# iq_option_adapter.py → DataAdapter
fresh_data = self._iq.get_candles(symbol, 'M1', 5)
```

### **Step 2: บันทึกลง RAM Storage**
```python
# data_adapter.py - บันทึกใน RAM (หลัก)
self._store_m1[symbol] = self._merge(old_data, fresh_data)
```

### **Step 3: ตรวจสอบคุณภาพ**
```python
# candle_validator.py - ตรวจสอบก่อนบันทึก
CandleValidator().validate(data, symbol)
```

### **Step 4: Timeframe Sync**
```python
# timeframe_sync.py - ประมวลผล timeframe อื่นๆ
m15_resampled = self._tf_sync.resample(m5_data, 'M5', 'M15')
```

### **Step 5: Async Queue สำหรับบันทึก Disk**
```python
# data_adapter.py → csv_queue.py - Non-blocking
self._csv_queue.enqueue_write(data, file_path)
```

### **Step 6: Background CSV Writing**
```python
# csv_queue.py → csv_writer.py → csv_manager.py
- Worker thread ทำงานใน background
- เขียนลง CSV โดยไม่ block main thread
- สร้างโฟลเดอร์/ไฟล์ตาม convention
```

### **Step 7: Monitoring**
```python
# data_monitor.py - เฝ้าระวังทุกขั้นตอน
self._data_monitor.report_latency(symbol, "M1", latency)
```

---

## 📊 **ตารางสรุปการส่งข้อมูล:**

| ไฟล์ | บทบาท | การส่งข้อมูล | การบันทึก | สถานะ |
|------|--------|-------------|-------------|--------|
| **iq_option_adapter.py** | Data Source | IQ Option API → DataAdapter | - | ✅ Active |
| **data_adapter.py** | **👑 Controller** | รับ/จัดการ/ส่งทั้งหมด | 💾 RAM + 📁 CSV | ✅ Active |
| **timeframe_sync.py** | Processor | M1→M5, M5→M15 | - | ✅ Active |
| **candle_validator.py** | Validator | ตรวจสอบคุณภาพ | - | ✅ Active |
| **csv_queue.py** | **🚀 Async Queue** | Data → Queue Background | 📝 Queue Memory | ✅ Active |
| **csv_writer.py** | **💾 Disk Writer** | Queue → File | 💾 CSV Files | ✅ Active |
| **csv_manager.py** | **📁 File Manager** | Path Creation | 🗂️ Directory | ✅ Active |
| **data_monitor.py** | Monitor | Tracking Status | - | ✅ Active |
| **data_source.py** | Interface | Contract | - | ✅ Abstract |

---

## 🎯 **แนวทางการทำงาน (Operation Flow):**

### **Memory Usage:**
```python
# In-Memory Storage (หลัก)
DataAdapter RAM Usage: ~10-50MB per symbol (M1+M5+M15)
- M1: 1,000 rows × 6 cols × 8 bytes = 48KB
- M5: 200 rows × 6 cols × 8 bytes = 9.6KB  
- M15: 100 rows × 6 cols × 8 bytes = 4.8KB
- ทั้งหมด ~62KB per symbol × 5 symbols = ~310KB

# Queue Buffer (ย่อย)
CSVQueue Max: 1,000 records × 1KB each = ~1MB
```

### **Disk I/O:**
```python
# CSV Writing (Non-blocking)
- จำนวนเขียน: ~3 files per symbol per cycle (M1+M5+M15)
- ขนาด: ~1-5KB per write
- ความถี่: ทุก 1 นาที (ที่ 2 วินาที)
- รวม: 15 files × 1KB × 1440 mins/day = ~21GB/day
```

---

## ⚙️ **การปรับแต่ง Storage:**

### **Memory Configuration:**
```python
# data_adapter.py (บรรทัด 67-68)
self.cache_size = 1000           # จำนวน candles ใน RAM
self.enable_cache = True          # เปิดใช้งาน In-Memory Storage
```

### **Queue Configuration:**
```python
# csv_queue.py (บรรทัด 32-36)
self.max_queue_size = 1000       # ขนาด Queue
self.max_workers = 1             # จำนวน Worker threads
self.queue_timeout = 30          # Timeout ใน Queue
```

### **File Storage:**
```python
# csv_manager.py (บรรทัด 29-30)
self.base_dir = "data_base/csv/iq_option"      # โฟลเดอร์หลัก
self.naming_convention = "{symbol}/{date}/{symbol}_{timeframe}.csv"
self.auto_create_dirs = True      # สร้างโฟลเดอร์อัตโนมัติ
```

---

## 🚨 **จุดที่ควรสังเกต:**

### **Performance:**
- **RAM Usage:** น้อย (< 100MB) ใช้ได้ดี
- **Queue Management:** ทำงานแบบ Non-blocking ดี
- **Disk I/O:** บันทึกแบบ Async ไม่ block main thread

### **Error Handling:**
- **Connection Drops:** DataAdapter จัดการ reconnect อัตโนมัติ
- **Queue Full:** จัดการการ overflow ดี
- **Write Errors:** Retry mechanism มี

### **Data Integrity:**
- **RAM + Disk:** 2 แหล่งเก็บข้อมูล (หนึ่งใน RAM, หนึ่งใน Disk)
- **Validation:** ตรวจสอบก่อนบันทึกทุกครั้ง
- **Monitoring:** เฝ้าระวังประสิทธิภาพตลอด

---

## 📈 **สถานะปัจจุบัน:**

### **✅ การส่งข้อมูล:**
- **Controller:** DataAdapter ควบคุมได้ดี
- **Memory:** บันทึกใน RAM อย่างมีประสิทธิภาพ
- **Disk:** Async CSV Writing ไม่ block main thread
- **Queue:** Non-blocking processing ดี

### **✅ การบันทึก:**
- **Primary:** In-Memory Storage (RAM) - ใช้งานจริง
- **Secondary:** CSV Files (Disk) - Backup และ Historical data
- **Format:** Append-only CSV พร้อม Date-based organization

### **🎯 สรุป:**
**DataAdapter เป็นสมองกลางควบคุมการส่งข้อมูล โดยเก็บข้อมูลหลักใน RAM และบันทึกลง Disk แบบ Async ผ่าน Queue System ทำให้ระบบทำงานได้เร็วและมีประสิทธิภาพ** 🚀💾

---
**สร้างเมื่อ:** 2024-01-13  
**สถานะ:** ✅ ใช้งานได้เต็มรูปแบบ  
**ความพร้อม:** 🚀 พร้อมการใช้งานจริง