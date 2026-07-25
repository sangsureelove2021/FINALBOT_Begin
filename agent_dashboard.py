#!/usr/bin/env python3
"""
Agent Skills Dashboard - Monitor and manage all trading agents
"""

import time
import threading
import json
# import psutil  # Not available, use alternative method
from datetime import datetime
from typing import Dict, List, Optional

class AgentDashboard:
    def __init__(self):
        self.agents = {
            "main_bot": {"status": "running", "pid": None, "last_check": None},
            "enhanced_bot": {"status": "running", "pid": None, "last_check": None},
            "backtrader": {"status": "stopped", "pid": None, "last_check": None},
            "risk_management": {"status": "stopped", "pid": None, "last_check": None},
            "position_sizing": {"status": "stopped", "pid": None, "last_check": None},
            "kelly_criterion": {"status": "stopped", "pid": None, "last_check": None},
            "portfolio_analytics": {"status": "stopped", "pid": None, "last_check": None},
            "market_microstructure": {"status": "stopped", "pid": None, "last_check": None},
            "volatility_modeling": {"status": "stopped", "pid": None, "last_check": None},
            "trading_visualization": {"status": "stopped", "pid": None, "last_check": None}
        }
        
        self.skill_counts = {
            "total_skills": 67,
            "active_skills": 2,
            "available_skills": 65
        }
        
    def check_agent_status(self, agent_name: str) -> str:
        """Check if an agent process is running using tasklist"""
        try:
            import subprocess
            result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                output = result.stdout
                if agent_name in output.lower():
                    # Extract PID from tasklist output
                    lines = output.split('\n')
                    for line in lines:
                        if agent_name in line.lower() and 'python.exe' in line:
                            parts = line.split()
                            if len(parts) > 1:
                                pid = parts[1]
                                self.agents[agent_name]["pid"] = pid
                                self.agents[agent_name]["status"] = "running"
                                self.agents[agent_name]["last_check"] = datetime.now()
                                return "running"
        except Exception:
            pass
        
        self.agents[agent_name]["status"] = "stopped"
        self.agents[agent_name]["pid"] = None
        self.agents[agent_name]["last_check"] = datetime.now()
        return "stopped"
    
    def update_all_status(self):
        """Update status for all agents"""
        for agent_name in self.agents:
            self.check_agent_status(agent_name)
    
    def get_skill_info(self) -> Dict:
        """Get information about available skills"""
        skill_info = {
            "market_analysis": [
                "backtrader", "market-microstructure", "market-microstructure-traditional",
                "regime-detection", "signal-classification", "trend-following"
            ],
            "risk_management": [
                "risk-management", "position-sizing", "kelly-criterion", "portfolio-analytics",
                "exposure_limits", "drawdown_management", "circuit-breakers"
            ],
            "technical_analysis": [
                "ta-lib", "pandas-ta", "custom-indicators", "ohlcv-processing",
                "volatility-modeling", "liquidity-analysis", "correlation-analysis"
            ],
            "execution": [
                "dex-execution", "slippage-modeling", "order-book-analysis", 
                "trade-execution", "smart-order-routing"
            ],
            "portfolio": [
                "portfolio-analytics", "trade-accounting", "cost-basis-engine",
                "tax-liability-tracking", "wash-sale-detection", "performance-metrics"
            ],
            "crypto_specific": [
                "solana-rpc", "helius-api", "birdeye-api", "dexscreener-api",
                "coingecko-api", "defillama-api", "token-economics"
            ],
            "ml_ai": [
                "mean-reversion", "prediction-market-strategy", "machine-learning",
                "neural-networks", "random-forest", "svm-classification"
            ]
        }
        
        return skill_info
    
    def print_dashboard(self):
        """Print the complete dashboard"""
        print("\n" + "="*80)
        print("🤖 AGENT SKILLS DASHBOARD 🤖")
        print("="*80)
        print(f"📊 Total Skills Available: {self.skill_counts['total_skills']}")
        print(f"🟢 Active Skills: {self.skill_counts['active_skills']}")
        print(f"⚪ Available Skills: {self.skill_counts['available_skills']}")
        print("="*80)
        
        # Agent Status
        print("\n🔍 AGENT STATUS:")
        print("-" * 80)
        for agent_name, info in self.agents.items():
            status = info["status"]
            pid = info["pid"] or "N/A"
            last_check = info["last_check"].strftime("%H:%M:%S") if info["last_check"] else "N/A"
            
            if status == "running":
                status_icon = "🟢"
            else:
                status_icon = "🔴"
            
            print(f"{status_icon} {agent_name:20} | PID: {pid:6} | Last: {last_check}")
        
        # Skills by Category
        skill_info = self.get_skill_info()
        print("\n📚 SKILLS BY CATEGORY:")
        print("-" * 80)
        
        for category, skills in skill_info.items():
            print(f"\n📂 {category.replace('_', ' ').title()}:")
            for skill in skills:
                status = self.agents.get(skill, {}).get("status", "stopped")
                if status == "running":
                    icon = "🟢"
                else:
                    icon = "⚪"
                print(f"  {icon} {skill}")
        
        print("\n" + "="*80)
        print("💡 Commands:")
        print("  'start <agent>' - Start specific agent")
        print("  'stop <agent>'  - Stop specific agent")  
        print("  'status'        - Show this dashboard")
        print("  'all'           - Start all available skills")
        print("  'quit'          - Exit dashboard")
        print("="*80)
    
    def start_agent(self, agent_name: str):
        """Start a specific agent"""
        if agent_name in self.agents:
            import subprocess
            try:
                if agent_name == "main_bot":
                    subprocess.Popen(["python", "main.py"])
                elif agent_name == "enhanced_bot":
                    subprocess.Popen(["python", "enhanced_bot.py"])
                elif agent_name == "backtrader":
                    subprocess.Popen(["python", ".agents\\skills\\backtrader\\scripts\\backtest_strategy.py"])
                elif agent_name == "risk_management":
                    subprocess.Popen(["python", ".agents\\skills\\risk-management\\scripts\\risk_dashboard.py"])
                elif agent_name == "position_sizing":
                    subprocess.Popen(["python", ".agents\\skills\\position-sizing\\scripts\\size_calculator.py"])
                elif agent_name == "kelly_criterion":
                    subprocess.Popen(["python", ".agents\\skills\\kelly-criterion\\scripts\\kelly_calculator.py"])
                elif agent_name == "portfolio_analytics":
                    subprocess.Popen(["python", ".agents\\skills\\portfolio-analytics\\scripts\\portfolio_analyzer.py"])
                elif agent_name == "market_microstructure":
                    subprocess.Popen(["python", ".agents\\skills\\market-microstructure\\scripts\\microstructure_analyzer.py"])
                elif agent_name == "volatility_modeling":
                    subprocess.Popen(["python", ".agents\\skills\\volatility-modeling\\scripts\\volatility_forecast.py"])
                elif agent_name == "trading_visualization":
                    subprocess.Popen(["python", ".agents\\skills\\trading-visualization\\scripts\\visualizer.py"])
                
                print(f"✅ Started {agent_name}")
                time.sleep(2)  # Wait for process to start
                self.update_all_status()
                
            except Exception as e:
                print(f"❌ Failed to start {agent_name}: {e}")
        else:
            print(f"❌ Agent {agent_name} not found")
    
    def start_all_agents(self):
        """Start all available agents"""
        print("🚀 Starting all agent skills...")
        
        # Start main trading bots
        self.start_agent("main_bot")
        self.start_agent("enhanced_bot")
        
        # Start analysis skills
        self.start_agent("backtrader")
        self.start_agent("risk_management")
        self.start_agent("position_sizing")
        self.start_agent("kelly_criterion")
        self.start_agent("portfolio_analytics")
        self.start_agent("market_microstructure")
        self.start_agent("volatility_modeling")
        self.start_agent("trading_visualization")
        
        print("✅ All agents started!")
        self.update_all_status()
    
    def interactive_mode(self):
        """Run interactive dashboard"""
        print("🤖 Agent Skills Dashboard - Interactive Mode")
        
        # Initial status check
        self.update_all_status()
        self.print_dashboard()
        
        while True:
            try:
                command = input("\n💬 Enter command (or 'help'): ").strip().lower()
                
                if command == "help":
                    print("\nAvailable commands:")
                    print("  status       - Show dashboard")
                    print("  all          - Start all agents")
                    print("  start <name> - Start specific agent")
                    print("  stop <name>   - Stop specific agent")
                    print("  skills       - Show all skills")
                    print("  quit         - Exit dashboard")
                
                elif command == "status":
                    self.update_all_status()
                    self.print_dashboard()
                
                elif command == "all":
                    self.start_all_agents()
                    self.print_dashboard()
                
                elif command == "skills":
                    skill_info = self.get_skill_info()
                    print("\n📚 All Available Skills:")
                    for category, skills in skill_info.items():
                        print(f"\n{category.replace('_', ' ').title()}: {len(skills)} skills")
                        for skill in skills:
                            print(f"  - {skill}")
                
                elif command.startswith("start "):
                    agent_name = command[6:]
                    self.start_agent(agent_name)
                    self.print_dashboard()
                
                elif command.startswith("stop "):
                    agent_name = command[5:]
                    print(f"❌ Stop functionality not implemented yet for {agent_name}")
                
                elif command == "quit":
                    print("👋 Goodbye!")
                    break
                
                else:
                    print("❌ Unknown command. Type 'help' for available commands.")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function"""
    dashboard = AgentDashboard()
    dashboard.interactive_mode()

if __name__ == "__main__":
    main()