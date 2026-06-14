TASK FOR CLAUDE.AI — POST-BLUEPRINT PHASE (CRITICAL)

ตอนนี้ Blueprint ของ Trading Intelligence Platform ถูกออกแบบครบแล้ว (Market Intelligence + Engines + Scoring + Strategy Layer)

ขั้นตอนต่อไปที่ต้องทำ “ไม่ใช่การเพิ่มความคิด” แต่คือการ “แปลงเป็นระบบที่ทำงานได้จริง”

ให้ Claude ทำสิ่งต่อไปนี้:

1) FREEZE ARCHITECTURE
- ห้ามเพิ่ม modules ใหม่
- ห้ามเพิ่ม indicators ใหม่
- ใช้เฉพาะ engine ที่มีใน blueprint เท่านั้น

2) BUILD CORE SKELETON (PYTHON)
- สร้าง project structure ทั้งระบบ
- สร้าง base classes ของทุก engine
- สร้าง shared context object (central state)
- สร้าง standard input/output schema ของ engine

3) IMPLEMENT DATA FLOW PIPELINE
- candle data → ingestion layer
- ingestion → context builder
- context → engines (parallel execution)
- engines → scoring aggregator
- aggregator → strategy interface

4) IMPLEMENT ENGINE INTERFACES (EMPTY LOGIC FIRST)
- Structure Engine
- Volatility Engine
- Liquidity Engine
- Market State Classifier
- Price Action Engine
- Quality Scorer

หมายเหตุ: ยังไม่ต้องใส่ logic ลึก ให้ทำแค่ framework + input/output contract

5) BUILD CONTEXT SYSTEM (CRITICAL)
- shared market context object
- versioned state tracking
- engine-to-engine communication rules
- conflict detection placeholder

6) BUILD SCORING PIPELINE
- raw engine outputs → normalized scores
- conflict resolution layer
- final market quality score
- signal eligibility flag (ALLOW / BLOCK)

7) STRATEGY LAYER (PLUG-IN ONLY)
- strategy must NOT contain market logic
- strategy only consumes context + scores
- implement 1 sample strategy: "5M Volatility Compression Breakout"

8) VALIDATION REQUIREMENT
- system must run end-to-end with dummy data
- must output structured context + score
- must show block/allow decision

OUTPUT EXPECTATION:
- clean modular python architecture
- fully separated layers
- no circular dependency
- deterministic data flow

GOAL:
Turn blueprint into executable trading intelligence framework skeleton
NOT a trading bot
NOT a strategy script