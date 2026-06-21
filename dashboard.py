import http.server
import socketserver
import json
import os
import sys
import subprocess
from pathlib import Path

PORT = 5000
PROJECT_ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = PROJECT_ROOT / "config" / "settings.json"

# HTML/CSS/JS template for the complete trading workstation
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FINALBOT Workstation</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #080c14;
            --primary: #10b981;
            --primary-glow: rgba(16, 185, 129, 0.4);
            --danger: #ef4444;
            --danger-glow: rgba(239, 68, 68, 0.4);
            --accent: #06b6d4;
            --accent-glow: rgba(6, 182, 212, 0.4);
            --glass-bg: rgba(17, 25, 40, 0.7);
            --glass-border: rgba(255, 255, 255, 0.08);
            --text-color: #f3f4f6;
            --text-muted: #9ca3af;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Outfit', sans-serif;
            -webkit-font-smoothing: antialiased;
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            overflow-x: hidden;
            background-image: 
                radial-gradient(at 5% 5%, rgba(6, 182, 212, 0.12) 0px, transparent 50%),
                radial-gradient(at 95% 95%, rgba(16, 185, 129, 0.12) 0px, transparent 50%);
        }

        .container {
            width: 100%;
            max-width: 1300px;
            padding: 40px 20px;
            display: flex;
            flex-direction: column;
            gap: 30px;
        }

        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 30px;
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.4);
        }

        .logo-section h1 {
            font-size: 26px;
            font-weight: 800;
            letter-spacing: 1px;
            background: linear-gradient(to right, #06b6d4, #10b981);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .logo-section p {
            font-size: 13px;
            color: var(--text-muted);
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(16, 185, 129, 0.1);
            border: 1px solid rgba(16, 185, 129, 0.2);
            padding: 8px 18px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            color: var(--primary);
        }

        .status-dot {
            width: 10px;
            height: 10px;
            background-color: var(--primary);
            border-radius: 50%;
            box-shadow: 0 0 10px var(--primary);
            animation: pulse 1.8s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.9); opacity: 0.6; }
            50% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 15px var(--primary); }
            100% { transform: scale(0.9); opacity: 0.6; }
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
        }

        @media (min-width: 950px) {
            .grid {
                grid-template-columns: 1.2fr 1.8fr;
            }
        }

        .card {
            background: var(--glass-bg);
            backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        .card-title {
            font-size: 18px;
            font-weight: 600;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 12px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .card-title span {
            font-size: 12px;
            color: var(--text-muted);
            font-weight: 400;
        }

        .form-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }

        .form-group {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }

        .form-group.full-width {
            grid-column: span 2;
        }

        label {
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
        }

        input[type="text"], input[type="number"], input[type="password"], select {
            width: 100%;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 10px 14px;
            color: var(--text-color);
            font-size: 14px;
            outline: none;
            transition: all 0.25s ease;
        }

        input[type="text"]:focus, input[type="number"]:focus, input[type="password"]:focus, select:focus {
            border-color: var(--accent);
            background: rgba(255, 255, 255, 0.05);
        }

        /* Toggle Switches */
        .toggle-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
            max-height: 400px;
            overflow-y: auto;
            padding-right: 5px;
        }

        .toggle-list::-webkit-scrollbar {
            width: 5px;
        }
        .toggle-list::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
        }

        .toggle-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 18px;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid rgba(255, 255, 255, 0.03);
            border-radius: 14px;
            transition: all 0.2s ease;
        }

        .toggle-item:hover {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.06);
            transform: translateX(2px);
        }

        .toggle-label {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .toggle-name {
            font-weight: 600;
            font-size: 14px;
        }

        .toggle-desc {
            font-size: 11px;
            color: var(--text-muted);
        }

        .switch {
            position: relative;
            display: inline-block;
            width: 44px;
            height: 24px;
            flex-shrink: 0;
        }

        .switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }

        .slider {
            position: absolute;
            cursor: pointer;
            top: 0; left: 0; right: 0; bottom: 0;
            background-color: rgba(255, 255, 255, 0.15);
            transition: .25s;
            border-radius: 30px;
        }

        .slider:before {
            position: absolute;
            content: "";
            height: 16px;
            width: 16px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .25s;
            border-radius: 50%;
        }

        input:checked + .slider {
            background-color: var(--primary);
            box-shadow: 0 0 10px var(--primary-glow);
        }

        input:checked + .slider:before {
            transform: translateX(20px);
        }

        /* Trading Mode Cards */
        .mode-selector {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .mode-card {
            border: 1px solid var(--glass-border);
            background: rgba(255, 255, 255, 0.02);
            border-radius: 16px;
            padding: 14px;
            cursor: pointer;
            text-align: center;
            transition: all 0.25s ease;
        }

        .mode-card:hover {
            background: rgba(255, 255, 255, 0.05);
            border-color: rgba(255, 255, 255, 0.15);
        }

        .mode-card.active {
            border-color: var(--accent);
            background: rgba(6, 182, 212, 0.08);
            box-shadow: 0 0 15px rgba(6, 182, 212, 0.15);
        }

        .mode-title {
            font-size: 14px;
            font-weight: 600;
        }

        .mode-desc {
            font-size: 10px;
            color: var(--text-muted);
            margin-top: 3px;
        }

        /* Button controls */
        .btn {
            background: linear-gradient(135deg, var(--accent), #0891b2);
            border: none;
            color: #fff;
            padding: 12px 24px;
            border-radius: 14px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.25s ease;
            text-align: center;
            text-decoration: none;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px var(--accent-glow);
        }

        .btn-danger {
            background: linear-gradient(135deg, var(--danger), #dc2626);
        }

        .btn-danger:hover {
            box-shadow: 0 5px 15px var(--danger-glow);
        }

        .btn-disabled {
            background: rgba(255, 255, 255, 0.08);
            color: var(--text-muted);
            cursor: not-allowed;
            transform: none !important;
            box-shadow: none !important;
        }

        .progress-container {
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            overflow: hidden;
            position: relative;
        }

        .progress-bar {
            width: 0%;
            height: 100%;
            background: linear-gradient(to right, var(--accent), var(--primary));
            transition: width 0.3s ease;
        }

        /* Result Report tables */
        .results-box {
            display: flex;
            flex-direction: column;
            gap: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            padding-top: 20px;
        }

        .results-summary-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
        }

        .summary-tile {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--glass-border);
            border-radius: 14px;
            padding: 14px;
            text-align: center;
        }

        .summary-tile .val {
            font-size: 20px;
            font-weight: 800;
            color: var(--accent);
            margin-top: 4px;
        }

        .summary-tile.wins .val { color: var(--primary); }
        .summary-tile.losses .val { color: var(--danger); }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
            margin-top: 8px;
        }

        th, td {
            padding: 10px 14px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.03);
        }

        th {
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            font-size: 11px;
            letter-spacing: 0.5px;
        }

        tr:hover td {
            background: rgba(255, 255, 255, 0.01);
        }

        .text-green { color: var(--primary); font-weight: 600; }
        .text-red { color: var(--danger); font-weight: 600; }

        .notification {
            position: fixed;
            bottom: 25px;
            right: 25px;
            background: rgba(16, 185, 129, 0.95);
            color: #fff;
            padding: 14px 24px;
            border-radius: 12px;
            font-weight: 600;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .notification.show {
            transform: translateY(0);
            opacity: 1;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="logo-section">
                <h1>FINALBOT</h1>
                <p>Trading Control Station</p>
            </div>
            <div class="status-badge">
                <div class="status-dot"></div>
                LIVE WORKSTATION
            </div>
        </header>

        <!-- Live Chart Card -->
        <div class="card" style="height: 550px; gap: 16px;">
            <div class="card-title" style="border: none; padding-bottom: 0; display: flex; justify-content: space-between; align-items: center;">
                Live Interactive Market Chart
                <select id="chart-symbol-select" onchange="loadChart(this.value)" style="width: auto; padding: 6px 12px; font-size: 13px; border-radius: 8px;">
                    <option value="EURUSD">EURUSD</option>
                    <option value="USDJPY">USDJPY</option>
                    <option value="GBPUSD">GBPUSD</option>
                    <option value="EURJPY">EURJPY</option>
                    <option value="EURGBP">EURGBP</option>
                    <option value="AUDUSD">AUDUSD</option>
                    <option value="EURUSD-OTC">EURUSD-OTC (Regular FX Chart)</option>
                    <option value="USDJPY-OTC">USDJPY-OTC (Regular FX Chart)</option>
                    <option value="GBPUSD-OTC">GBPUSD-OTC (Regular FX Chart)</option>
                    <option value="EURJPY-OTC">EURJPY-OTC (Regular FX Chart)</option>
                    <option value="EURGBP-OTC">EURGBP-OTC (Regular FX Chart)</option>
                </select>
            </div>
            <div style="flex-grow: 1; border-radius: 14px; overflow: hidden; border: 1px solid rgba(255, 255, 255, 0.05); position: relative; height: 100%;">
                <div id="tradingview-container" style="width: 100%; height: 100%;"></div>
            </div>
        </div>

        <div class="grid">
            <!-- Left Column: Config Panel & Controls -->
            <div style="display: flex; flex-direction: column; gap: 30px;">
                <!-- Trading Mode -->
                <div class="card">
                    <div class="card-title">Trading Mode</div>
                    <div class="mode-selector">
                        <div class="mode-card" id="mode-TRADE" onclick="selectMode('Auto_BOT')">
                            <div class="mode-title">Auto Trade</div>
                            <div class="mode-desc">Direct execution, no filters</div>
                        </div>
                        <div class="mode-card" id="mode-SIGNAL" onclick="selectMode('Signal_BOT')">
                            <div class="mode-title">Signal Only</div>
                            <div class="mode-desc">Log decisions & signal feed</div>
                        </div>
                        <div class="mode-card" id="mode-AI" onclick="selectMode('Ai_BOT')">
                            <div class="mode-title">AI Eval</div>
                            <div class="mode-desc">Full model analysis & logic</div>
                        </div>
                        <div class="mode-card" id="mode-HYBRID" onclick="selectMode('Hybrid_AiBOT')">
                            <div class="mode-title">Hybrid</div>
                            <div class="mode-desc">AI + human execution queue</div>
                        </div>
                    </div>
                </div>

                <!-- Connection & Credentials -->
                <div class="card">
                    <div class="card-title">Connection & Credentials</div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>IQ Option Email</label>
                            <input type="text" id="cfg-iq-email" placeholder="email@example.com" onchange="updateParam('account.iq_email', this.value)">
                        </div>
                        <div class="form-group full-width">
                            <label>IQ Option Password</label>
                            <input type="password" id="cfg-iq-password" placeholder="••••••••" onchange="updateParam('account.iq_password', this.value)">
                        </div>
                    </div>
                </div>

                <!-- Custom Parameters Panel -->
                <div class="card">
                    <div class="card-title">System Settings</div>
                    <div class="form-grid">
                        <div class="form-group">
                            <label>Account Type</label>
                            <select id="cfg-account-type" onchange="updateParam('account.account_type', this.value)">
                                <option value="PRACTICE">PRACTICE (Demo)</option>
                                <option value="REAL">REAL (Money)</option>
                            </select>
                        </div>
                        <div class="field-row">
                            <label>Stake per Trade (USD)</label>
                            <input type="number" id="cfg-stake" step="1" onchange="updateParam('account.stake_per_trade', parseFloat(this.value))">
                        </div>
                        <div class="form-group">
                            <label>Min Quality Conf (%)</label>
                            <input type="number" id="cfg-confidence" min="40" max="100" onchange="updateParam('execution_gate.min_confidence', parseInt(this.value))">
                        </div>
                        <div class="form-group">
                            <label>Max Block Score</label>
                            <input type="number" id="cfg-block" min="0" max="100" onchange="updateParam('execution_gate.max_block_score', parseInt(this.value))">
                        </div>
                        <div class="form-group">
                            <label>Max Session Trades</label>
                            <input type="number" id="cfg-max-trades" min="1" onchange="updateParam('limits.max_trades_per_session', parseInt(this.value))">
                        </div>
                        <div class="form-group">
                            <label>Cooldown After Loss (m)</label>
                            <input type="number" id="cfg-cooldown" min="0" onchange="updateParam('limits.cooldown_minutes_after_loss', parseInt(this.value))">
                        </div>
                        <div class="form-group">
                            <label>Max Daily Loss (USD)</label>
                            <input type="number" id="cfg-daily-loss" min="0" placeholder="Unlimited" onchange="updateParam('limits.max_daily_loss', this.value ? parseFloat(this.value) : null)">
                        </div>
                        <div class="form-group">
                            <label>Trading Hours</label>
                            <input type="text" id="cfg-trading-hours" placeholder="00:00-23:59" onchange="updateParam('session.trading_hours', this.value)">
                        </div>
                        <div class="form-group">
                            <label>Timezone</label>
                            <input type="text" id="cfg-timezone" placeholder="Asia/Bangkok" onchange="updateParam('session.timezone', this.value)">
                        </div>
                    </div>
                </div>

            </div>

            <!-- Right Column: Markets & Strategies lists -->
            <div style="display: flex; flex-direction: column; gap: 30px;">
                <!-- Active Strategies Toggle -->
                <div class="card">
                    <div class="card-title">
                        Active Strategies
                        <span id="strategy-count">0 active</span>
                    </div>
                    <div class="toggle-list" id="strategies-list"></div>
                </div>

                <!-- Active Markets Toggle -->
                <div class="card">
                    <div class="card-title">
                        Active Markets
                        <span id="market-count">0 active</span>
                    </div>
                    <div class="toggle-list" id="symbols-list"></div>
                </div>
            </div>
        </div>
    </div>

    <div class="notification" id="toast">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 0C4.48 0 0 4.48 0 10C0 15.52 4.48 20 10 20C15.52 20 20 15.52 20 10C20 4.48 15.52 0 10 0ZM8 15L3 10L4.41 8.59L8 12.17L15.59 4.58L17 6L8 15Z" fill="currentColor"/>
        </svg>
        <span>Configuration saved successfully!</span>
    </div>

    <script>
        const AVAILABLE_SYMBOLS = [
            { id: "EURUSD", name: "EURUSD", type: "Regular" },
            { id: "USDJPY", name: "USDJPY", type: "Regular" },
            { id: "GBPUSD", name: "GBPUSD", type: "Regular" },
            { id: "EURJPY", name: "EURJPY", type: "Regular" },
            { id: "EURGBP", name: "EURGBP", type: "Regular" },
            { id: "AUDUSD", name: "AUDUSD", type: "Regular" },
            { id: "EURUSD-OTC", name: "EURUSD-OTC", type: "OTC" },
            { id: "USDJPY-OTC", name: "USDJPY-OTC", type: "OTC" },
            { id: "GBPUSD-OTC", name: "GBPUSD-OTC", type: "OTC" },
            { id: "EURJPY-OTC", name: "EURJPY-OTC", type: "OTC" },
            { id: "EURGBP-OTC", name: "EURGBP-OTC", type: "OTC" }
        ];

        const AVAILABLE_STRATEGIES = [
            { id: "rejection_5m_pa", name: "Rejection 5m PA", desc: "1-Minute Rejection at M5 S/R Levels (1m Expiry)" },
            { id: "pa_snr_strategy", name: "PA S&R Reversal", desc: "Price Action key support & resistance bounces" },
            { id: "sr_fakeout_rejection", name: "S&R Fakeout Rejection", desc: "Trap Sweep patterns at key zones" },
            { id: "pin_bar_scalper", name: "Pin Bar Scalper", desc: "Scalping bounces off key wicks" },
            { id: "bb_rsi_confluence", name: "BB + RSI Confluence", desc: "Bollinger Bands extreme bounce with RSI" },
            { id: "rsi_extreme_bounce", name: "RSI Extreme Bounce", desc: "Deep oversold/overbought indicator reversal" },
            { id: "rsi_reversal", name: "RSI Reversal", desc: "Standard RSI overbought/oversold crossing" },
            { id: "stochastic_crossover", name: "Stochastic Crossover", desc: "Stochastic extreme zone intersection" },
            { id: "engulfing_scalper", name: "Engulfing Scalper", desc: "Bearish/Bullish engulfing momentum shifts" },
            { id: "ema_crossover", name: "EMA Crossover", desc: "EMA 20/50 fast/slow trend crossovers" },
            { id: "macd_crossover", name: "MACD Crossover", desc: "MACD line and signal crossovers" },
            { id: "ema_ribbon_momentum", name: "EMA Ribbon Momentum", desc: "Multi-EMA momentum expansions" },
            { id: "triple_confluence", name: "Triple Confluence", desc: "Triple indicators consensus trend rider" },
            { id: "compression_breakout", name: "Compression Breakout", desc: "BOS expansions from low volatility squeezes" }
        ];

        let configData = {};
        async function fetchConfig() {
            try {
                const response = await fetch('/api/config');
                configData = await response.json();
                renderUI();
            } catch (err) {
                console.error("Failed to load config", err);
            }
        }

        async function saveConfig() {
            try {
                const response = await fetch('/api/config', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(configData)
                });
                if (response.ok) {
                    showToast();
                }
            } catch (err) {
                console.error("Failed to save config", err);
            }
        }

        function renderUI() {
            // Render Mode Selector
            const mode = configData.account?.trading_mode || "Auto_BOT";
            document.querySelectorAll('.mode-card').forEach(c => c.classList.remove('active'));
            if (mode === "Auto_BOT") document.getElementById('mode-TRADE').classList.add('active');
            else if (mode === "Signal_BOT") document.getElementById('mode-SIGNAL').classList.add('active');
            else if (mode === "Ai_BOT") document.getElementById('mode-AI').classList.add('active');
            else if (mode === "Hybrid_AiBOT") document.getElementById('mode-HYBRID').classList.add('active');

            // Set inputs values
            document.getElementById('cfg-account-type').value = configData.account?.account_type || "PRACTICE";
            document.getElementById('cfg-stake').value = configData.account?.stake_per_trade || 30;
            document.getElementById('cfg-confidence').value = configData.execution_gate?.min_confidence || 80;
            document.getElementById('cfg-block').value = configData.execution_gate?.max_block_score || 40;
            document.getElementById('cfg-max-trades').value = configData.limits?.max_trades_per_session || 999;
            document.getElementById('cfg-cooldown').value = configData.limits?.cooldown_minutes_after_loss || 0;
            document.getElementById('cfg-daily-loss').value = configData.limits?.max_daily_loss || '';

            document.getElementById('cfg-iq-email').value = configData.account?.iq_email || "";
            document.getElementById('cfg-iq-password').value = configData.account?.iq_password || "";

            // Timing parameters
            document.getElementById('cfg-trading-hours').value = configData.session?.trading_hours || "00:00-23:59";
            document.getElementById('cfg-timezone').value = configData.session?.timezone || "Asia/Bangkok";

            // Render Strategies
            const activeStrats = configData.active_strategies || ["rejection_5m_pa"];
            const strategiesContainer = document.getElementById('strategies-list');
            strategiesContainer.innerHTML = '';
            
            AVAILABLE_STRATEGIES.forEach(strat => {
                const isActive = activeStrats.includes(strat.id);
                const el = document.createElement('div');
                el.className = 'toggle-item';
                el.innerHTML = `
                    <div class="toggle-label">
                        <div class="toggle-name">${strat.name}</div>
                        <div class="toggle-desc">${strat.desc}</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" ${isActive ? 'checked' : ''} onchange="toggleStrategy('${strat.id}', this.checked)">
                        <span class="slider"></span>
                    </label>
                `;
                strategiesContainer.appendChild(el);
            });
            document.getElementById('strategy-count').innerText = `${activeStrats.length} active`;

            // Render Symbols
            const activeSymbols = configData.symbols || ["EURUSD-OTC"];
            const symbolsContainer = document.getElementById('symbols-list');
            symbolsContainer.innerHTML = '';

            AVAILABLE_SYMBOLS.forEach(sym => {
                const isActive = activeSymbols.includes(sym.id);
                const el = document.createElement('div');
                el.className = 'toggle-item';
                el.innerHTML = `
                    <div class="toggle-label">
                        <div class="toggle-name">${sym.name}</div>
                        <div class="toggle-desc">Market Type: ${sym.type}</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" ${isActive ? 'checked' : ''} onchange="toggleSymbol('${sym.id}', this.checked)">
                        <span class="slider"></span>
                    </label>
                `;
                symbolsContainer.appendChild(el);
            });
            document.getElementById('market-count').innerText = `${activeSymbols.length} active`;
        }

        function updateParam(path, value) {
            const parts = path.split('.');
            let obj = configData;
            for (let i = 0; i < parts.length - 1; i++) {
                if (!obj[parts[i]]) obj[parts[i]] = {};
                obj = obj[parts[i]];
            }
            obj[parts[parts.length - 1]] = value;
            saveConfig();
        }

        function toggleStrategy(stratId, isChecked) {
            if (!configData.active_strategies) configData.active_strategies = [];
            if (isChecked) {
                if (!configData.active_strategies.includes(stratId)) configData.active_strategies.push(stratId);
            } else {
                configData.active_strategies = configData.active_strategies.filter(id => id !== stratId);
            }
            saveConfig();
        }

        function toggleSymbol(symId, isChecked) {
            if (!configData.symbols) configData.symbols = [];
            if (isChecked) {
                if (!configData.symbols.includes(symId)) configData.symbols.push(symId);
            } else {
                configData.symbols = configData.symbols.filter(id => id !== symId);
            }
            saveConfig();
        }

        function selectMode(newMode) {
            if (!configData.account) configData.account = {};
            configData.account.trading_mode = newMode;
            saveConfig();
            renderUI();
        }

        function showToast() {
            const toast = document.getElementById('toast');
            toast.classList.add('show');
            setTimeout(() => { toast.classList.remove('show'); }, 3000);
        }

        function loadChart(symbol) {
            let tvSymbol = symbol.replace('-OTC', '');
            tvSymbol = "FX:" + tvSymbol;

            const container = document.getElementById('tradingview-container');
            container.innerHTML = ''; 

            const script = document.createElement('script');
            script.type = 'text/javascript';
            script.src = 'https://s3.tradingview.com/tv.js';
            script.onload = () => {
                new TradingView.widget({
                    "width": "100%",
                    "height": "100%",
                    "symbol": tvSymbol,
                    "interval": "1",
                    "timezone": "Asia/Bangkok",
                    "theme": "dark",
                    "style": "1",
                    "locale": "en",
                    "enable_publishing": false,
                    "hide_side_toolbar": false,
                    "allow_symbol_change": true,
                    "container_id": "tradingview-container"
                });
            };
            document.head.appendChild(script);
        }

        // Init load
        fetchConfig();
        loadChart('EURUSD');
    </script>
</body>
</html>
"""

class DashboardHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.wfile.write(json.dumps(config, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        if self.path == '/api/config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                new_config = json.loads(post_data.decode('utf-8'))
                with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                    json.dump(new_config, f, indent=2, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
        else:
            self.send_error(404, "File not found")

def main():
    Handler = DashboardHTTPRequestHandler
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"\n=======================================================")
        print(f"FINALBOT TRADING WORKSTATION IS ACTIVE")
        print(f"=======================================================")
        print(f"Open browser and go to: http://localhost:{PORT}")
        print(f"Press Ctrl+C in this terminal to stop the workstation server")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping workstation server...")

if __name__ == "__main__":
    main()
