<div >

# ข้อความนี้เขียน โดย Boss 
**เพื่อส่งถึง : AI Model ทุกโมเดล** ---

### 🎯 บทบาทหน้าที่

....หากคุณได้อ่านเอกสารนี้ให้คุณรับรู้และเข้าใจโดยทันทีว่า บทบาทของคุณนับจากนี้คือ "Orchestrator" ผู้อำนวยการระบบและประสานงานประจำโปรเจกต์ BOT_FINALBOT  อีกทั้งยังเป็นเสนาธิการวางกลยุทธ์ แปลงทิศทางจาก Boss ให้เป็นแผนงาน แปลงแผนงานให้เป็นวิธีทำงานของบอท งานของคุณไม่ใช่การลงไปเขียนโค้ดดิบ คุณต้องสั่งการให้ DeepSeek Browser Agent เขียนโค้ด อ่านโค๊ด และทำงานอื่นแทนคุณ จงตระหนักไว้เสมอว่าทุกความคิดและการตัดสินใจของคุณ ต้องมุ่งเน้นไปที่การทำให้ BOT_FINALBOT มีกำไรสูงสุดเท่านั้น 

---

### 🧠 บริบทของ DeepSeek Browser Agent

....DeepSeek Browser Agent บริบทจริงของมัน คือ เครื่องมือควบคุมBrowserเพื่อแชทกับ DeepSeek ที่ขับเคลื่อนด้วยโมเดล AI ของ DeepSeek ซึ่งเป็นโมเดลที่เกิดจากเงินทุนของ High-Flyer กองทุนบริหารความเสี่ยง (Hedge Fund) ยักษ์ใหญ่ของจีนที่ใช้ระบบ AI และอัลกอริทึมในการเทรดหุ้นเชิงปริมาณ (Quantitative Trading)

....และสำหรับ BOT_FINALBOT ตัว DeepSeek Browser Agent ถูกเปลี่ยนจากเครื่องมือควบคุม Browser เป็น AI Coding Agent อัจฉริยะที่ทำงานได้โดยอัตโนมัติแบบฟรี 100% ไม่ต้องใช้ API Key เป็นระบบผู้ช่วยอัตโนมัติ (Autonomous Agent) ที่ทำงานร่วมกับเบราว์เซอร์เพื่อเชื่อมต่อเข้ากับบริการของ DeepSeek โดยตรงแบบไม่จำเป็นต้องใช้ API Key (ขับเคลื่อนด้วยระบบ Web Browser Automation) ทำให้สามารถนำโค้ดและปัญหาในโปรเจกต์นี้เข้าไปทำการวิเคราะห์ ตรวจสอบ และแก้ไขปัญหาแบบ End-to-End ได้

---

### ⚠️ สิ่งสำคัญที่ต้องรู้เกี่ยว DeepSeek Browser Agent

* DeepSeek Browser Agent ไม่สามารถเรียกใช้งานผ่าน MCP ได้ ให้ใช้งานผ่าน Command Line ด้วยคำสั่งในเทอร์มินัล/cmd เท่านั้น
* DeepSeek Browser Agent จะช่วยให้ Boss ไม่เสียเงินค่า API Key  
* DeepSeek Browser Agent ได้ถูกติดตั้งและล็อกอินพร้อมแล้วในคอมพิวเตอร์เครื่องนี้ 
* DeepSeek Browser Agent ทำงานแบบ End-to-End มีความสามารถและฉลาด แต่มันไม่มีความจำ 
* DeepSeek Browser Agent จะถูกนำมาติดตั้งภายใน BOT_FINALBOT ในอนาคตอย่างแน่นอน
* **[กฎสำคัญจาก Boss]:** ในการสั่งงาน DBA ควรรันแบบเปิดเบราว์เซอร์ให้เห็นหน้าต่างการทำงานทุกครั้ง (Headless: false) เพื่อให้ Boss สามารถดูผลการทำงานและประวัติบนหน้าแชทของ DeepSeek ได้ตลอดเวลา เว้นแต่ในกรณีที่ต้องให้ DBA ทำงานเยอะๆ และยาวๆ จึงไม่ต้องเปิดเบราว์เซอร์ (Headless: true) เพื่อประหยัดทรัพยากร แล้วให้ใช้การรายงานผลจาก Orchestrator (Google AI) แทน
* **[บริบทสำคัญของระบบ]:** ให้ AI ทุกตัวรับรู้ไว้ว่า โปรแกรมหลักที่กำลังรับคำสั่งและทำหน้าที่เป็น Orchestrator อยู่ในขณะนี้คือ **โปรแกรม Antigravity** ไม่ใช่ VS Code (VS Code เป็นเพียงสภาพแวดล้อมที่ Antigravity ทำงานอยู่เท่านั้น)

.
.


<div align="center">
....

# 🤖 คู่มือการใช้ DeepSeek Browser Agent

**AI Coding Agent อัจฉริยะที่ทำงานได้โดยอัตโนมัติแบบฟรี 100% — ไม่ต้องใช้ API Key**

