**:Market Ingestion (Data Feed)**

---

data\_source.py

หน้าที่: กำหนด Interface มาตรฐานของแหล่งข้อมูล (Data Source Contract)

เช่น: connect(), disconnect(), subscribe(), unsubscribe(), get\_candles()

ออกแบบมาเพื่อรองรับหลาย Broker ในอนาคต



iq\_option\_adapter.py

หน้าที่: เชื่อมต่อ IQ Option โดยเฉพาะ

ทำหน้าที่: Login, Reconnect, Subscribe, Download OHLCV

แปลง API ของ IQ Option ให้เป็นมาตรฐานของระบบ



data\_adapter.py

หน้าที่: แปลงข้อมูลดิบจาก Broker เป็น Standard Candle Model

ฟังก์ชัน: Mapping Field, Timestamp, Symbol, Timeframe, Type Conversion



timeframe\_sync.py

หน้าที่: จัดการ Timeframe (M1, M5, M15)

ตรวจจับการปิดแท่ง (Bar Close)

Synchronize เวลา

Trigger เมื่อแท่งสมบูรณ์



candle\_validator.py

หน้าที่: ตรวจสอบคุณภาพข้อมูลก่อนใช้งาน

เช็ค: Missing Candle, Duplicate, Timestamp, OHLC ถูกต้อง, Volume, Timeframe Alignment



csv\_queue.py

หน้าที่: Queue สำหรับรับ Candle

แยกการรับข้อมูลออกจากการเขียนไฟล์

ป้องกันการ Block เมื่อหลายคู่เงินปิดแท่งพร้อมกัน



csv\_writer.py

หน้าที่: เขียนข้อมูลลงไฟล์ CSV

เขียนแบบ Append Only (ไม่ลบข้อมูลเก่า)



csv\_manager.py

หน้าที่: จัดการไฟล์ CSV

สร้างโฟลเดอร์, ตั้งชื่อไฟล์, แยกตาม Symbol/Timeframe/วันที่

File Rotation

ตรวจสอบไฟล์



data\_monitor.py

หน้าที่: เฝ้าระวังการทำงานของ Data Module

เช็ค: Connection Status, Missing Candle, Queue Length, Write Error, Latency

แจ้งเตือนเมื่อเกิดปัญหา

