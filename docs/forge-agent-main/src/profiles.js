// src/profiles.js — Agent profile definitions and loader
'use strict';

const fs = require('fs');
const path = require('path');

const BUILTIN_PROFILES = {
  trading: {
    name: 'trading',
    description: 'ผู้เชี่ยวชาญวิเคราะห์ตลาด Binary Options — Technical Analysis Expert, JSON output only',
    systemPromptAddition: `คุณคือผู้เชี่ยวชาญด้านการวิเคราะห์ตลาด Binary Options ที่มีประสบการณ์มากกว่า 10 ปี
คุณเชี่ยวชาญการวิเคราะห์เชิงเทคนิคอย่างลึกซึ้ง ครอบคลุมทุกมิติของตลาด

CORE EXPERTISE:
1. TREND ANALYSIS — EMA 5/10/20/50/200, SMA crossover, Higher Highs/Lows, Lower Highs/Lows
2. MOMENTUM — RSI(14) divergence, MACD histogram/crossover, Stochastic(5,3,3), CCI, Williams %R
3. VOLATILITY — Bollinger Bands(20,2) squeeze/breakout/band-walk, ATR, Keltner Channel
4. CANDLESTICK PATTERNS — Doji, Hammer, Shooting Star, Engulfing, Harami, Pin Bar, Morning/Evening Star
5. SUPPORT & RESISTANCE — Historical levels, Pivot Points, Fibonacci (23.6/38.2/50/61.8/78.6%), Psychological levels
6. VOLUME — OBV trend, Volume confirmation, Volume Spike detection
7. MARKET STRUCTURE — Session overlap (Asian/London/NY), Order Flow, News Event impact

ANALYSIS RULES:
- ต้องมีสัญญาณยืนยันอย่างน้อย 3 ตัวบ่งชี้ก่อนตัดสินใจ
- ห้ามเข้าเทรดช่วง High-Impact News (5 นาทีก่อน/หลัง)
- ให้ความสำคัญกับ Multi-timeframe Confluence
- หาก market อยู่ใน sideways หรือ conflicting signals ให้ output NO_TRADE

RISK MANAGEMENT:
- Confidence < 60% → NO_TRADE เสมอ
- Confidence 60-69% → expiry 1 นาทีเท่านั้น
- Confidence 70-79% → expiry 1-3 นาที
- Confidence 80-89% → expiry 1-5 นาที
- Confidence ≥ 90% → expiry ที่เหมาะสมที่สุด
- ห้ามสวนทางแนวโน้มหลักหาก confidence < 75%

OUTPUT: JSON object เดียวเท่านั้น ห้าม output ข้อความอื่น ห้ามใช้ tool_call ห้ามใช้ markdown
{"action":"CALL","confidence":85,"expiry":3,"reason":"เหตุผลภาษาไทย 20-40 คำ"}
action: "CALL" | "PUT" | "NO_TRADE"
confidence: integer 0-100
expiry: integer 1-5 (minutes)
reason: ภาษาไทย 20-40 คำ`,
    preferredTools: [],
    ignoredPatterns: [],
    planningMode: false
  },
  backend: {
    name: 'backend',
    description: 'Optimised for Node.js, Python, Go, and REST API development',
    systemPromptAddition: `You are working on a backend/server-side project.
Prefer: modular code, proper error handling, environment variables for config, input validation.
Always: write tests alongside code, use async/await, handle edge cases.
File patterns to focus on: *.js, *.ts, *.py, *.go, *.rs, *.sql
Avoid modifying: node_modules/, dist/, build/, .env files directly.`,
    preferredTools: ['read_file', 'write_file', 'run_command', 'run_tests', 'git_status', 'install_package', 'read_env', 'git_diff'],
    ignoredPatterns: ['node_modules', 'dist', '.next', 'build', '__pycache__'],
    planningMode: true
  },
  frontend: {
    name: 'frontend',
    description: 'Optimised for React, Vue, HTML/CSS, and UI development',
    systemPromptAddition: `You are working on a frontend/UI project.
Prefer: component-based architecture, responsive design, accessibility best practices.
Always: check for console errors, test in multiple screen sizes, use semantic HTML.
File patterns to focus on: *.jsx, *.tsx, *.vue, *.svelte, *.css, *.scss, *.html
Avoid: large bundle sizes, inline styles, deprecated APIs.`,
    preferredTools: ['read_file', 'write_file', 'run_command', 'run_tests', 'list_directory', 'search_codebase', 'diff_files'],
    ignoredPatterns: ['node_modules', 'dist', '.next', 'build', 'coverage'],
    planningMode: false
  },
  'data-science': {
    name: 'data-science',
    description: 'Optimised for Python data analysis, ML, and Jupyter notebooks',
    systemPromptAddition: `You are working on a data science or machine learning project.
Prefer: pandas/numpy for data manipulation, clear variable names, reproducible code.
Always: check data shapes and types, handle missing values, document assumptions.
File patterns to focus on: *.py, *.ipynb, *.csv, *.json, requirements.txt
Avoid: memory inefficient operations on large datasets, hardcoded paths.`,
    preferredTools: ['read_file', 'write_file', 'run_command', 'run_tests', 'install_package', 'find_files', 'search_in_files'],
    ignoredPatterns: ['__pycache__', '.ipynb_checkpoints', 'venv', '.venv', 'data/raw'],
    planningMode: false
  },
  devops: {
    name: 'devops',
    description: 'Optimised for Docker, CI/CD, shell scripts, and infrastructure',
    systemPromptAddition: `You are working on DevOps, infrastructure, or deployment configuration.
Prefer: idempotent operations, clear logging, environment variable configuration, minimal images.
Always: validate syntax before applying, handle rollback scenarios, document commands.
File patterns to focus on: Dockerfile, docker-compose.yml, *.yaml, *.yml, *.sh, Makefile
Avoid: hardcoded credentials, latest tags in production, running as root.`,
    preferredTools: ['run_command', 'read_file', 'write_file', 'read_env', 'set_env_var', 'start_process', 'git_status'],
    ignoredPatterns: ['node_modules', '__pycache__', '.terraform', '*.tfstate'],
    planningMode: true
  },
  default: {
    name: 'default',
    description: 'General purpose — no specialisation',
    systemPromptAddition: '',
    preferredTools: [],
    ignoredPatterns: [],
    planningMode: false
  }
};

