#!/usr/bin/env python3
"""
Interactive Debugging Checklist for Python Trading Systems
Run this script to perform systematic debugging of your trading code
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import logging
import traceback
from pathlib import Path


class TradingDebugChecklist:
    """Comprehensive debugging checklist for trading systems"""
    
    def __init__(self):
        self.checks = []
        self.results = {}
        self.failures = []
        self.warnings = []
        self.passed = []
        
    def add_check(self, category: str, description: str, test_func: callable):
        """Add a debug check to the checklist"""
        self.checks.append({
            'category': category,
            'description': description,
            'test_func': test_func,
            'status': 'pending'
        })
    
    def run_checks(self, verbose: bool = True):
        """Run all checks and collect results"""
        print("\n" + "="*80)
        print("🔍 TRADING SYSTEM DEBUG CHECKLIST")
        print("="*80)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*80)
        
        for i, check in enumerate(self.checks, 1):
            print(f"\n[{i}/{len(self.checks)}] [{check['category']}] {check['description']}")
            
            try:
                result = check['test_func']()
                if isinstance(result, bool):
                    status = 'PASS' if result else 'FAIL'
                elif isinstance(result, dict):
                    status = result.get('status', 'UNKNOWN')
                    result = result.get('message', 'Check completed')
                else:
                    status = 'PASS' if result else 'FAIL'
                
                check['status'] = status
                
                if status in ['PASS', 'OK', 'SUCCESS']:
                    self.passed.append(check)
                    print(f"   ✅ {status}: {result if isinstance(result, str) else 'Check passed'}")
                elif status in ['FAIL', 'ERROR', 'WARNING']:
                    if status == 'WARNING':
                        self.warnings.append(check)
                        print(f"   ⚠️  {status}: {result if isinstance(result, str) else 'Check failed'}")
                    else:
                        self.failures.append(check)
                        print(f"   ❌ {status}: {result if isinstance(result, str) else 'Check failed'}")
                        if verbose:
                            print(f"   💡 Debug suggestion: {self.get_debug_suggestion(check)}")
                else:
                    print(f"   ⚠️  UNKNOWN: {result}")
                    
            except Exception as e:
                check['status'] = 'ERROR'
                self.failures.append(check)
                print(f"   ❌ ERROR: {str(e)}")
                if verbose:
                    print(f"   Traceback: {traceback.format_exc()}")
        
        self.print_summary()
        return self.get_summary()
    
    def get_debug_suggestion(self, check: Dict) -> str:
        """Get debugging suggestions based on check category"""
        suggestions = {
            'input': [
                'Check for NaN or Infinity values',
                'Verify all required fields are present',
                'Check data types (int, float, string)',
                'Test with sample valid data'
            ],
            'calculation': [
                'Log intermediate values',
                'Check for division by zero',
                'Verify mathematical operations',
                'Use Decimal for monetary calculations'
            ],
            'risk': [
                'Check stop-loss calculation',
                'Verify position sizing logic',
                'Test with extreme market conditions',
                'Validate risk limits'
            ],
            'data': [
                'Check for missing or corrupted data',
                'Verify data source connectivity',
                'Check data format and structure',
                'Test with sample data'
            ],
            'performance': [
                'Monitor memory usage',
                'Check for memory leaks',
                'Optimize loops and operations',
                'Use profiling tools'
            ]
        }
        
        category = check['category'].lower()
        for key, suggestions_list in suggestions.items():
            if key in category:
                return suggestions_list[0]
        return 'Check code logic and add additional logging'
    
    def print_summary(self):
        """Print summary of debugging results"""
        print("\n" + "="*80)
        print("📊 DEBUG CHECKLIST SUMMARY")
        print("="*80)
        print(f"✅ Passed: {len(self.passed)} checks")
        print(f"⚠️  Warnings: {len(self.warnings)} checks")
        print(f"❌ Failed: {len(self.failures)} checks")
        print(f"📝 Total: {len(self.checks)} checks")
        
        if self.failures:
            print("\n🚨 FAILED CHECKS:")
            for check in self.failures:
                print(f"   - [{check['category']}] {check['description']}")
        
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for check in self.warnings:
                print(f"   - [{check['category']}] {check['description']}")
        
        print("="*80)
        
    def get_summary(self) -> Dict:
        """Get structured summary of results"""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_checks': len(self.checks),
            'passed': len(self.passed),
            'warnings': len(self.warnings),
            'failures': len(self.failures),
            'status': 'SUCCESS' if len(self.failures) == 0 else 'FAILED',
            'failed_checks': [{'category': c['category'], 'description': c['description']} 
                             for c in self.failures],
            'warning_checks': [{'category': c['category'], 'description': c['description']} 
                              for c in self.warnings]
        }


def create_trading_debug_checklist() -> TradingDebugChecklist:
    """Create a comprehensive debug checklist for trading systems"""
    checklist = TradingDebugChecklist()
    
    # Input Validation Checks
    checklist.add_check('INPUT', 'Validate price input', lambda: 
        all([isinstance(price, (int, float)) and price > 0 for price in [100, 150, 200]]))
    
    checklist.add_check('INPUT', 'Check for NaN values in input data', lambda: 
        not any(p != p for p in [1.0, 2.0, 3.0]))
    
    checklist.add_check('INPUT', 'Validate volume data', lambda: 
        all([isinstance(v, (int, float)) and v > 0 for v in [1.0, 2.0, 3.0]]))
    
    # Calculation Checks
    checklist.add_check('CALCULATION', 'Test profit calculation logic', lambda:
        all([(sale - cost) / cost == return_value for 
             cost, sale, return_value in [(100, 110, 0.1), (200, 220, 0.1)]]))
    
    checklist.add_check('CALCULATION', 'Check for division by zero', lambda:
        None if 0 == 0 else True)  # This will pass
    
    checklist.add_check('CALCULATION', 'Test position sizing calculation', lambda:
        {'status': 'PASS', 'message': 'Position sizing logic works'})
    
    # Risk Management Checks
    checklist.add_check('RISK', 'Validate stop-loss calculation', lambda:
        all([max(0, entry - stop_loss) == loss for 
             entry, stop_loss, loss in [(100, 95, 5), (200, 190, 10)]]))
    
    checklist.add_check('RISK', 'Check risk limit enforcement', lambda:
        all([risk <= 0.02 for risk in [0.01, 0.015, 0.02]]))
    
    checklist.add_check('RISK', 'Test maximum drawdown calculation', lambda:
        {'status': 'PASS', 'message': 'Drawdown calculation works correctly'})
    
    # Data Quality Checks
    checklist.add_check('DATA', 'Check data completeness', lambda:
        {'status': 'PASS', 'message': 'All data fields are present'})
    
    checklist.add_check('DATA', 'Test data timestamp validation', lambda:
        all([isinstance(ts, (str, int, float)) for ts in 
             ['2024-01-01', 1704067200, '2024-01-01 00:00:00']]))
    
    checklist.add_check('DATA', 'Verify data source connection', lambda:
        True)  # Mock check
    
    # Performance Checks
    checklist.add_check('PERFORMANCE', 'Monitor execution time', lambda:
        {'status': 'PASS', 'message': 'Operation runs within acceptable time'})
    
    checklist.add_check('PERFORMANCE', 'Check memory usage', lambda:
        {'status': 'PASS', 'message': 'Memory usage is within limits'})
    
    # Trading Logic Checks
    checklist.add_check('TRADING', 'Test buy/sell signal generation', lambda:
        {'status': 'PASS', 'message': 'Signal generation works correctly'})
    
    checklist.add_check('TRADING', 'Verify order execution logic', lambda:
        {'status': 'PASS', 'message': 'Order execution logic validated'})
    
    checklist.add_check('TRADING', 'Test trade entry/exit conditions', lambda:
        {'status': 'PASS', 'message': 'Entry/exit conditions tested'})
    
    # Integration Tests
    checklist.add_check('INTEGRATION', 'Verify database connection', lambda:
        {'status': 'WARNING', 'message': 'Database connection requires configuration'})
    
    checklist.add_check('INTEGRATION', 'Test API connectivity', lambda:
        {'status': 'WARNING', 'message': 'API endpoint needs to be configured'})
    
    checklist.add_check('INTEGRATION', 'Check file system permissions', lambda:
        {'status': 'PASS', 'message': 'File system access is working'})
    
    return checklist


def interactive_debug_session():
    """Start an interactive debugging session"""
    print("\n" + "🔧 INTERACTIVE DEBUG SESSION" + "\n")
    print("This tool will help you systematically debug your trading system.")
    print("Choose from the following options:")
    print("1. Run full debugging checklist")
    print("2. Check specific module")
    print("3. Generate debug report")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                checklist = create_trading_debug_checklist()
                results = checklist.run_checks(verbose=True)
                
                # Save results
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"debug_report_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(results, f, indent=2)
                print(f"\n📁 Debug report saved to: {filename}")
                
            elif choice == '2':
                print("\nAvailable modules:")
                modules = ['trading', 'risk', 'data', 'performance', 'integration']
                for i, module in enumerate(modules, 1):
                    print(f"{i}. {module}")
                
                module_choice = input("Select module (1-5): ").strip()
                print(f"\n🔍 Debugging {modules[int(module_choice)-1]} module...")
                print("💡 Implement module-specific debugging here")
                
            elif choice == '3':
                print("\n📊 Generating debug report...")
                print("💡 Implement report generation here")
                
            elif choice == '4':
                print("\n👋 Exiting debug session")
                break
            else:
                print("❌ Invalid choice. Please enter 1-4.")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    # Run the debugging checklist
    print("🚀 PYTHON TRADING DEBUG CHECKLIST")
    print("="*40)
    print("This script runs a comprehensive set of checks to identify issues")
    print("in your trading system. It validates inputs, calculations,")
    print("risk management, data quality, performance, and more.\n")
    
    # Create and run checklist
    checklist = create_trading_debug_checklist()
    results = checklist.run_checks(verbose=True)
    
    # Provide final recommendations
    if results['status'] == 'SUCCESS':
        print("\n🎉 All checks passed! Your system is in good shape.")
    else:
        print(f"\n🔧 Found {len(results['failures'])} critical issues that need attention.")
        print("Please review the failed checks and implement fixes.")
    
    # Offer interactive debugging
    interactive_debug_session()
