// src/config.js — Central configuration for DeepSeek Agent
const path = require('path');
const fs   = require('fs');
const os   = require('os');

// ─────────────────────────────────────────────
//  Default configuration
// ─────────────────────────────────────────────
const defaults = {
  // Browser
  DEEPSEEK_URL   : 'https://chat.deepseek.com',
  SESSION_DIR    : process.env.DS_SESSION_DIR || path.join(os.homedir(), '.deepseek-agent', 'session'),
  HEADLESS       : false,

  // Timing
  RESPONSE_TIMEOUT : 30_000,   // Reduced from 60s to 30s
  STABLE_DELAY     : 500,      // Reduced from 1000ms to 500ms
  SEND_DELAY       : 50,       // Reduced from 100ms to 50ms

  // Agent
  MAX_ITERATIONS   : 60,
  WORKING_DIR      : process.cwd(),

  // Output
  MAX_OUTPUT_LENGTH : process.env.DS_QUIET === 'true' ? 4_000 : 8_000,
  DEBUG             : false,

// Tool behavior controls
  AUTO_TOOLS       : false,         // Disable automatic tool usage
  ASK_BEFORE_TOOLS : false,         // Don't ask for permission (auto-decide based rules)
  STRICT_TOOL_MODE : true,         // Use strict tool usage rules
  SMART_TOOL_DETECTION : true,     // Enable intelligent tool detection
  
  // Performance optimizations
  PERSISTENT_SESSION : true,      // Reuse browser sessions
  RESPONSE_STREAMING : true,      // Enable streaming responses
  CACHE_ENABLED      : true,      // Enable response caching
};

// ─────────────────────────────────────────────
//  Config loading priority (highest wins):
//
//  1. ~/.deepseek-agent/config.json  — global user config
//  2. ./deepseek-agent.config.json   — per-project config
// ─────────────────────────────────────────────

function loadJson(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return JSON.parse(fs.readFileSync(filePath, 'utf8'));
    }
  } catch {
    console.warn('[deepseek-agent] Could not parse config file: ' + filePath);
  }
  return {};
}

const globalConfigPath  = path.join(os.homedir(), '.deepseek-agent', 'config.json');
const projectConfigPath = path.join(process.cwd(), 'deepseek-agent.config.json');

const config = {
  ...defaults,
  ...loadJson(globalConfigPath),   // global overrides defaults
  ...loadJson(projectConfigPath),  // project overrides global
};

// Remove comment keys from JSON files
delete config._comment;

// Resolve session dir to absolute path
if (!path.isAbsolute(config.SESSION_DIR)) {
  config.SESSION_DIR = path.resolve(process.cwd(), config.SESSION_DIR);
}

// Ensure required directories exist
fs.mkdirSync(config.SESSION_DIR, { recursive: true });
fs.mkdirSync(path.join(os.homedir(), '.deepseek-agent', 'logs'), { recursive: true });

module.exports = config;
