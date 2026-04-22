#!/usr/bin/env python3
import json
import os
import ssl
import subprocess
import sys
import time
import urllib.request

# --- Configuration & Files ---
APP_HOME = os.getenv("LLM_REROUTER_HOME", os.path.expanduser("~/.llm_rerouter"))
os.makedirs(APP_HOME, exist_ok=True)
ENV_FILE = os.path.join(APP_HOME, ".env")
DISABLED_MODELS_FILE = os.path.join(APP_HOME, "disabled_models.json")

# --- Colors & UI Elements ---
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_BLUE = "\033[34m"
C_MAGENTA = "\033[35m"

ICON_CHECK = f"{C_GREEN}✓{C_RESET}"
ICON_X = f"{C_RED}✗{C_RESET}"
ICON_GEAR = "⚙"
ICON_ARROW = "➜"

# --- Provider Metadata ---
PROVIDER_KEYS = {
    "openai": [("OPENAI_API_KEY", "OpenAI API Key")],
    "anthropic": [("ANTHROPIC_API_KEY", "Anthropic API Key")],
    "cohere": [("COHERE_API_KEY", "Cohere API Key")],
    "huggingface": [("HUGGINGFACE_API_KEY", "Hugging Face API Key")],
    "gemini": [("GEMINI_API_KEY", "Google Gemini API Key")],
    "custom/local": [
        ("CUSTOM_LLM_BASE_URL", "Base URL (e.g., http://localhost:11434/v1)"),
        ("CUSTOM_LLM_API_KEY", "API Key (or dummy)"),
    ],
}

# --- Utility Functions ---


def load_env():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    env_vars[key.strip()] = val.strip().strip("'").strip('"')
    return env_vars


def save_env(env_vars):
    with open(ENV_FILE, "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")


def load_disabled_models():
    if os.path.exists(DISABLED_MODELS_FILE):
        try:
            with open(DISABLED_MODELS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()


def save_disabled_models(disabled_set):
    with open(DISABLED_MODELS_FILE, "w") as f:
        json.dump(list(disabled_set), f)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title):
    clear_screen()
    width = 64
    print(f"{C_CYAN}┏" + "━" * (width - 2) + "┓")
    print(f"┃ {C_BOLD}{title:^{width - 4}}{C_RESET}{C_CYAN} ┃")
    print(f"{C_CYAN}┗" + "━" * (width - 2) + f"┛{C_RESET}\n")


def print_status(msg, type="info"):
    icon = {"success": ICON_CHECK, "error": ICON_X, "info": ICON_GEAR, "warn": "!"}.get(
        type, ICON_GEAR
    )
    color = {"success": C_GREEN, "error": C_RED, "info": C_CYAN, "warn": C_YELLOW}.get(
        type, C_CYAN
    )
    print(f"  {color}{icon}{C_RESET} {msg}")


def prompt(text, default="", color=C_YELLOW):
    p_text = f"  {C_BOLD}{text}{C_RESET}"
    if default:
        p_text += f" {C_CYAN}[{default}]{C_RESET}"
    p_text += f" {ICON_ARROW} "
    val = input(p_text).strip()
    return val if val else default


# --- Discovery Logic ---


def sync_discover_ollama(base_url="http://localhost:11434"):
    discovered = []
    try:
        url = (
            base_url.replace("/v1", "/api/tags")
            if base_url.endswith("/v1")
            else f"{base_url}/api/tags"
        )
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                for model in data.get("models", []):
                    name = model.get("name")
                    if name:
                        discovered.append(
                            {
                                "id": name,
                                "name": f"Ollama: {name}",
                                "provider": "ollama",
                            }
                        )
    except:
        pass
    return discovered


def sync_discover_openai_compat(base_url, api_key, provider_name):
    discovered = []
    try:
        url = (
            f"{base_url}/models" if not base_url.endswith("/") else f"{base_url}models"
        )
        req = urllib.request.Request(url)
        if api_key and api_key != "dummy":
            req.add_header("Authorization", f"Bearer {api_key}")
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=3, context=ctx) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                for model in data.get("data", []):
                    m_id = model.get("id")
                    if m_id:
                        if (
                            provider_name == "openai"
                            and "gpt" not in m_id
                            and "o1" not in m_id
                        ):
                            continue
                        discovered.append(
                            {
                                "id": m_id,
                                "name": f"{provider_name.title()}: {m_id}",
                                "provider": provider_name,
                            }
                        )
    except:
        pass
    return discovered


