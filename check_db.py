#!/usr/bin/env python3
import sqlite3
import os
import time

DB_PATH = "llm-router/llm_router.db"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Run the server first!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        while True:
            clear_screen()
            print("========================================")
            print("      LLM Rerouter Database Viewer      ")
            print("========================================")
            
            # --- 1. Print Overall Stats ---
            c.execute("SELECT COUNT(*) as count, SUM(cost) as total_cost FROM routing_logs")
            stats = c.fetchone()
            count = stats['count'] if stats['count'] else 0
            total_cost = stats['total_cost'] if stats['total_cost'] else 0.0
            
            c.execute("SELECT COUNT(*) as failed FROM routing_logs WHERE success=0")
            fails = c.fetchone()['failed']
            success_rate = ((count - fails) / count * 100) if count > 0 else 0
            
            print(f"Total Routing Decisions : {count}")
            print(f"Total Money Spent     : ${total_cost:.6f}")
            print(f"Overall Success Rate  : {success_rate:.1f}%")
            print("========================================\n")
            
            # --- 2. Print Best Performing Models ---
            print("--- Top Performing Models ---")
            c.execute("SELECT * FROM model_performance ORDER BY total_requests DESC, success_rate DESC LIMIT 5")
            perf = c.fetchall()
            if not perf:
                print("No performance data found. Send some prompts first!")
            else:
                for p in perf:
                    print(f"[{p['model_name']}]")
                    print(f"   Requests: {p['total_requests']} | Success Rate: {p['success_rate']*100:.1f}% | Avg Latency: {p['average_time']:.2f}s | Total Cost: ${p['total_cost']:.6f}")
            
            # --- 3. Print Latest Logs ---
            print("\n--- Last 5 Routing Decisions ---")
            c.execute("SELECT * FROM routing_logs ORDER BY timestamp DESC LIMIT 5")
            logs = c.fetchall()
            
            if not logs:
                print("No logs found.")
            else:
                for log in logs:
                    status = "✅ SUCCESS" if log['success'] else "❌ FAILED"
                    print(f"[{log['timestamp']}] {status}")
                    print(f"   Winner Model : {log['model_id']}")
                    print(f"   Expected Util: {log['expected_utility']:.4f}")
                    print(f"   Latency      : {log['time']:.2f}s")
                    print(f"   Prompt Snippet: {str(log['query'])[:50]}...")
                    print()
            
            print("----------------------------------------")
            choice = input("Press [Enter] to refresh, or [q] to quit: ").strip().lower()
            if choice == 'q':
                break
                
        conn.close()
        
    except Exception as e:
        print(f"\nError reading database: {e}")

if __name__ == "__main__":
    check_db()
