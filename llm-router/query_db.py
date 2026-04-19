import json
import sqlite3


def get_logs():
    try:
        import os

        db_path = (
            "llm_router.db" if os.path.exists("llm_router.db") else "../llm_router.db"
        )
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        print("\n=== Recent Routing Logs ===")
        c.execute("SELECT * FROM routing_logs ORDER BY timestamp DESC LIMIT 5")
        logs = c.fetchall()

        if not logs:
            print("No logs found. The database is empty.")
        else:
            for log in logs:
                print(f"ID: {log['id']}")
                print(f"Timestamp: {log['timestamp']}")
                print(f"Model ID: {log['model_id']}")
                print(f"Expected Utility: {log['expected_utility']}")
                print(f"Cost: {log['cost']}")
                print(f"Time: {log['time']}")
                print(f"Probability: {log['probability']}")
                print(f"Success: {log['success']}")
                print(f"Query: {log['query'][:100]}...")
                print("-" * 40)

        print("\n=== Model Performance ===")
        c.execute(
            "SELECT * FROM model_performance ORDER BY success_rate DESC, total_requests DESC"
        )
        perf = c.fetchall()

        if not perf:
            print("No performance data found.")
        else:
            for p in perf:
                print(f"Model: {p['model_name']} ({p['model_id']})")
                print(f"Total Requests: {p['total_requests']}")
                print(f"Total Cost: ${p['total_cost']:.6f}")
                print(f"Average Time: {p['average_time']:.4f}s")
                print(f"Success Rate: {p['success_rate'] * 100:.2f}%")
                print("-" * 40)

        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")


if __name__ == "__main__":
    get_logs()