def get_all_models(env_vars):
    models = []
    # Custom/Ollama
    c_url = env_vars.get("CUSTOM_LLM_BASE_URL")
    if c_url:
        if "11434" in c_url:
            models.extend(sync_discover_ollama(c_url))
        else:
            models.extend(
                sync_discover_openai_compat(
                    c_url, env_vars.get("CUSTOM_LLM_API_KEY", "dummy"), "custom"
                )
            )
    # OpenAI
    oa_key = env_vars.get("OPENAI_API_KEY")
    if oa_key and oa_key != "dummy":
        models.extend(
            sync_discover_openai_compat("https://api.openai.com/v1", oa_key, "openai")
        )
    # Gemini
    g_key = env_vars.get("GEMINI_API_KEY")
    if g_key and g_key != "dummy":
        # Get models from OpenAI compat endpoint
        compat_models = sync_discover_openai_compat(
            "https://generativelanguage.googleapis.com/v1beta/openai",
            g_key,
            "gemini",
        )
        compat_ids = {m["id"] for m in compat_models}
        models.extend(compat_models)
        
        # Also poll the native endpoint to catch missing 2.5/3.1 aliases that aren't on compat yet
        try:
            import urllib.request
            import json
            import ssl
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={g_key}"
            req = urllib.request.Request(url)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req, timeout=3, context=ctx) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    for model in data.get("models", []):
                        m_id = model.get("name")
                        if m_id and m_id not in compat_ids:
                            models.append({
                                "id": m_id,
                                "name": f"Gemini: {m_id}",
                                "provider": "gemini"
                            })
        except:
            pass
            
    return models


# --- Setup Wizard ---


def wizard_global_settings(env_vars):
    print_header("Step 2: Intelligence Coefficients")
    print_status("Tune how the router prioritizes Accuracy vs Cost vs Speed.")

    print(f"\n  {C_BOLD}Utility Formula:{C_RESET}")
    print(
        f"  {C_CYAN}EU(m) = p * {C_BOLD}R{C_RESET}{C_CYAN} - {C_BOLD}α{C_RESET}{C_CYAN} * cost - {C_BOLD}β{C_RESET}{C_CYAN} * time{C_RESET}\n"
    )

    env_vars["REWARD"] = prompt("Success Value (R)", env_vars.get("REWARD", "1.0"))
    env_vars["COST_SENSITIVITY"] = prompt(
        "Cost Penalty (α)", env_vars.get("COST_SENSITIVITY", "0.5")
    )
    env_vars["TIME_SENSITIVITY"] = prompt(
        "Time Penalty (β)", env_vars.get("TIME_SENSITIVITY", "0.5")
    )

    save_env(env_vars)
    print_status("Settings updated.", "success")
    time.sleep(0.8)


def wizard_routing_strategy(env_vars):
    print_header("Step 1: Routing Strategy")
    print(
        f"  {C_CYAN}[1]{C_RESET} {C_BOLD}Expected Utility{C_RESET} (Single-shot, Fast)"
    )
    print(
        f"  {C_CYAN}[2]{C_RESET} {C_BOLD}Tiered Assessment{C_RESET} (Sequential, Verified)\n"
    )

    choice = prompt("Select Strategy", env_vars.get("DEFAULT_STRATEGY", "1"))
    if choice in ["2", "tiered_assessment"]:
        env_vars["DEFAULT_STRATEGY"] = "tiered_assessment"
        print_status("Strategy set to Tiered Assessment.", "success")
    else:
        env_vars["DEFAULT_STRATEGY"] = "expected_utility"
        print_status("Strategy set to Expected Utility.", "success")

    save_env(env_vars)
    time.sleep(0.8)


def wizard_providers(env_vars):
    while True:
        print_header("Step 3: Provider Credentials")

        providers = ["OpenAI", "Google Gemini", "Anthropic", "Cohere", "Custom/Ollama"]
        for i, p in enumerate(providers, 1):
            key_check = (
                ICON_CHECK
                if any(
                    env_vars.get(k[0])
                    for k in PROVIDER_KEYS[
                        p.lower()
                        .replace("google ", "")
                        .replace("custom/ollama", "custom/local")
                    ]
                )
                else ICON_X
            )
            print(f"  {C_CYAN}[{i}]{C_RESET} {p:<15} {key_check}")

        print(f"\n  {C_CYAN}[c]{C_RESET} Continue to Model Selection")

        choice = prompt("Action", "c").lower()
        if choice == "c":
            break

        mapping = {
            "1": "openai",
            "2": "gemini",
            "3": "anthropic",
            "4": "cohere",
            "5": "custom/local",
        }
        if choice in mapping:
            provider = mapping[choice]
            print(f"\n  {C_MAGENTA}--- {provider.upper()} CONFIGURATION ---{C_RESET}")
            for env_key, desc in PROVIDER_KEYS[provider]:
                cur = env_vars.get(env_key, "")
                masked = (
                    cur
                    if "URL" in env_key
                    else (cur[:4] + "*" * 12 if len(cur) > 8 else "None")
                )
                new_val = prompt(f"{desc} (Current: {masked})")
                if new_val:
                    env_vars[env_key] = new_val
            save_env(env_vars)


