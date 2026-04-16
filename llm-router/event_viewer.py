#!/usr/bin/env python3
import json
import os
import sqlite3
import time

DB_PATH = "llm_router.db"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def format_payload(payload_str, truncate_lines=None):
    """
    Format payload for display.
    Maintains original data structure via JSON parsing but improves
    readability by expanding escaped newlines into actual line breaks.
    """
    if not payload_str or payload_str == "{}":
        return "  None"

    try:
        # Attempt to parse as JSON to maintain structure
        data = json.loads(payload_str)
        formatted = json.dumps(data, indent=2, ensure_ascii=False)

        # Expand escaped newlines inside strings for human readability
        # This makes multi-line content (like LLM prompts/responses) easy to read
        formatted = formatted.replace("\\n", "\n")

        if truncate_lines:
            lines = formatted.split("\n")
            if len(lines) > truncate_lines:
                return "\n".join(lines[:truncate_lines]) + "\n  ... (truncated)"
        return formatted
    except:
        # Fallback for non-JSON content or malformed strings
        raw = payload_str.replace("\\n", "\n")
        if truncate_lines:
            lines = raw.split("\n")
            if len(lines) > truncate_lines:
                return "\n".join(lines[:truncate_lines]) + "\n  ... (truncated)"
        return raw


def show_detail_view(log):
    """
    Detailed view showing un-truncated request and response payloads.
    """
    while True:
        clear_screen()
        print("=====================================================")
        print("                Event Detail View                    ")
        print("=====================================================")
        print(f"Timestamp: {log['timestamp']}")
        status = "✅ SUCCESS" if log["success"] else "❌ FAILED"
        print(f"Status:    {status}")
        print(f"Model:     {log['model_name']} ({log['model_id']})")
        print(
            f"Metrics:   Time: {log['time']:.2f}s | Cost: ${log['cost']:.6f} | Utility: {log['expected_utility']:.4f}"
        )
        print(
            f"Tokens:    {log['prompt_tokens']} prompt + {log['completion_tokens']} completion = {log['total_tokens']} total"
        )

        # Show Model Comparison Table
        context = log["routing_context"] if "routing_context" in log.keys() else None
        if context:
            try:
                decisions = json.loads(context)
                print("\n[MODEL COMPARISON]")
                print(f"{'Model Name':<30} | {'Utility':>8} | {'Prob':>6}")
                print("-" * 31 + "|" + "-" * 10 + "|" + "-" * 8)
                for d in decisions:
                    # Highlight the selected model with >>
                    prefix = ">>" if d["model_id"] == log["model_id"] else "  "
                    name = d.get("name", d["model_id"])[:27]
                    print(
                        f"{prefix} {name:<27} | {d['expected_utility']:>8.4f} | {d['probability']:>6.2f}"
                    )
            except:
                pass

        print("-" * 53)

        print("\n[FULL REQUEST PAYLOAD]")
        print(format_payload(log["request_payload"]))

        print("\n" + "-" * 53)
        print("\n[FULL RESPONSE PAYLOAD]")
        print(format_payload(log["response_payload"]))

        print("\n" + "=" * 53)
        input("\nPress [Enter] to return to list view: ")
        return


def view_events():
    """
    Main loop for viewing the latest events.
    """
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Send some requests first!")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        while True:
            clear_screen()
            print("=====================================================")
            print("         LLM Rerouter Event & Debug Viewer           ")
            print("=====================================================")

            # Retrieve last 5 events
            c.execute("SELECT * FROM routing_logs ORDER BY timestamp DESC LIMIT 5")
            logs = c.fetchall()

            if not logs:
                print("\nNo events logged yet. Try sending a prompt to the server!")
            else:
                for idx, log in enumerate(logs, 1):
                    status = "✅ SUCCESS" if log["success"] else "❌ FAILED"
                    print(f"[{idx}] [{log['timestamp']}] {status}")
                    print(f"    Model: {log['model_name']} ({log['model_id']})")
                    print(f"    Time: {log['time']:.2f}s | Cost: ${log['cost']:.6f}")

                    # Short preview of the request content
                    req_preview = format_payload(
                        log["request_payload"], truncate_lines=2
                    )
                    print(f"    Req Preview: {req_preview.strip()}")
                    print("-" * 53)

            print("\nCommands: [Enter] Refresh | [1-5] View Details | [q] Quit")
            choice = input("Choice: ").strip().lower()

            if choice == "q":
                break
            elif choice.isdigit():
                val = int(choice)
                if 1 <= val <= len(logs):
                    show_detail_view(logs[val - 1])

        conn.close()
    except Exception as e:
        print(f"Error reading database: {e}")


if __name__ == "__main__":
    view_events()
