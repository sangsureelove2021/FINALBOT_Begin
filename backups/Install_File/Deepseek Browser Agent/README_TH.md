<div align="center">

<img src="https://img.shields.io/badge/status-in%20development-orange?style=for-the-badge" alt="Status: In Development"/>
<img src="https://img.shields.io/npm/v/deepseek-browser-agent?style=for-the-badge&color=blue" alt="npm version"/>
<img src="https://img.shields.io/badge/node-%3E%3D18.0.0-brightgreen?style=for-the-badge" alt="Node.js"/>
<img src="https://img.shields.io/badge/license-MIT-green?style=for-the-badge" alt="License"/>
<img src="https://img.shields.io/badge/PRs-welcome-brightgreen?style=for-the-badge" alt="PRs Welcome"/>

# 🤖 DeepSeek Browser Agent (เวอร์ชันภาษาไทย)

**AI coding agent ที่ทำงานแบบอิสระ - ฟรีไม่ต้องใช้ API key**

มันขับเคลื่อนเบราว์เซอร์จริงเพื่อพูดคุยกับ [DeepSeek](https://chat.deepseek.com) ให้คุณได้ AI coding agent แบบ Claude Code / Cursor ที่ใช้พลังงานจาก DeepSeek ได้ฟรีๆ

[ติดตั้ง](#-ติดตั้งงาน) · [เริ่มใช้งาน](#-เริ่มใช้งาน) · [วิธีใช้](#-วิธีใช้งาน) · [การตั้งค่า](#-การตั้งค่า) · [เครื่องมือ](#-เครื่องมือที่มี) · [การมีส่วนร่วม](#-การมีส่วนร่วม)

---

> ⚠️ **โปรเจกต์นี้กำลังพัฒนาอยู่**
> ฟังก์ชันหลักๆ ทำงานได้แล้ว แต่อาจเจอปัญหาบางอย่าง รายงาน bug และมีส่วนร่วมได้ครับ - [การมีส่วนร่วม](#-การมีส่วนร่วม)

</div>

---

## 🧠 วิธีการทำงาน

AI coding agents ส่วนใหญ่ติดต่อกับ paid API แต่ตัวนี้ไม่ใช่

แทนนั้นมันใช้ **Playwright** ควบคุมเบราว์เซอร์ Chromium จริงๆ นำทางไปที่ `chat.deepseek.com` ส่ง task ของคุณ รอ response และ parse tool calls ทั้งหมดโดยอัตโนมัติ

ไฟล์และ terminal ของคุณถูกเชื่อมต่อเป็น tools ที่ AI ใช้ได้ ดังนั้นมันอ่าน code, เขียนไฟล์, รัน commands และสร้างโปรเจคทีละขั้นตอนได้เอง

```
Terminal ของคุณ
        │
        ▼
    Agent Core          ← จัดการ loop ทั้งหมด
        │
    ├──► Browser (Playwright)  ← พูดคุยกับ chat.deepseek.com
    │         │
    │    DeepSeek AI  ← คิดคำนวณ ตัดสินใจใช้ tool
    │         │
    └──► Tool Executor  ← อ่าน/เขียนไฟล์ รัน commands
             │
         โปรเจคของคุณ
```

---

## 📦 การติดตั้งงาน

```bash
npm install -g deepseek-browser-agent
```

> Chromium จะดาวโหลดอัตโนมัติหลังติดตั้ง (~150 MB, ครั้งเดียว)

**ข้อกำหนด:** Node.js ≥ 18

---

## 🚀 เริ่มใช้งาน

**1. ครั้งแรก - login เข้า DeepSeek:**
```bash
deepseek-agent --interactive
```
เบราว์เซอร์จะเปิดขึ้น ล็อกอินเข้า DeepSeek กลับมาที่ terminal กด **Enter** ครั้งเดียว แล้ว session ถูกเก็บไว้

**2. ส่ง task:**
```bash
deepseek-agent "สร้าง REST API ด้วย Express กับ user authentication"
```

**3. ใช้ alias `dsa` จากโฟลเดอร์โปรเจคใดๆ:**
```bash
cd ~/my-project
dsa "เพิ่ม input validation ให้ API routes ทั้งหมด"
```

---

## 💻 วิธีใช้งาน

```
deepseek-agent [OPTIONS] [TASK]

  -t, --task <task>    Task ที่จะทำ (หรือพิมพ์เป็น argument สุดท้าย)
  -i, --interactive    รักษาเบราว์เซอร์เปิดไว้ ทำหลาย tasks ใน session เดียว
  -d, --dir <path>     ตั้ง working directory (default: directory ปัจจุบัน)
  --debug              พิมพ์ raw AI responses ที่ terminal
  --headless           รันเบราว์เซอร์แบบหลับ (ต้อง login ก่อนแล้ว)
  --save-log           บันทึก session log ทั้งหมดที่ ~/.deepseek-agent/logs/
  --calibrate          ตรวจจับ DOM selectors อัตโนมัติ (รันหาก agent เกิดขัดข้อง)
  -h, --help           แสดง help

Aliases:
  dsa                  รูปแบย่อของ deepseek-agent
```

### ตัวอย่าง

```bash
# Single task - รันแล้วจบ
deepseek-agent "สร้าง Python script ที่ scrapes Hacker News"

# Interactive mode - รักษาเบราว์เซอร์เปิด
deepseek-agent --interactive

# รันบนโปรเจคเฉพาะ
dsa --dir ~/projects/my-app "refactor ทั้งหมด callbacks เป็น async/await"

# Debug mode (แสดงว่า DeepSeek กำลัง output อะไร)
dsa --debug "สร้าง calculator"

# Headless mode (เร็วกว่า - เบราว์เซอร์รันใน background)
dsa --headless "เขียน unit tests สำหรับ utils.js"

# ใน interactive mode พิมพ์ 'new' เพื่อเริ่ม chat ใหม่:
❯ Task: new
```

---

## ⚙️ การตั้งค่า

### Global config - ใช้ทุกที่

สร้าง `~/.deepseek-agent/config.json`:

```json
{
  "HEADLESS": true,
  "MAX_ITERATIONS": 50,
  "STABLE_DELAY": 3000,
  "DEBUG": false
}
```

### Per-project config - override global

วาง `deepseek-agent.config.json` ที่ root โปรเจค:

```json
{
  "MAX_ITERATIONS": 60,
  "MAX_OUTPUT_LENGTH": 12000
}
```

### ทั้งหมดที่ตั้งได้

| Setting | Default | คำอธิบาย |
|---|---|---|
| `HEADLESS` | `false` | ซ่อนเบราว์เซอร์ window |
| `MAX_ITERATIONS` | `60` | Max agent steps per task ก่อนจบ |
| `RESPONSE_TIMEOUT` | `180000` | Max ms รอ response (3 นาที) |
| `STABLE_DELAY` | `2500` | Ms ของ silence ที่หมายถึง DeepSeek ทำเสร็จ |
| `SEND_DELAY` | `400` | Ms ระหว่างการพิมพ์และกด Enter |
| `MAX_OUTPUT_LENGTH` | `8000` | ตัด output ที่ยาวเกินไปที่ส่งให้ AI |
| `DEBUG` | `false` | พิมพ์ raw AI responses ที่ terminal |
| `SESSION_DIR` | `~/.deepseek-agent/session` | ที่เก็บ browser cookies |

---

## 🛠️ เครื่องมือที่มี

Agent สามารถใช้ tools เหล่านี้อย่างอิสระเพื่อทำ task ให้เสร็จ:

| Tool | คำอธิบาย |
|---|---|
| `read_file` | อ่าน contents ของไฟล์, บางส่วนหรือทั้งหมด |
| `write_file` | สร้างหรือ overwrite ไฟล์ (auto-create directories) |
| `append_to_file` | เพิ่ม text ไปที่ไฟล์เดิม |
| `replace_in_file` | ค้นหาและแทนที่ text ในไฟล์ (regex supported) |
| `delete_file` | ลบไฟล์ถาวร |
| `list_directory` | แสดง contents ของ directory, บางที recursive |
| `create_directory` | สร้าง directory และ parents ทั้งหมด |
| `move_file` | ย้ายหรือ rename ไฟล์/directory |
| `copy_file` |  copy ไฟล์ไปที่ตำแหน่งใหม่ |
| `get_file_info` | ด metadata ของไฟล์ (size, line count, dates) |
| `run_command` |  execute shell commands |
| `find_files` |  ค้นหาไฟล์ตาม pattern (e.g. `*.ts`) |
| `search_in_files` | ค้นหา text ในไฟล์ (เหมือน `grep -r`) |
| `read_url` | ดึงและอ่าน content ของ URL |
| `write_files` |  เขียนหลายๆ ไฟล์พร้อมกัน (batch scaffold) |

---

## 📂 ข้อมูลเก็บไว้ที่ไหน

ทุกอยู่อยู่ใน `~/.deepseek-agent/` ใน home directory ของคุณ:

```
~/.deepseek-agent/
├── session/        ← Browser cookies (login ครั้งเดียว ใช้ได้ตลอด)
├── logs/           ← Session logs (บันทึกก็ต่อเมื่อใช้ --save-log)
└── config.json     ← Global settings ของคุณ
```

---

## 🔧 การแก้ปัญหา

### Agent ตอบแต่สร้างไฟล์ไม่ได้
Browser DOM  render AI response ในแบบที่ parser ไม่ capture ได้ รันด้วย `--debug` เพื่อดูว่าได้รับอะไร:
```bash
deepseek-agent --debug "สร้าง calculator"
```

### Agent หยุดตอบ/loop
DeepSeek UI อาจเปลี่ยนไป รัน calibration tool - มัน inspect live DOM และ print updated selectors:
```bash
deepseek-agent --calibrate
```

### Login session หมดอายุ
รันโดยไม่ใช้ `--headless` - เบราว์เซอร์เปิดและคุณ login ใหม่:
```bash
deepseek-agent --interactive
```

### Chromium ไม่โหลดอัตโนมัติ
```bash
npx playwright install chromium
```

### Response timeout บน tasks ยาว
เพิ่ม timeout ใน config:
```json
{ "RESPONSE_TIMEOUT": 300000, "STABLE_DELAY": 4000 }
```

---

## 🗂️ โครงสร้างโปรเจค

```
deepseek-browser-agent/
├── src/
│   ├── index.js          ← CLI entry point และ argument parsing
│   ├── agent.js          ← Core agent loop (send → wait → parse → execute)
│   ├── browser.js        ← Playwright controller สำหรับ chat.deepseek.com
│   ├── tools.js          ← ทั้งหมด 15 filesystem และ shell tools
│   ├── parser.js         ← Extracts tool calls จาก AI responses (6 strategies)
│   ├── prompt.js         ← System prompt และ conversation history manager
│   ├── config.js         ← Configuration loader (global + per-project)
│   ├── logger.js         ← ANSI-colored terminal output
│   ├── calibrate.js      ← DOM selector inspector / auto-fix tool
│   └── postinstall.js    ← Auto-downloads Chromium หลังจาก npm install
├── LICENSE
├── README.md
└── package.json
```

---

## 🤝 การมีส่วนร่วม

การมีส่วนร่วมยินดีเป็นอย่างยิ่ง - โปรเจกต์นี้กำลังพัฒนาอยู่และมีเวลาให้เติบโต

### การตั้งค่าในเครื่อง

```bash
git clone https://github.com/Omar-Azam/deepseek-browser-agent
cd deepseek-browser-agent
npm install
npx playwright install chromium
node src/index.js --interactive
```

### ส่วนที่ต้องการพัฒนา

- 🧪 **Tests** - ไม่มี automated tests ยัง; test suite จะเป็น contribution ที่ดี
- 🎨 **UI selector resilience** - DeepSeek อัปเดต UI บางครั้ง; selector strategies ที่ดียินดีต้อนรับ
- 🔌 **More tools** - image generation, browser control, database tools, etc.
- 🌐 **Other AI frontends** - adapting browser layer ให้ work กับ other free AI chats
- 📦 **Windows support** - ทดลองบน Linux; Windows path handling อาจจะต้องแก้
- 📝 **Better error messages** - ทำให้ failures ง่ายต่อการวินิจฉัย

### วิธีการมีส่วนร่วม

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-improvement`
3. Make your changes
4. Open a Pull Request ด้วย description ที่ชัดเจน

Please keep PRs focused — one feature or fix per PR makes review much faster.

### การรายงาน bugs

Open an issue on GitHub พร้อม:
- อะไรที่คุณรัน
- อะไรที่คุณคาดหวัง
- อะไรที่เกิดขึ้นจริง
- Output ของ `deepseek-agent --debug "your task"` หากเกี่ยวข้อง

---

## ⚠️ ข้อควรระวัง

โปรเจกต์นี้ automates a web browser เพื่อ interact กับ chat.deepseek.com การ automate web UIs อาจ violate terms of service ของ website ที่ถูก automate ใช้ tool นี้สำหรับ **personal and development purposes only** ผู้เขียนไม่รับผิดชอบสำหรับ account suspensions หรือ consequences อื่นๆ ของการใช้

---

## 📄 ใบอนุญาต

MIT —ดู [LICENSE](./LICENSE) สำหรับรายละเอียด

---

<div align="center">

**สร้างด้วย Playwright · ขับเคลื่อนด้วย DeepSeek · ฟรีตลอดไป**

ถ้าโปรเจกต์นี้ช่วยคุณ พิจารณาให้ ⭐ บน GitHub!

</div>