def wizard_model_management(env_vars):
    disabled = load_disabled_models()
    all_models = get_all_models(env_vars)
    page = 0
    PAGE_SIZE = 10

    while True:
        print_header("Step 4: Model Visibility & Sentiment")
        print_status(
            "Toggle models 'ON' or 'OFF' and select the Sentiment Analysis model.\n"
        )

        if not all_models:
            print_status("No models found! Check your API keys in Step 3.", "warn")
            prompt("Press Enter to return", "")
            return

        total_pages = (len(all_models) + PAGE_SIZE - 1) // PAGE_SIZE
        if page >= total_pages and total_pages > 0:
            page = total_pages - 1

        start_idx = page * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        current_page_models = all_models[start_idx:end_idx]

        for i, m in enumerate(current_page_models, start_idx + 1):
            status_icon = ICON_X if m["id"] in disabled else ICON_CHECK
            status_text = (
                f"{C_RED}[OFF]{C_RESET}"
                if m["id"] in disabled
                else f"{C_GREEN}[ ON]{C_RESET}"
            )
            cur_sentiment = env_vars.get("SENTIMENT_MODEL_ID", "")
            sentiment_tag = (
                f" {C_MAGENTA}[SENTIMENT]{C_RESET}" if m["id"] == cur_sentiment else ""
            )
            print(
                f"  {C_CYAN}[{i:2}]{C_RESET} {status_text} {m['name']}{sentiment_tag}"
            )

        print(f"\n  Page {page + 1} of {total_pages}")
        if page > 0:
            print(f"  {C_CYAN}[p]{C_RESET} Previous Page")
        if page < total_pages - 1:
            print(f"  {C_CYAN}[n]{C_RESET} Next Page")

        print(f"  {C_CYAN}[s]{C_RESET} {C_BOLD}Save & Start Server{C_RESET}")
        print(f"  {C_CYAN}[r]{C_RESET} Refresh Discovery")
        print(f"  {C_CYAN}[f]{C_RESET} Set # as Sentiment Model (Feedback Analysis)")
        print(f"  {C_CYAN}[#]{C_RESET} Enter number to toggle model ON/OFF")

        choice = prompt("Choice", "s").lower()

        if choice == "s":
            save_disabled_models(disabled)
            # We pass the disabled list to the env so the router can read it easily
            env_vars["DISABLED_MODELS"] = ",".join(list(disabled))
            save_env(env_vars)
            break
        elif choice == "n" and page < total_pages - 1:
            page += 1
            continue
        elif choice == "p" and page > 0:
            page -= 1
            continue
        elif choice == "r":
            print_status("Scanning for models...")
            all_models = get_all_models(env_vars)
            page = 0
            continue
        elif choice.startswith("f") and len(choice) > 1:
            try:
                idx = int(choice[1:]) - 1
                if 0 <= idx < len(all_models):
                    m_id = all_models[idx]["id"]
                    env_vars["SENTIMENT_MODEL_ID"] = m_id
                    print_status(f"Sentiment model set to: {m_id}", "success")
                    time.sleep(0.5)
            except ValueError:
                pass
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(all_models):
                m_id = all_models[idx]["id"]
                if m_id in disabled:
                    disabled.remove(m_id)
                else:
                    disabled.add(m_id)


def start_server(env_vars):
    print_header("Final Step: Ignition")
    print_status("Building environment and launching core...")

    env = os.environ.copy()
    env.update(env_vars)
    env["PYTHONPATH"] = "llm-router"

    print(f"\n  {C_GREEN}{C_BOLD}Server active at http://0.0.0.0:8000{C_RESET}")
    print(f"  {C_CYAN}Press [CTRL+C] to stop the process.{C_RESET}\n")
    print(f"{C_BLUE}" + "━" * 64 + f"{C_RESET}")

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "src.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--no-access-log",
            ],
            cwd="llm-router",
            env=env,
        )
    except KeyboardInterrupt:
        print(f"\n\n  {C_YELLOW}Shutdown signal received. Server stopped.{C_RESET}")
    except Exception as e:
        print_status(f"Crash detected: {e}", "error")


def main():
    env_vars = load_env()

    # Check if we should skip to start
    if os.path.exists(ENV_FILE):
        print_header("LLM Rerouter")
        print_status("Welcome back! Existing config detected.\n")
        action = prompt("(s)tart server or (r)econfigure?", "s").lower()
        if action == "s":
            start_server(env_vars)
            return

    try:
        print_header("LLM Rerouter Setup")
        print(f"  Welcome to the {C_BOLD}LLM Rerouter{C_RESET} initialization wizard.")
        print(f"  Optimized for {C_GREEN}Utility{C_RESET}.\n")
        prompt("Press Enter to begin", "")

        wizard_routing_strategy(env_vars)
        wizard_global_settings(env_vars)
        wizard_providers(env_vars)
        wizard_model_management(env_vars)
        start_server(env_vars)

    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {C_RED}Setup aborted.{C_RESET}")


if __name__ == "__main__":
    main()
