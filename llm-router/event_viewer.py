#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import sys
import time

DB_PATH = "llm_router.db"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def clear_database():
    """Delete all records from the routing_logs and model_performance tables."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}. Nothing to clear.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Clear logs
        c.execute("DELETE FROM routing_logs")
        # Clear performance metrics so utility resets too
        c.execute("DELETE FROM model_performance")

        conn.commit()
        conn.close()
        print("Successfully cleared all historical data from the database.")
    except Exception as e:
        print(f"Error clearing database: {e}")


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

        row = dict(log)
        rc_id = row.get("reality_check_id")
        if rc_id:
            print(f"RC Decision ID: {rc_id}")

        print(
            f"Metrics:   Time: {log['time']:.2f}s | Cost: ${log['cost']:.6f} | Utility: {log['expected_utility']:.4f}"
        )
        print(
            f"Tokens:    {log['prompt_tokens']} prompt + {log['completion_tokens']} completion = {log['total_tokens']} total"
        )

        # Show User Sentiment
        sentiment = (
            log["user_sentiment"] if "user_sentiment" in dict(log).keys() else None
        )
        if sentiment:
            s_map = {
                "happy": "😊 Happy",
                "unhappy": "😟 Unhappy",
                "indeterminate": "😐 Indeterminate",
            }
            print(f"Sentiment: {s_map.get(sentiment, sentiment)}")

        # Show Agent Features
        row = dict(log)
        feat_json = row.get("features_json")
        if feat_json:
            try:
                f = json.loads(feat_json)
                print("\n[AGENT FEATURES (40-Dim Set)]")
                print(
                    f"  Structural : nodes:{f.get('struct_nodes', 0):.0f}, h:{f.get('struct_height', 0):.0f}, loops:{f.get('struct_loop_dens', 0):.2f}, func:{f.get('struct_func_dens', 0):.2f}"
                )
                print(
                    f"  State/Trace: iter:{f.get('trace_iter_idx', 0):.0f}, ratio:{f.get('trace_iter_ratio', 0):.2f}, err:{f.get('trace_err_flag', 0):.0f}"
                )
                print(
                    f"  Tools (f) : rd:{f.get('trace_read_freq', 0):.2f}, wr:{f.get('trace_write_freq', 0):.2f}, ex:{f.get('trace_exec_freq', 0):.2f}, sh:{f.get('trace_search_freq', 0):.2f}"
                )
                print(
                    f"  Metadata   : pos:{f.get('meta_pos_con', 0):.0f}, neg:{f.get('meta_neg_con', 0):.0f}, grounded:{f.get('meta_grounding', 0):.0f}"
                )
                print(
                    f"  Semantic   : gen:{f.get('sem_gen', 0):.0f}, fix:{f.get('sem_fix', 0):.0f}, refac:{f.get('sem_refactor', 0):.0f}, docs:{f.get('sem_docs', 0):.0f}"
                )
                print(
                    f"  Telemetry  : p_len:{f.get('tele_p_len', 0):.0f}, depth:{f.get('tele_hist_depth', 0):.0f}, pressure:{f.get('tele_ctx_pressure', 0):.2f}"
                )
                print(
                    f"  Model FP   : {' '.join([f'{f.get(f'model_fp_{i}', 0):.2f}' for i in range(8)])}"
                )
            except Exception:
                pass

        # Show Model Comparison Table
        context = row.get("routing_context")
        if context:
            try:
                decisions = json.loads(context)
                print("\n[MODEL COMPARISON]")
                print(f"{'Model Name':<30} | {'Utility':>8} | {'Prob':>6}")
                print("-" * 31 + "|" + "-" * 10 + "|" + "-" * 8)
                for d in decisions:
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
            try:
                c.execute("SELECT * FROM routing_logs ORDER BY timestamp DESC LIMIT 5")
                logs = c.fetchall()
            except sqlite3.OperationalError:
                print("\nError: Table 'routing_logs' not found. Is the server running?")
                break

            if not logs:
                print("\nNo events logged yet. Try sending a prompt to the server!")
            else:
                for idx, log in enumerate(logs, 1):
                    status = "✅ SUCCESS" if log["success"] else "❌ FAILED"
                    print(f"[{idx}] [{log['timestamp']}] {status}")
                    print(f"    Model: {log['model_name']} ({log['model_id']})")
                    print(f"    Time: {log['time']:.2f}s | Cost: ${log['cost']:.6f}")

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
    parser = argparse.ArgumentParser(description="LLM Rerouter Event Viewer")
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear all historical data from the database",
    )

    args = parser.parse_args()

    if args.clear:
        confirm = (
            input(
                "Are you sure you want to delete ALL logs and performance data? (y/N): "
            )
            .strip()
            .lower()
        )
        if confirm == "y":
            clear_database()
        else:
            print("Abort.")
    else:
        view_events()