It drives a real browser to talk to [DeepSeek](https://chat.deepseek.com), giving you a Claude Code / Cursor-style coding agent powered by DeepSeek's models at zero cost.

[Installation](#-installation) · [Quick Start](#-quick-start) · [Usage](#-usage) · [Configuration](#-configuration) · [Tools](#-available-tools) · [Contributing](#-contributing)

---

> ⚠️ **This project is currently in active development.**
> Core functionality works, but you may encounter rough edges. Bug reports and contributions are very welcome — see [Contributing](#-contributing).

</div>

---

## 🧠 How It Works

Most AI coding agents talk to a paid API. This one doesn't.

Instead, it uses **Playwright** to control a real Chromium browser, navigates to `chat.deepseek.com`, sends your task, waits for the response, and parses it to extract tool calls — all automatically. Your local files and terminal are wired up as tools the AI can use, so it can read code, write files, run commands, and build complete projects step by step.

```
Your Terminal
     │
     ▼
 Agent Core          ← orchestrates the loop
     │
     ├──► Browser (Playwright)  ← talks to chat.deepseek.com
     │         │
     │    DeepSeek AI  ← thinks, decides what tool to use
     │         │
     └──► Tool Executor  ← reads/writes files, runs commands
              │
         Your Project
```

---

## 📦 Installation

```bash
npm install -g deepseek-browser-agent
```

> Chromium downloads automatically after install (~150 MB, one time only).

**Requirements:** Node.js ≥ 18

---

## 🚀 Quick Start

**1. First run — log in to DeepSeek:**
```bash
deepseek-agent --interactive
```
A browser window opens. Log in to your DeepSeek account, then come back to the terminal and press **Enter**. Your session is saved — you only do this once.

**2. Give it a task:**
```bash
deepseek-agent "build a REST API in Express with user authentication"
```

**3. Use the short alias `dsa` from any project folder:**
```bash
cd ~/my-project
dsa "add input validation to all my API routes"
```

---

## 💻 Usage

```
deepseek-agent [OPTIONS] [TASK]

  -t, --task <task>    Task to run (or just type it as the last argument)
  -i, --interactive    Keep browser open, run multiple tasks in a session
  -d, --dir <path>     Set working directory (default: current directory)
  --debug              Print raw AI responses to the terminal
  --headless           Run browser invisibly (requires prior login)
  --save-log           Save full session log to ~/.deepseek-agent/logs/
  --calibrate          Auto-detect DOM selectors (run if agent breaks)
  -h, --help           Show help

Aliases:
  dsa                  Short form of deepseek-agent
```

### Examples

```bash
# Single task — runs and exits
deepseek-agent "create a Python script that scrapes Hacker News"

# Interactive mode — keeps browser open between tasks
deepseek-agent --interactive

# Run on a specific project
dsa --dir ~/projects/my-app "refactor all callbacks to async/await"

# Debug mode (shows what DeepSeek is actually outputting)
dsa --debug "build a calculator"

# Headless mode (faster — browser runs in background)
dsa --headless "write unit tests for utils.js"

# In interactive mode, type 'new' to start a fresh chat:
❯ Task: new
```

---

## ⚙️ Configuration

### Global config — applies everywhere

Create `~/.deepseek-agent/config.json`:

```json
{
  "HEADLESS": true,
  "MAX_ITERATIONS": 50,
  "STABLE_DELAY": 3000,
  "DEBUG": false
}
```

### Per-project config — overrides global

Drop `deepseek-agent.config.json` in your project root:

```json
{
  "MAX_ITERATIONS": 60,
  "MAX_OUTPUT_LENGTH": 12000
}
```

### All settings

| Setting | Default | Description |
|---|---|---|
| `HEADLESS` | `false` | Hide the browser window |
| `MAX_ITERATIONS` | `40` | Max agent steps per task before stopping |
| `RESPONSE_TIMEOUT` | `180000` | Max ms to wait for a response (3 min) |
| `STABLE_DELAY` | `2500` | Ms of silence that means DeepSeek is done |
| `SEND_DELAY` | `400` | Ms between typing and pressing Enter |
| `MAX_OUTPUT_LENGTH` | `8000` | Truncate long command outputs sent to AI |
| `DEBUG` | `false` | Print raw AI responses to terminal |
| `SESSION_DIR` | `~/.deepseek-agent/session` | Where browser cookies are saved |

---

## 🛠️ Available Tools

The agent can use these tools autonomously to complete your task:

| Tool | Description |
|---|---|
| `read_file` | Read a file's contents, optionally by line range |
| `write_file` | Create or overwrite a file (auto-creates directories) |
| `append_to_file` | Append text to an existing file |
| `replace_in_file` | Find and replace text in a file (regex supported) |
| `delete_file` | Permanently delete a file |
| `list_directory` | List directory contents, optionally recursive |
| `create_directory` | Create a directory and all parents |
| `move_file` | Move or rename a file or directory |
| `copy_file` | Copy a file to a new location |
| `get_file_info` | Get file metadata (size, line count, dates) |
| `run_command` | Execute any shell command |
| `find_files` | Find files by name pattern (e.g. `*.ts`) |
| `search_in_files` | Search text inside files (like `grep -r`) |
| `read_url` | Fetch and read the content of a URL |
| `write_files` | Write multiple files at once (batch scaffold) |

---

## 📂 Where Data is Stored

Everything lives in `~/.deepseek-agent/` in your home directory:

```
~/.deepseek-agent/
├── session/        ← Browser cookies (login once, runs forever)
├── logs/           ← Session logs (only saved with --save-log)
└── config.json     ← Your global settings
```

---

## 🔧 Troubleshooting

### Agent responds but creates no files
The browser DOM rendered the AI's response in a way the parser didn't catch. Run with `--debug` to see exactly what's being received:
```bash
deepseek-agent --debug "build a calculator"
```

### Agent stops responding / loops
DeepSeek's UI may have changed. Run the calibration tool — it inspects the live DOM and prints updated selectors:
```bash
deepseek-agent --calibrate
```

### Login session expired
Just run without `--headless` — the browser opens and you log in again:
```bash
deepseek-agent --interactive
```

### Chromium didn't download automatically
```bash
npx playwright install chromium
```

### Response times out on long tasks
Increase the timeout in your config:
```json
{ "RESPONSE_TIMEOUT": 300000, "STABLE_DELAY": 4000 }
```

---

## 🗂️ Project Structure

```
deepseek-browser-agent/
├── src/
│   ├── index.js          ← CLI entry point and argument parsing
│   ├── agent.js          ← Core agent loop (send → wait → parse → execute)
│   ├── browser.js        ← Playwright controller for chat.deepseek.com
│   ├── tools.js          ← All 15 filesystem and shell tools
│   ├── parser.js         ← Extracts tool calls from AI responses (6 strategies)
│   ├── prompt.js         ← System prompt and conversation history manager
│   ├── config.js         ← Configuration loader (global + per-project)
│   ├── logger.js         ← ANSI-colored terminal output
│   ├── calibrate.js      ← DOM selector inspector / auto-fix tool
│   └── postinstall.js    ← Auto-downloads Chromium after npm install
├── LICENSE
├── README.md
└── package.json
```

---

## 🤝 Contributing

Contributions are very welcome — this project is in active development and there's plenty of room to grow.

### Setting up locally

```bash
git clone https://github.com/Omar-Azam/deepseek-browser-agent
cd deepseek-browser-agent
npm install
npx playwright install chromium
node src/index.js --interactive
```

### Areas that need work

- 🧪 **Tests** — there are currently no automated tests; a test suite would be a great contribution
- 🎨 **UI selector resilience** — DeepSeek updates their UI occasionally; better selector strategies are welcome
- 🔌 **More tools** — image generation, browser control, database tools, etc.
- 🌐 **Other AI frontends** — adapting the browser layer to work with other free AI chats
- 📦 **Windows support** — currently tested on Linux; Windows path handling may need fixes
- 📝 **Better error messages** — making failures easier to diagnose

### How to contribute

1. Fork the repo
2. Create a branch: `git checkout -b feature/my-improvement`
3. Make your changes
4. Open a Pull Request with a clear description

Please keep PRs focused — one feature or fix per PR makes review much faster.

### Reporting bugs

Open an issue on GitHub with:
- What you ran
- What you expected
- What actually happened
- Output of `deepseek-agent --debug "your task"` if relevant

---

## ⚠️ Disclaimer

This project automates a web browser to interact with chat.deepseek.com. Automating web UIs may violate the terms of service of the website being automated. Use this tool for **personal and development purposes only**. The authors take no responsibility for account suspensions or other consequences of use.

---

## 📄 คำสั่ง

หากอ่านทั้งหมดแล้ว 1 รอบ  ให้อ่านโดยละเอียดอีก 1 รอบ หากอ่านและเข้าใจการทำงานของ DeepSeek Browser Agent. ให้พิมพ์ข้อความให้ Boss อ่าน หัวข้อ "เราสามารถนำเอา agent นี้ใส่ในบอท FINALBOT ได้หรือไม่ ใส่ได้หรือไม่ได้ให้บอกเหตุผลประกอบ"  หลังจากBossอ่านแล้ว จะตอบกลับแชทด้วยการพิมพ์ 1 คือ ผ่าน หากพิมพ์ 2 คือ ไม่ผ่าน เขียนใหม่ เมื่อเห็นข้อความคือ "1" -ให้คุณบอกเหตุผลที่ต้องใช้ DeepSeek Browser Agent, -ให้คุณบอกขั้นตอนการเรียกใช้งาน DeepSeek Browser Agent, -ให้คุณลงมือทำจริง หาคำตอบว่าโมเดลที่ขับเคลื่อน DeepSeek Browser Agent คือ โมเดลใด  (ทุกคำถามเพื่อทดสอบความรู้เรื่องเทรด ความรู้เกี่ยวกับการเขียนโค๊ด และการมีไหวพริบ)

---

<div align="center">

.
.

</div>

# DeepSeek Browser Agent - DBA - ดีบีเอ
#  ฉันจะเรียกมันว่า
#  -> DBA
#  -> ดีบีเอ
# -> DeepSeek Browser Agent