Markdown# ทักษะการเทรดสำหรับ Claude (Claude Trading Skills)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.md)
[![Skills](https://img.shields.io/badge/Skills-67-brightgreen.svg)](#-สิ่งที่รวมอยู่ด้วย)
[![Agent Skills](https://img.shields.io/badge/Standard-Agent_Skills-blueviolet.svg)](https://agentskills.io)
[![Works with](https://img.shields.io/badge/Works_with-Claude_Code_|_Cursor_|_Codex_|_Gemini_CLI-blue.svg)](#-เริ่มต้นการใช้งาน)

แหล่งรวบรวม **[Agent Skills](https://agentskills.io) สำหรับการเทรด, DeFi และ Quantitative Finance ที่พร้อมใช้งานกว่า 67 รายการ** ใช้งานได้กับ Claude Code, Cursor, Codex, Gemini CLI และ [เครื่องมืออื่นๆ อีกกว่า 30 ชนิด](https://agentskills.io) เปลี่ยน AI agent ของท่านให้เป็นนักวิเคราะห์การเทรดที่สามารถรันเวิร์กโฟลว์หลายขั้นตอนที่ซับซ้อน ครอบคลุมตั้งแต่การวิเคราะห์ข้อมูลตลาด, การวิจัย On-chain, การทดสอบกลยุทธ์ย้อนหลัง (Backtesting), การจัดการความเสี่ยง, การจัดการภาษี และอื่นๆ อีกมากมาย

**เน้น Crypto/DeFi เป็นหลัก และสามารถนำไปประยุกต์ใช้ได้กับ Quant finance ทุกรูปแบบ**

> 🙌 **ร่วมเพิ่มทักษะของท่าน — ยินดีรับ Pull Requests!** คอลเลกชันนี้เติบโตขึ้นจากประสบการณ์การเทรดและการวิจัยจริงของชุมชน **หากท่านสร้างสิ่งที่เป็นประโยชน์?** ไม่ว่าจะเป็นกระดานเทรดหรือเชนใหม่ๆ, ประเภทตลาด, แหล่งข้อมูล, กลยุทธ์ หรือบทเรียนล้ำค่าที่ได้เรียนรู้ — **[เปิด PR ได้เลย](CONTRIBUTING.md)** และมาร่วมแบ่งปันกัน กติกาง่ายๆ: แค่มีไฟล์ `SKILL.md` ที่ใช้งานได้ตามรูปแบบ [Agent Skills](https://agentskills.io) พร้อมคำแนะนำที่ผ่านการทดสอบและเชื่อถือได้ (ดู **[CONTRIBUTING.md](CONTRIBUTING.md)**) ทุกการมีส่วนร่วมจะช่วยให้ชุมชนทั้งหมดเทรดได้อย่างชาญฉลาดยิ่งขึ้น

<p align="center">
  <img src="claude-trading-skills.gif" alt="Claude Trading Skills Demo" width="800"/>
</p>

> ⚠️ **ข้อจำกัดความรับผิดชอบ (Disclaimer)**: นี่คือเครื่องมือสำหรับการวิเคราะห์และการวิจัย ผลลัพธ์ที่ได้จากทักษะเหล่านี้ไม่ถือเป็นคำแนะนำทางการลงทุน โปรดศึกษาข้อมูลด้วยตัวท่านเอง (DYOR) เสมอ

> ⭐ **หากท่านพบว่า Repository นี้มีประโยชน์** โปรดพิจารณากดให้ดาว! เพื่อช่วยให้ผู้อื่นค้นพบเครื่องมือเหล่านี้และสนับสนุนการพัฒนาอย่างต่อเนื่อง

---

## 📋 สารบัญ

- [เหตุผลที่ควรใช้งาน](#-เหตุผลที่ควรใช้งาน)
- [สิ่งที่รวมอยู่ด้วย](#-สิ่งที่รวมอยู่ด้วย)
- [เริ่มต้นการใช้งาน](#-เริ่มต้นการใช้งาน)
- [ตัวอย่างการใช้งานฉับไว](#-ตัวอย่างการใช้งานฉับไว)
- [ข้อกำหนดเบื้องต้น](#-ข้อกำหนดเบื้องต้น)
- [ทักษะที่มีให้ใช้งาน](#-ทักษะที่มีให้ใช้งาน)
- [การมีส่วนร่วม](#-การมีส่วนร่วม)
- [การแก้ไขปัญหา](#-การแก้ไขปัญหา)
- [คำถามที่พบบ่อย (FAQ)](#-คำถามที่พบบ่อย-faq)
- [การอ้างอิง](#-การอ้างอิง)
- [ใบอนุญาต](#-ใบอนุญาต)

---

## 🚀 เหตุผลที่ควรใช้งาน

### ⚡ ยกระดับความเร็วในการวิจัย
- **ข้ามขั้นตอนการเขียน API boilerplate** — ทักษะต่างๆ จัดการการเชื่อมต่อกับ Birdeye, DexScreener, Jupiter, Helius, CoinGecko และ DeFiLlama ให้เรียบร้อย
- **โค้ดพร้อมใช้งานจริง (Production-ready)** — รูปแบบโค้ดที่ผ่านการทดสอบมาแล้วสำหรับการทำ Backtesting, การจัดการความเสี่ยง และการวิเคราะห์พอร์ตโฟลิโอ
- **เวิร์กโฟลว์แบบหลายขั้นตอน** — รวบรวมข้อมูล → วิเคราะห์ → สร้างกราฟ จบใน Prompt เดียว

### 🎯 ครอบคลุมทุกมิติ
- **67 ทักษะ** ใน 17 หมวดหมู่ที่ครอบคลุมขั้นตอนการเทรดทั้งหมด
- **API ข้อมูลตลาด 7 ตัว** — แหล่งข้อมูลทั้งบน Solana และข้ามเชน
- **เครื่องมือโครงสร้างพื้นฐาน Solana 6 ตัว** — สำหรับ Stream แบบเรียลไทม์, Shreds, Bundles, DEX aggregation และการสร้างธุรกรรม
- **เครื่องมือวิเคราะห์ On-Chain 5 ตัว** — สำหรับการวิเคราะห์กระเป๋า, ติดตามวาฬ (Whale tracking), ตรวจจับ Sybil และวิเคราะห์สภาพคล่อง
- **สถิติ + Machine Learning** — วิธีการที่สร้างมาเพื่อการเทรดโดยเฉพาะ
- **เครื่องมือภาษี & Compliance 7 ตัว** — สำหรับคำนวณต้นทุน, Wash sales, Tax-loss harvesting และการทำรายงาน

### 🔧 ผสานการทำงานได้ง่าย
- **ติดตั้งในคลิกเดียว** ผ่านปลั๊กอิน Claude Code หรือคัดลอกด้วยตัวเองสำหรับเครื่องมือใดๆ ที่รองรับ [Agent Skills](https://agentskills.io)
- **ค้นพบอัตโนมัติ** — Agent ของท่านจะค้นหาและใช้งานทักษะที่เกี่ยวข้องตามคำสั่งของท่านโดยอัตโนมัติ
- **ขยายความสามารถได้** — สามารถเพิ่มทักษะด้านหุ้น (Equities), ออปชั่น (Options) และฟิวเจอร์ส (Futures) ในรูปแบบเดียวกันได้

---

## 📦 สิ่งที่รวมอยู่ด้วย

### หมวดหมู่ทักษะ

| หมวดหมู่ | จำนวนทักษะ | คำอธิบาย |
|----------|--------|-------------|
| 📊 **ข้อมูลตลาด & APIs** | 7 | Birdeye, DexScreener, SolanaTracker, CoinGecko, Helius, Solana RPC, DeFiLlama |
| 🔌 **โครงสร้างพื้นฐาน Solana** | 6 | กลไก PumpFun, การสร้างธุรกรรม, Yellowstone gRPC, ShredStream, Jito bundles, Raptor DEX aggregator |
| 🔗 **การวิเคราะห์ On-Chain** | 5 | การวิเคราะห์กระเป๋า, วิเคราะห์ผู้ถือครอง, ติดตามวาฬ, สภาพคล่อง, ตรวจจับ Sybil |
| 📈 **การวิเคราะห์ทางเทคนิค** | 3 | pandas-ta, TA-Lib, อินดิเคเตอร์เฉพาะสำหรับคริปโต |
| 🔄 **Backtesting & กลยุทธ์** | 4 | vectorbt, Backtrader, โครงสร้างกลยุทธ์, Walk-forward validation |
| ⚖️ **พอร์ตโฟลิโอ & ความเสี่ยง** | 4 | การวิเคราะห์พอร์ตโฟลิโอ, การกำหนดขนาด Position, การจัดการความเสี่ยง, Kelly criterion |
| 🏦 **เฉพาะกลุ่ม DeFi** | 6 | คณิตศาสตร์ LP, Impermanent loss, วิเคราะห์ผลตอบแทน, MEV, Tokenomics, วิเคราะห์ DEX pool |
| 📐 **วิธีการทางสถิติ** | 5 | ตรวจจับ Regime, โมเดลความผันผวน, Cointegration, Mean reversion, Correlation |
| 🤖 **ML สำหรับการเทรด** | 4 | การแยกประเภทสัญญาณ (Signal classification), Feature engineering, การส่งคำสั่งด้วย RL, วิเคราะห์ความรู้สึก (Sentiment) |
| ⚡ **การส่งคำสั่ง & การเทรด** | 4 | ส่งคำสั่ง DEX, โมเดล Slippage, Copy-trading, กลยุทธ์การทำกำไร/ตัดขาดทุน (Exit) |
| 📉 **ข้อมูล & การทำภาพจำลอง** | 3 | กราฟเทรด, การประมวลผล OHLCV, บันทึกการเทรด (Journal) |
| 🔬 **โครงสร้างตลาดจุลภาค (Microstructure)** | 2 | วิเคราะห์ Orderflow บน DEX, ทฤษฎี LOB แบบดั้งเดิม, Market making |
| 🔮 **Quant Finance** | 2 | การตั้งราคาออปชั่น, ตราสารหนี้ (Fixed income) |
| 🗳️ **ตลาดคาดการณ์ (Prediction Markets)** | 5 | Kalshi & Polymarket API, ตลาดคาดการณ์สภาพอากาศ + กรอบราคาคริปโต/ดัชนี, กลยุทธ์/การกำหนดขนาด/Backtesting แบบ Cross-cutting |
| 🧾 **ภาษี, บัญชี & Compliance** | 7 | ต้นทุน, Wash sales, Tax-loss harvesting, นำออกข้อมูล, ทำบัญชี, ทำรายงาน |

ทักษะแต่ละตัวประกอบด้วย:
- ✅ เอกสารประกอบครบถ้วน (`SKILL.md`)
- ✅ ตัวอย่างโค้ดที่รันได้จริง
- ✅ Use cases และคำแนะนำในการนำไปใช้
- ✅ ข้อมูลอ้างอิงในแฟ้ม `references/`

---

## 🎯 เริ่มต้นการใช้งาน

Repository นี้ปฏิบัติตามมาตรฐาน [Agent Skills](https://agentskills.io) ที่เป็นแบบเปิด และสามารถใช้ได้กับ Agent ใดๆ ที่รองรับ

### ตัวเลือก A: ปลั๊กอิน Claude Code (แนะนำ)

วิธีติดตั้งที่เร็วที่สุด (ต้องใช้ Claude Code v1.0.33+)

**ขั้นตอนที่ 1: เพิ่ม Marketplace**

/plugin marketplace add agiprolabs/claude-trading-skills
**ขั้นตอนที่ 2: ติดตั้งปลั๊กอิน**

/plugin install trading-skills@agiprolabs-claude-trading-skills
**เสร็จสิ้น!** ตอนนี้ทักษะทั้ง 67 ตัวพร้อมใช้งานแล้ว Claude จะค้นพบและใช้งานทักษะเหล่านี้โดยอัตโนมัติเมื่อเกี่ยวข้องกับงานเทรดของท่าน โดยจะใช้ชื่อ (Namespace) ในรูปแบบ `/trading-skills:skill-name`

**การจัดการปลั๊กอิน:**

/plugin                                                    # ดูปลั๊กอินที่ติดตั้งไว้/plugin disable trading-skills@agiprolabs-claude-trading-skills   # ปิดใช้งาน/plugin enable trading-skills@agiprolabs-claude-trading-skills    # เปิดใช้งานอีกครั้ง/plugin uninstall trading-skills@agiprolabs-claude-trading-skills # ถอนการติดตั้ง/reload-plugins                                            # อัปเดตการเปลี่ยนแปลงโดยไม่ต้องรีสตาร์ท
### ตัวเลือก B: คัดลอกด้วยตัวเอง (สำหรับเครื่องมือที่รองรับ Agent Skills)

ใช้งานได้กับ Claude Code, Cursor, Codex, Gemini CLI และ [เครื่องมืออื่นๆ กว่า 30 ชนิด](https://agentskills.io)

**ขั้นตอนที่ 1: Clone repository**

```bash
git clone [https://github.com/agiprolabs/claude-trading-skills.git](https://github.com/agiprolabs/claude-trading-skills.git)
ขั้นตอนที่ 2: คัดลอกโฟลเดอร์ทักษะไปยังไดเรกทอรีทักษะของ Agent ของท่านขอบเขตClaude CodeCursorCodexGemini CLIระดับ Global (ทุกโปรเจกต์)~/.claude/skills/~/.cursor/skills/~/.codex/skills/~/.gemini/skills/ระดับ Project (โปรเจกต์เดียว).claude/skills/.cursor/skills/.codex/skills/.gemini/skills/Bash# ติดตั้งแบบ Global — เลือกเครื่องมือของท่าน:
cp -r claude-trading-skills/skills/* ~/.claude/skills/   # Claude Code
cp -r claude-trading-skills/skills/* ~/.cursor/skills/   # Cursor
cp -r claude-trading-skills/skills/* ~/.codex/skills/    # Codex
cp -r claude-trading-skills/skills/* ~/.gemini/skills/   # Gemini CLI

# หรือติดตั้งระดับโปรเจกต์ (ตัวอย่าง Claude Code):
mkdir -p .claude/skills
cp -r /path/to/claude-trading-skills/skills/* .claude/skills/
Agent ของท่านจะค้นพบทักษะอัตโนมัติและเรียกใช้เมื่อเกี่ยวข้องกับคำสั่งการเทรดของท่านหมายเหตุ: Agent Skills รองรับในเครื่องมือกว่า 30 ชนิด เช่น Claude Code, Cursor, Codex, Gemini CLI, VS Code Copilot, Roo Code, Goose, OpenHands และอื่นๆ สามารถดูรายชื่อทั้งหมดได้ที่ agentskills.io💡 ตัวอย่างการใช้งานฉับไว🔍 เจาะลึกข้อมูล Token (Token Deep Dive)ใช้ทักษะที่มีอยู่ ช่วยวิเคราะห์ Solana token นี้: [MINT_ADDRESS] ดึงข้อมูลราคาและปริมาณการซื้อขายปัจจุบัน
จาก Birdeye, ตรวจสอบการกระจายตัวของผู้ถือครองและสัดส่วนของผู้ถือครองสูงสุด 10 อันดับแรก, วิเคราะห์ความลึก
ของสภาพคล่องใน DEX pools ต่างๆ, คำนวณ RSI/MACD/BBands บนแท่งเทียน 1 ชม., ประเมิน slippage 
สำหรับการเข้าซื้อด้วย 0.5 SOL และช่วยประเมินความเสี่ยงพร้อมเสนอขนาด position ที่เหมาะสม โดยสมมติ
ว่ารับความเสี่ยงได้ 2% ของพอร์ต
ทักษะที่ใช้: birdeye-api, token-holder-analysis, liquidity-analysis, dex-pool-analysis, pandas-ta, slippage-modeling, risk-management, position-sizing📊 ทดสอบกลยุทธ์ย้อนหลัง (Strategy Backtest)ใช้ทักษะที่มีอยู่ ช่วยทำ Backtest กลยุทธ์ RSI mean-reversion แบบง่ายบนคู่เหรียญ SOL/USDC 
กราฟ 1 ชม. ย้อนหลัง 6 เดือน เข้าซื้อเมื่อ RSI(14) < 30 และออกเมื่อ RSI > 70 ใช้ความเสี่ยง 1% 
ต่อการเทรด พร้อมตั้ง Stop loss ที่ ATR(14)*2 ขอดู Equity curve, กราฟ Drawdown และ
ตัวชี้วัดสำคัญ (Sharpe, max DD, win rate, profit factor)
ทักษะที่ใช้: birdeye-api, ohlcv-processing, pandas-ta, vectorbt, portfolio-analytics, trading-visualization🏦 เปรียบเทียบผลตอบแทน DeFi (DeFi Yield Comparison)ใช้ทักษะที่มีอยู่ เปรียบเทียบโอกาสรับผลตอบแทนของ SOL บน Raydium, Orca และ Meteora LP pools 
คำนวณ Impermanent loss หากราคาขยับ ±25% และ ±50% แสดงค่า Net APY หลังหัก IL สำหรับ 
แต่ละ pool และจัดอันดับตามผลตอบแทนที่ปรับความเสี่ยงแล้ว รวมถึงประเมินความเสี่ยงจาก MEV ด้วย
ทักษะที่ใช้: defillama-api, dex-pool-analysis, lp-math, impermanent-loss, yield-analysis, mev-analysis, trading-visualization🐋 การตรวจสอบวาฬ (Whale Monitoring)ใช้ทักษะที่มีอยู่ วิเคราะห์ผู้ถือครอง 20 อันดับแรกของ [TOKEN_MINT] ค้นหาว่ากระเป๋าใดที่มีการสะสม
(Accumulating) ในช่วง 7 วันที่ผ่านมา ตรวจสอบว่ามีกระเป๋าใดเป็นเทรดเดอร์ที่เคยทำกำไรได้ดีหรือไม่ 
แสดงการกระจายตัวของผู้ถือครองด้วยค่า Gini coefficient และแจ้งเตือนหากมีความเสี่ยงเรื่อง
การกระจุกตัวของเหรียญ
ทักษะที่ใช้: helius-api, token-holder-analysis, whale-tracking, solana-onchain, trading-visualization🧾 การจัดการ Position โดยคำนึงถึงภาษีใช้ทักษะที่มีอยู่ ฉันกำลังติดตามต้นทุนสำหรับการเทรด SOL โดยใช้วิธีต้นทุนเฉลี่ย (proportional) 
สำหรับกลยุทธ์ accumulate/house-money ของฉัน ฉันซื้อ 10 SOL ที่ $150 จากนั้นซื้อ 5 SOL 
ที่ $180 ตอนนี้ฉันต้องการขาย 3 SOL ที่ $200 ช่วยคำนวณต้นทุน (Cost basis), กำไรที่รับรู้ 
(Realized gain) และจำนวนคงเหลือ จากนั้นตรวจสอบว่าการขายล่าสุดของฉันเข้าข่าย Wash sale 
หรือไม่ และแสดงตัวอย่างรายการบน Form 8949 ส่งออกผลลัพธ์ในรูปแบบที่เข้ากันได้กับ Koinly
ทักษะที่ใช้: cost-basis-engine, tax-liability-tracking, wash-sale-detection, crypto-tax-export, regulatory-reporting🤖 ไปป์ไลน์ ML Signalใช้ทักษะที่มีอยู่ สร้างชุด Feature สำหรับ [TOKEN] โดยใช้ข้อมูล OHLCV 1 ชม.: RSI, MACD, 
ความกว้าง Bollinger Band, สัดส่วนปริมาณการซื้อขาย และโมเมนตัมจำนวนผู้ถือครอง 
ฝึกสอน (Train) XGBoost classifier เพื่อทำนายผลตอบแทน >2% ในอีก 4 ชั่วโมงข้างหน้า 
ใช้ Walk-forward validation โดยมีระยะเวลา Train 30 วันและ Test 7 วัน แสดง 
Feature importance และ Classification metrics 
ทักษะที่ใช้: birdeye-api, ohlcv-processing, pandas-ta, custom-indicators, feature-engineering, signal-classification, trading-visualization⚙️ ข้อกำหนดเบื้องต้นPython: 3.9+ (แนะนำ 3.12+)uv: Python package manager (จำเป็นสำหรับการติดตั้ง dependencies ของทักษะ)Client: Agent ใดๆ ที่รองรับมาตรฐาน Agent Skills (เช่น Claude Code, Cursor, Codex, Gemini CLI เป็นต้น)ระบบปฏิบัติการ: macOS, Linux หรือ Windows พร้อม WSL2API Keys (ตามความจำเป็น):Birdeye (ฟรีที่ birdeye.so)Helius (ฟรีที่ helius.dev)CoinGecko Pro (ทางเลือก, แบบฟรีจะมีการจำกัดการเรียกใช้งาน)Dependencies: มีการจัดการอัตโนมัติแยกตามแต่ละทักษะ (ตรวจสอบข้อกำหนดเฉพาะในไฟล์ SKILL.md แต่ละตัว)การติดตั้ง uvBash# macOS / Linux
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"

# ตรวจสอบการติดตั้ง
uv --version
📚 ทักษะที่มีให้ใช้งาน📊 ข้อมูลตลาด & APIs (7 ทักษะ)birdeye-api — ข้อมูลโทเค็น Solana: ราคา, OHLCV, วอลุ่ม, Metadata, กิจกรรมของเทรดเดอร์dexscreener-api — ข้อมูลคู่เทรด DEX ข้ามเชน, ไม่ต้องใช้ API keysolanatracker-api — ข้อมูลโทเค็น Solana, โทเค็นที่เรียนจบ (Graduating), การเชื่อมต่อกับ PumpFuncoingecko-api — ข้อมูลตลาดคริปโตแบบกว้าง: โทเค็น 13,000+ ตัว, สถิติระดับโลก, ข้อมูลย้อนหลังhelius-api — Enhanced Solana RPC: ธุรกรรมที่ Parsed แล้ว, DAS, Webhookssolana-rpc — โต้ตอบโดยตรงกับ Solana blockchain ผ่าน JSON-RPCdefillama-api — วิเคราะห์ DeFi: TVL, ผลตอบแทน (Yields), วอลุ่ม, ค่าธรรมเนียม, สะพาน (Bridges)🔌 โครงสร้างพื้นฐาน Solana (6 ทักษะ)pumpfun-mechanics — คำนวณ Bonding curve, การจบหลักสูตร (Graduation), การย้าย, การแยกเหตุการณ์ (Event parsing)solana-tx-building — ธุรกรรมแบบ Versioned, ค่าธรรมเนียม Priority, งบประมาณ Compute, ALTsyellowstone-grpc — รับข้อมูล Solana แบบเรียลไทม์ผ่าน Yellowstone gRPC (Geyser)shredstream — Jito ShredStream เพื่อเข้าถึงข้อมูล Shred ล่วงหน้าก่อนเปิดบล็อก (ได้เปรียบ ~200-400ms)jito-bundles — ส่ง Bundle เพื่อป้องกัน MEV, กลยุทธ์การให้ทิป, Block engine APIraptor-dex — DEX aggregator ที่โฮสต์เอง: รองรับ 25+ DEXes, ไม่มี Rate limits, Yellowstone Jet TPU🔗 การวิเคราะห์ On-Chain (5 ทักษะ)token-holder-analysis — การกระจายตัวของผู้ถือครอง, การกระจุกตัว, การตรวจจับคนใน (Insider)whale-tracking — ติดตามกระเป๋าขนาดใหญ่, ตรวจจับการสะสม/กระจายเหรียญliquidity-analysis — วิเคราะห์ความลึก, Pool TVL, การประเมิน Slippage, องค์ประกอบ LPwallet-profiling — จัดประเภทพฤติกรรมกระเป๋า, Win rate, ติดตาม PnL, วิเคราะห์สไตล์การเทรดsybil-detection — จัดกลุ่มพฤติกรรมการเทรดร่วมกัน, ตรวจจับ Wash trading, วิเคราะห์ Bundler📈 การวิเคราะห์ทางเทคนิค (3 ทักษะ)pandas-ta — อินดิเคเตอร์ 130+ ตัว: RSI, MACD, Bollinger Bands, SuperTrend, Ichimoku ฯลฯta-lib — อินดิเคเตอร์ที่ปรับจูนด้วยภาษา C + ฟังก์ชันจดจำรูปแบบแท่งเทียน 61 รูปแบบcustom-indicators — เฉพาะคริปโต: NVT, MVRV, Exchange flow, สัญญาณ Funding rate🔄 Backtesting & กลยุทธ์ (4 ทักษะ)vectorbt — Backtesting แบบ Vectorized ประสิทธิภาพสูงพร้อมการปรับจูนพารามิเตอร์ (Optimization)backtrader — Backtesting แบบอิงเหตุการณ์ (Event-driven) พร้อมประเภทคำสั่งที่หลากหลายและตัววิเคราะห์strategy-framework — เทมเพลตมาตรฐานในการระบุและจัดทำเอกสารกลยุทธ์walk-forward-validation — การทดสอบโมเดลตามกรอบเวลา (Time-series), ตรวจจับ Overfit, CPCV⚖️ พอร์ตโฟลิโอ & ความเสี่ยง (4 ทักษะ)portfolio-analytics — Sharpe, Sortino, Calmar, Max drawdown, Quantstats reportsposition-sizing — สัดส่วนคงที่แบบ Fractional, ปรับตามความผันผวน, การหาขนาดด้วย Kellyrisk-management — ควบคุมระดับพอร์ตโฟลิโอ: ลิมิต Drawdown, ความเกี่ยวพัน (Correlation), Circuit breakerskelly-criterion — หาขนาดที่เหมาะสมที่สุดด้วย Fractional Kelly รูปแบบต่างๆ🏦 เฉพาะกลุ่ม DeFi (6 ทักษะ)lp-math — คณิตศาสตร์ AMM: Constant product, CLMM, Price impact, สัดส่วน LPimpermanent-loss — คำนวณ IL, จุดคุ้มทุน IL กับค่าธรรมเนียม, การขยาย IL ใน CLMMyield-analysis — ผลตอบแทนที่แท้จริงเทียบกับหน้าป้าย, Net APY, ความยั่งยืนของการจ่ายรางวัล (Emission)mev-analysis — ตรวจจับ Sandwich, ความเสี่ยง Front-running, กลไก Solana MEVtoken-economics — สร้างแบบจำลองอุปทาน, Vesting, เงินเฟ้อ, กรอบการประเมินมูลค่าdex-pool-analysis — กลไก AMM pool, วิเคราะห์ค่าธรรมเนียม, การเปรียบเทียบ Pool ระหว่าง DEXes📐 วิธีการทางสถิติ (5 ทักษะ)regime-detection — HMM, การตรวจจับจุดเปลี่ยน (Change-point), การเกาะกลุ่มความผันผวนvolatility-modeling — GARCH, EWMA, Realized volatility, Volatility conescointegration-analysis — Engle-Granger, Johansen, Rolling cointegrationmean-reversion — Hurst exponent, Half-life, Z-score signals, การทดสอบ ADFcorrelation-analysis — Rolling correlation, Hierarchical clustering, Tail dependence🤖 ML สำหรับการเทรด (4 ทักษะ)signal-classification — ตัวจำแนก XGBoost/LightGBM พร้อม Walk-forward validationfeature-engineering — การคำนวณ Feature จากข้อมูล OHLCV, On-chain และข้อมูลทางเลือกrl-execution — ใช้ Reinforcement learning (RL) เพื่อปรับการส่งคำสั่งให้ได้ราคาที่ดีที่สุดsentiment-analysis — ดึงความรู้สึกจากโซเชียล/ข่าวสาร และสร้างสัญญาณซื้อขาย⚡ การส่งคำสั่ง & การเทรด (4 ทักษะ)dex-execution — ส่งคำสั่ง DEX swap ผ่าน Jupiter aggregator (⚠️ จำเป็นต้องได้รับการยืนยันจากผู้ใช้)slippage-modeling — ประมาณการต้นทุนส่งคำสั่ง และหาขนาดการเทรดที่ดีที่สุดcopy-trading — ค้นหากระเป๋าผู้นำ, ติดตามขนาด (Follow sizing), เลียนแบบการตัดขาย (Exit)exit-strategies — แบ่งเป้าหมายการทำกำไร (Tiered), Trailing stops, การออกตามเวลา และตามสัญญาณ📉 ข้อมูล & การทำภาพจำลอง (3 ทักษะ)trading-visualization — แท่งเทียน, Equity curves, Drawdowns, Heatmapsohlcv-processing — ทำความสะอาดข้อมูล, Resampling, จัดการช่วงว่างข้อมูล, ทำให้เป็นมาตรฐานtrade-journal — บันทึกการเทรดอย่างเป็นระบบและทบทวนผลงาน🔬 โครงสร้างตลาดจุลภาค (Microstructure) (2 ทักษะ)market-microstructure — วิเคราะห์ DEX orderflow, จำแนกการเทรด, Volume profiles, ตรวจจับ Wash tradingmarket-microstructure-traditional — ทฤษฎี LOB, แยกระยะห่างราคา (Spread), Market making, เทียบ CEX กับ DEX🔮 Quantitative Finance (2 ทักษะ)options-pricing — Black-Scholes, Greeks, กราฟความผันผวน (Implied vol surfaces), คริปโตออปชั่นfixed-income — การตั้งราคาพันธบัตร, Yield curves, วิเคราะห์อัตราดอกเบี้ยยืมบน DeFi🗳️ ตลาดคาดการณ์ (Prediction Markets) (5 ทักษะ)kalshi-api — กลไกตลาด Kalshi: Host, RSA-PSS auth, โครงสร้าง Dollar-string order, ระเบียบ YES/NO order-book, แท่งเทียน, การค้นหาผ่าน WebSocket, Rate limits, Lifecycle gotchas (เอกสารมาตรฐาน + verify-first)polymarket-api — กลไกตลาด Polymarket: Gamma/CLOB/Data APIs, EIP-712 auth, โมเดลโทเค็น ERC-1155, WebSocket, การแลกรับ On-chain, ข้อพิพาท UMA, US geo/KYC (เอกสารมาตรฐาน + verify-first)kalshi-weather-markets — การทายผลอุณหภูมิสูงสุด/ต่ำสุดรายวัน และ Thresholds: คาดการณ์สภาพอากาศ→P(YES) แผนที่ Gaussian, การชำระบัญชีผ่าน NWS-CLI/LST, ความแตกต่างของสถานี/DST, การปรับแก้ Bias ของ CLI-spacekalshi-crypto-index-markets — ตลาดกรอบราคาแบบรายวัน/รายชั่วโมงของ BTC/ETH & S&P/Nasdaq: โครงสร้างวงเล็บกรอบราคา, การจำลอง σ-from-volatility, การตัดสินใจปิดในช่วงหมดเวลา, การชำระบัญชีตามผลลัพธ์prediction-market-strategy — ครอบคลุม: ส่วนต่างความได้เปรียบแบบ Favorite-longshot maker, การกำหนดขนาดและการเลือกเข้าเทรดแบบคำนึงถึงค่าธรรมเนียม, วิธีการ Backtesting (the phantom-edge hall of fame) และเอกสารที่เกี่ยวข้อง🧾 ภาษี, บัญชี & Compliance (7 ทักษะ)tax-liability-tracking — ติดตามกำไร/ขาดทุนแบบเรียลไทม์ต่อการเทรดและทั้งพอร์ตโฟลิโอcost-basis-engine — วิธีต้นทุน FIFO, LIFO, HIFO, Specific ID, และต้นทุนถัวเฉลี่ยwash-sale-detection — สแกนหารายการ Wash sale ในช่วงเวลา 61 วันภายใต้กฎภาษีคริปโตปี 2025 ของสหรัฐฯtax-loss-harvesting — ให้คะแนนโอกาส, เสนอสินทรัพย์ทดแทน, ปฏิบัติตามกฎ Wash salecrypto-tax-export — นำออกข้อมูลไป Koinly, CoinTracker, TurboTax และฟอร์ม 8949 เป็น CSVtrade-accounting — การทำบัญชีคู่ (Double-entry) สำหรับการดำเนินงานการเทรดregulatory-reporting — สร้าง Form 8949, Schedule D, FBAR และตรวจสอบความถูกต้อง📖 สำหรับเอกสารประกอบฉบับเต็มของทุกทักษะ สามารถอ่านได้ที่ trading-skills.md🤝 การมีส่วนร่วมเรายินดีต้อนรับทุกการมีส่วนร่วม! ยังมีพื้นที่สำหรับทักษะใหม่ๆ อีกมากมายที่ครอบคลุมถึงเชนอื่นๆ, การเชื่อมต่อ CEX และกลยุทธ์ชั้นสูงต่างๆวิธีการมีส่วนร่วมFork พื้นที่เก็บข้อมูล (Repository)สร้าง แบรนช์ฟีเจอร์ใหม่ (git checkout -b feature/amazing-skill)ปฏิบัติตาม โครงสร้างไดเรกทอรีและรูปแบบเอกสารที่มีอยู่เดิมตรวจสอบ ให้แน่ใจว่าทักษะใหม่ทั้งหมดมีไฟล์ SKILL.md ที่ครบถ้วนพร้อม Frontmatter ที่ถูกต้องทดสอบ ตัวอย่างและสคริปต์ของท่านอย่างถี่ถ้วน (ให้รวมโหมด --demo เข้าไปด้วย)Commit การเปลี่ยนแปลงของท่าน (git commit -m 'Add amazing skill')Push ไปที่แบรนช์ของท่าน (git push origin feature/amazing-skill)ส่ง (Submit) Pull request พร้อมคำอธิบายที่ชัดเจนเกี่ยวกับการเปลี่ยนแปลงแนวทางการมีส่วนร่วม✅ ปฏิบัติตาม มาตรฐาน Agent Skills — Frontmatter ใน SKILL.md ถูกต้อง, กฎการตั้งชื่อ, โครงสร้างไดเรกทอรี✅ ความยาวของไฟล์ SKILL.md ไม่ควรเกิน 500 บรรทัด — ให้ย้ายเนื้อหารายละเอียดไปไว้ที่โฟลเดอร์ references/✅ โปรดเตรียมโหมด --demo ในสคริปต์เพื่อให้สามารถใช้งานได้โดยไม่ต้องใช้ API keys✅ ให้ใช้ uv pip install ในตัวอย่างการติดตั้ง Dependency ทั้งหมด✅ เรียกใช้ API keys ผ่านตัวแปรสภาพแวดล้อม (Environment variables) เท่านั้น — ห้ามฮาร์ดโค้ด (Hardcode)✅ ไม่ใช้ภาษาหรือถ้อยคำที่ส่อถึงคำแนะนำทางการลงทุน — ให้สื่อสารผลลัพธ์ว่าเป็นการ "วิเคราะห์" (Analysis) หรือ "ให้ข้อมูล" (Information) เท่านั้นอ่านแนวทางปฏิบัติฉบับเต็มได้ที่ CONTRIBUTING.mdไอเดียสำหรับทักษะใหม่เชื่อมต่อ API กับ CEX (Binance, Bybit, Coinbase)วิเคราะห์เชนอื่นๆ (Ethereum, Base, Arbitrum)กลยุทธ์ Options และภาพจำลอง Greeksทำ Arbitrage ด้วย Funding rateการตรวจจับ Cross-exchange arbitrageการวิเคราะห์เครือข่ายโซเชียลกราฟ (ใครตามใครบน On-chain)การปรับปรุง (Optimize) ค่าแก๊ส/Priority feeกระบวนการรีบาลานซ์พอร์ตโฟลิโออัตโนมัติ🔧 การแก้ไขปัญหาปัญหา: โหลดทักษะไม่ได้ตรวจสอบให้แน่ใจว่าโฟลเดอร์ทักษะอยู่ในไดเรกทอรีที่ถูกต้อง (ดู เริ่มต้นการใช้งาน)โฟลเดอร์ทักษะแต่ละโฟลเดอร์จะต้องมีไฟล์ SKILL.mdรีสตาร์ท Agent/IDE ของท่านหลังจากคัดลอกทักษะลงไปแล้วสำหรับการติดตั้งผ่านปลั๊กอิน: รันคำสั่ง /plugin เพื่อตรวจสอบสถานะ หรือลอง /reload-pluginsปัญหา: หา Python dependencies ไม่พบตรวจสอบไฟล์ SKILL.md ที่เฉพาะเจาะจงนั้นๆ สำหรับแพ็กเกจที่ต้องการติดตั้ง Dependencies โดยรันคำสั่ง: uv pip install package-nameปัญหา: ติด Rate limits ของ APIแบบฟรีมักจะมีการจำกัด (Rate limits) — โปรดศึกษาเอกสารประกอบของ API ตัวนั้นๆพิจารณาทำระบบ Caching หรือส่งคำขอแบบชุด (Batch requests)อัปเกรดเป็นระดับ Pro สำหรับการใช้งานหนักปัญหา: พบข้อผิดพลาด API keyโปรดจัดเก็บ Keys ไว้ในตัวแปรสภาพแวดล้อม (Environment variables) ห้ามใส่ในโค้ดตรวจสอบไฟล์ SKILL.md ของทักษะ เพื่อดูวิธีตั้งค่าการพิสูจน์ตัวตน (Authentication)ยืนยันข้อมูล Credentials และสิทธิ์เข้าถึงของคุณว่าถูกต้องปัญหา: สคริปต์รันไม่ผ่าน (Failing)สคริปต์ส่วนใหญ่รองรับโหมด --demo เพื่อทดสอบแบบไม่ต้องใช้ API keysตรวจสอบข้อความ (Docstring) ในสคริปต์เพื่อดูว่าต้องการ Environment variables ตัวไหนบ้างตรวจสอบว่าติดตั้ง Python 3.9+ ขึ้นไปเรียบร้อยแล้ว❓ คำถามที่พบบ่อย (FAQ)ทั่วไปQ: สามารถใช้งานฟรีได้หรือไม่?A: ใช่ครับ อนุญาตให้ใช้งานภายใต้ลิขสิทธิ์แบบ MIT แต่ทักษะบางรายการอาจอ้างอิงเครื่องมืออื่นที่มีเงื่อนไขลิขสิทธิ์ของตนเองQ: ฉันใช้สำหรับเทรดจริงได้ไหม?A: ทักษะที่เกี่ยวกับการส่งคำสั่ง (เช่น dex-execution, raptor-dex) สามารถทำงานในตลาดจริงได้ แต่โดยค่าเริ่มต้นจะตั้งค่าให้เป็นโหมดจำลอง (Simulation/Demo) ไว้ ซึ่งจะต้องใช้การยืนยันคำสั่งเอง (Explicit confirmation) การใช้งานถือเป็นความเสี่ยงของท่านเองQ: ทำไมจึงเน้น Crypto/DeFi ก่อน?A: เนื่องจากช่องว่างด้านเครื่องมือในคริปโต/DeFi มีมากที่สุด โครงสร้างที่ถูกออกแบบให้ขยายเพิ่มได้นี้ แปลว่าผู้เข้าร่วมสามารถเพิ่มทักษะหุ้น, ออปชั่น และฟิวเจอร์สเข้าไปในรูปแบบเดียวกันนี้ได้อย่างง่ายดายQ: รองรับการทำงานร่วมกับเครื่องมืออื่นที่ไม่ใช่ Claude Code หรือไม่?A: ใช่ครับ ทักษะต่างๆ ปฏิบัติตามมาตรฐานแบบเปิด Agent Skills และใช้งานได้กับเครื่องมือที่รองรับมากกว่า 30 ชนิด เช่น Cursor, Codex, Gemini CLI, VS Code Copilot, Roo Code, Goose และอีกมากมายQ: ทำไมต้องมัดรวมทักษะทั้งหมดไว้ด้วยกัน แทนที่จะแยกเป็นแพ็กเกจเดี่ยวๆ?A: การเทรดเป็นศาสตร์ที่เชื่อมโยงกันอยู่แล้ว การมัดรวมทักษะเข้าไว้ด้วยกัน ทำให้การต่อเวิร์กโฟลว์ (Chaining workflows) ทำได้ง่าย — เช่น การดึงข้อมูล, การคำนวณอินดิเคเตอร์, Backtesting, กำหนดขนาดโพสิชั่น และนำออกข้อมูลรายงานภาษี — โดยไม่ต้องกังวลว่าต้องไปติดตั้งทักษะชิ้นไหนแยกกันบ้างการติดตั้ง & การตั้งค่าQ: ฉันต้องใช้ API keys ทุกตัวเลยหรือไม่?A: ไม่ครับ หลายๆ ทักษะ (เช่น DexScreener, DeFiLlama, Jupiter quotes, CoinGecko โหมดฟรี) ไม่ต้องการการยืนยันตัวตนเลย ให้ติดตั้ง API keys เฉพาะบริการที่ท่านต้องการใช้งานเท่านั้นก็พอQ: ฉันจำเป็นต้องติดตั้ง Python packages ทุกตัวไหม?A: ไม่ครับ ติดตั้งเฉพาะแพ็กเกจที่ท่านต้องใช้เท่านั้น แต่ละทักษะจะระบุความต้องการไว้อย่างชัดเจนในไฟล์ SKILL.mdQ: หากมีทักษะที่ไม่ทำงาน ควรทำอย่างไร?A: ให้ตรวจสอบที่หัวข้อ การแก้ไขปัญหา ก่อน หากปัญหายังคงอยู่ให้ เปิด Issue บน GitHub และอธิบายขั้นตอนอย่างละเอียดการมีส่วนร่วมQ: ฉันสามารถสร้างและใส่ทักษะของตัวเองลงไปได้หรือไม่?A: ได้แน่นอน! เรายินดีรับการมีส่วนร่วมจากทุกคน กรุณาตรวจสอบหัวข้อ การมีส่วนร่วม สำหรับแนวทางปฏิบัติQ: จะแจ้งบั๊กหรือเสนอแนะฟีเจอร์ใหม่ได้อย่างไร?A: ท่านสามารถ เปิด Issue บน GitHub พร้อมคำอธิบายที่ชัดเจน สำหรับการแจ้งบั๊ก โปรดใส่ขั้นตอนการทำซ้ำปัญหา พฤติกรรมที่ควรจะเป็น และพฤติกรรมที่เกิดขึ้นจริง💬 การช่วยเหลือ (Support)📖 เอกสารประกอบ (Documentation): อ่าน SKILL.md และดูโฟลเดอร์ references/ ที่เกี่ยวข้อง🐛 แจ้งบั๊ก (Bug Reports): เปิด Issue บน GitHub💡 เสนอแนะฟีเจอร์ (Feature Requests): ส่งข้อเสนอแนะฟีเจอร์ใหม่📖 การอ้างอิงBibTeXข้อมูลโค้ด@software{claude_trading_skills_2026,
  author = {{AGIPro}},
  title = {Claude Trading Skills: Trading, DeFi, and Quantitative Finance Agent Skills},
  year = {2026},
  url = {[https://github.com/agiprolabs/claude-trading-skills](https://github.com/agiprolabs/claude-trading-skills)},
  note = {67 skills covering market data, on-chain analysis, backtesting, risk management, tax compliance, and more}
}
APAAGIPro. (2026). Claude Trading Skills: Trading, DeFi, and quantitative finance Agent Skills [Computer software]. [https://github.com/agiprolabs/claude-trading-skills](https://github.com/agiprolabs/claude-trading-skills)
ข้อความปกติ (Plain Text)Claude Trading Skills by AGIPro (2026)
Available at: [https://github.com/agiprolabs/claude-trading-skills](https://github.com/agiprolabs/claude-trading-skills)
📄 ใบอนุญาตอยู่ภายใต้ใบอนุญาต MIT ดูข้อกำหนดแบบเต็มได้ที่ LICENSE.mdประเด็นสำคัญ:✅ ใช้งานได้ฟรีในทุกวัตถุประสงค์ (ทั้งเชิงพาณิชย์และไม่ใช่เชิงพาณิชย์)✅ Open source — สามารถแก้ไข แจกจ่าย และใช้งานได้อย่างอิสระ⚠️ ไม่มีการรับประกัน — ให้บริการตามสภาพ "as is"⚠️ ไม่ใช่คำแนะนำการลงทุน — สิ่งนี้คือชุดเครื่องมือสำหรับการวิจัยเท่านั้นสร้างโดยเทรดเดอร์ เพื่อเทรดเดอร์ กดดาว ⭐ หากท่านพบว่าเครื่องมือนี้มีประโยชน์!