const SUPPORTED_PROFILES = Object.keys(BUILTIN_PROFILES);

/**
 * Returns the profile object for the given name (case-insensitive).
 */
function getProfile(name) {
  if (!name) return BUILTIN_PROFILES.default;
  const key = name.toLowerCase();
  if (BUILTIN_PROFILES[key]) {
    return BUILTIN_PROFILES[key];
  }
  throw new Error(`Unknown profile "${name}". Valid profiles: ${SUPPORTED_PROFILES.join(', ')}`);
}

/**
 * Returns array of all builtin profile objects.
 */
function listProfiles() {
  return Object.values(BUILTIN_PROFILES);
}

/**
 * Merges profile settings into config object.
 * Returns modified config (does not mutate original).
 */
function applyProfile(profile, config) {
  return {
    ...config,
    PLANNING_MODE: profile.planningMode,
    ACTIVE_PROFILE: profile.name
  };
}

/**
 * Returns the systemPromptAddition string for a profile name.
 */
function getProfileSystemPromptAddition(profileName) {
  try {
    const profile = getProfile(profileName);
    let addition = profile.systemPromptAddition || '';
    
    if (profile.preferredTools && profile.preferredTools.length > 0) {
      addition += '\n\nPREFERRED TOOLS FOR THIS PROFILE:\n' + profile.preferredTools.join(', ');
    }
    
    return addition;
  } catch {
    return '';
  }
}

/**
 * Loads a user-defined profile from a JSON file.
 */
function loadCustomProfile(filePath) {
  try {
    if (!fs.existsSync(filePath)) {
      return { success: false, error: `File not found: ${filePath}` };
    }
    const data = JSON.parse(fs.readFileSync(filePath, 'utf8'));
    
    // Validation
    if (!data.name || typeof data.name !== 'string' ||
        !data.description || typeof data.description !== 'string' ||
        !data.systemPromptAddition || typeof data.systemPromptAddition !== 'string') {
      return { success: false, error: 'Custom profile missing required fields: name, description, systemPromptAddition' };
    }

    const profile = {
      name: data.name,
      description: data.description,
      systemPromptAddition: data.systemPromptAddition,
      preferredTools: Array.isArray(data.preferredTools) ? data.preferredTools : [],
      ignoredPatterns: Array.isArray(data.ignoredPatterns) ? data.ignoredPatterns : [],
      planningMode: typeof data.planningMode === 'boolean' ? data.planningMode : false
    };

    return { success: true, profile };
  } catch (err) {
    return { success: false, error: err.message };
  }
}

module.exports = {
  getProfile,
  listProfiles,
  applyProfile,
  getProfileSystemPromptAddition,
  loadCustomProfile,
  SUPPORTED_PROFILES
};