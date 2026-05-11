#!/usr/bin/env python3
import json
import logging
import os
import ssl
import subprocess
import sys
import time
import urllib.request

import inquirer

# Set up simple file logging
APP_HOME = os.getenv("REALITY_ROUTER_HOME", os.path.expanduser("~/.reality_router"))
os.makedirs(APP_HOME, exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG, filename=os.path.join(APP_HOME, "wizard_debug.log")
)
logger = logging.getLogger("wizard")

# --- Configuration & Files ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REALITY_ROUTER_DIR = os.path.join(SCRIPT_DIR, "reality-router")
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


def check_docker():
    """Check if docker and docker compose are available"""
    try:
        subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        # Check for 'docker compose' (v2)
        subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except:
        return False


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
    logger.debug("Clearing screen: executing system('clear' or 'cls')")
    os.system("cls" if os.name == "nt" else "clear")


def print_header(title):
    clear_screen()
    width = 64
    header = (
        f"{C_CYAN}┏"
        + "━" * (width - 2)
        + "┓\n"
        + f"┃ {C_BOLD}{title:^{width - 4}}{C_RESET}{C_CYAN} ┃\n"
        + f"{C_CYAN}┗"
        + "━" * (width - 2)
        + f"┛{C_RESET}\n"
    )
    print(header)
    logger.debug(f"Printed header: {title}")


def print_status(msg, type="info"):
    icon = {"success": ICON_CHECK, "error": ICON_X, "info": ICON_GEAR, "warn": "!"}.get(
        type, ICON_GEAR
    )
    color = {"success": C_GREEN, "error": C_RED, "info": C_CYAN, "warn": C_YELLOW}.get(
        type, C_CYAN
    )
    print(f"  {color}{icon}{C_RESET} {msg}")
    logger.debug(f"Printed status: {msg} [type={type}]")


def prompt(text, default="", color=C_YELLOW):
    questions = [inquirer.Text("value", message=text, default=default)]
    answers = inquirer.prompt(questions)
    if answers:
        return answers["value"].strip()
    return default


# --- Discovery Logic ---


def sync_discover_ollama(base_url="http://localhost:11434"):
    discovered = []
    try:
        base_url = base_url.rstrip("/")
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
    except Exception as e:
        print(f"  \033[93m[WARN] Failed to connect to Ollama at {base_url}: {e}\033[0m")
        logger.error(f"Failed to discover Ollama models: {e}")
    return discovered


def sync_discover_openai_compat(base_url, api_key, provider_name):
    discovered = []
    try:
        base_url = base_url.rstrip("/")
        url = f"{base_url}/models"
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
                        if m_id.startswith("models/"):
                            m_id = m_id[7:]
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
    except Exception as e:
        print(
            f"  \033[93m[WARN] Failed to connect to {provider_name} API at {base_url}: {e}\033[0m"
        )
        logger.error(f"Failed to discover {provider_name} models: {e}")
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
                        if m_id:
                            if m_id.startswith("models/"):
                                m_id = m_id[7:]
                            if m_id not in compat_ids:
                                models.append(
                                    {
                                        "id": m_id,
                                        "name": f"Gemini: {m_id}",
                                        "provider": "gemini",
                                    }
                                )
        except:
            pass
    logger.debug(f"Found {len(models)} models.")
    return models


# --- Setup Wizard ---


def wizard_global_settings(env_vars):
    print_header("Step 2: Intelligence Coefficients")
    print_status("Tune how the router prioritizes Accuracy vs Cost vs Speed.")

    print(f"\n  {C_BOLD}Utility Formula:{C_RESET}")
    print(
        f"  {C_CYAN}EU(m) = p * {C_BOLD}R{C_RESET}{C_CYAN} - {C_BOLD}α{C_RESET}{C_CYAN} * cost - {C_BOLD}β{C_RESET}{C_CYAN} * time{C_RESET}\n"
    )

    questions = [
        inquirer.Text(
            "reward", message="Success Value (R)", default=env_vars.get("REWARD", "1.0")
        ),
        inquirer.Text(
            "alpha",
            message="Cost Penalty (α)",
            default=env_vars.get("COST_SENSITIVITY", "0.5"),
        ),
        inquirer.Text(
            "beta",
            message="Time Penalty (β)",
            default=env_vars.get("TIME_SENSITIVITY", "0.5"),
        ),
    ]
    answers = inquirer.prompt(questions)
    if not answers:
        print(f"\n  {C_RED}Wizard aborted.{C_RESET}")
        sys.exit(0)

    env_vars["REWARD"] = answers["reward"].strip()
    env_vars["COST_SENSITIVITY"] = answers["alpha"].strip()
    env_vars["TIME_SENSITIVITY"] = answers["beta"].strip()

    save_env(env_vars)
    print_status("Settings updated.", "success")
    time.sleep(0.8)


def wizard_routing_strategy(env_vars):
    print_header("Step 1: Routing Strategy")

    questions = [
        inquirer.List(
            "strategy",
            message="Select Routing Strategy",
            choices=[
                ("Expected Utility (Single-shot, Fast)", "expected_utility"),
                ("Tiered Assessment (Sequential, Verified)", "tiered_assessment"),
            ],
            default="expected_utility"
            if env_vars.get("DEFAULT_STRATEGY") != "tiered_assessment"
            else "tiered_assessment",
        )
    ]
    answers = inquirer.prompt(questions)

    if not answers:
        print(f"\n  {C_RED}Wizard aborted.{C_RESET}")
        sys.exit(0)

    env_vars["DEFAULT_STRATEGY"] = answers["strategy"]

    if answers["strategy"] == "tiered_assessment":
        print_status("Strategy set to Tiered Assessment.", "success")
    else:
        print_status("Strategy set to Expected Utility.", "success")

    save_env(env_vars)
    time.sleep(0.8)


def wizard_providers(env_vars):
    providers_list = [
        ("openai", "OpenAI"),
        ("gemini", "Google Gemini"),
        ("anthropic", "Anthropic"),
        ("cohere", "Cohere"),
        ("custom/local", "Custom/Ollama"),
    ]

    while True:
        print_header("Step 3: Provider Credentials")

        choices = []
        for p_id, p_name in providers_list:
            is_configured = any(env_vars.get(k[0]) for k in PROVIDER_KEYS[p_id])
            display = f"{p_name:<15} {'✓' if is_configured else '✗'}"
            choices.append((display, p_id))

        choices.append(("Continue to Model Selection", "continue"))

        questions = [
            inquirer.List(
                "provider", message="Select Provider to Configure", choices=choices
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            print(f"\n  {C_RED}Wizard aborted.{C_RESET}")
            sys.exit(0)

        choice = answers["provider"]

        if choice == "continue":
            break

        print(f"\n  {C_MAGENTA}--- {choice.upper()} CONFIGURATION ---{C_RESET}")

        for env_key, desc in PROVIDER_KEYS[choice]:
            cur = env_vars.get(env_key, "")
            masked = (
                cur
                if "URL" in env_key
                else (cur[:4] + "*" * 12 if len(cur) > 8 else "None")
            )

            val_q = [
                inquirer.Text(
                    "value",
                    message=f"{desc} (Current: {masked})",
                )
            ]
            val_a = inquirer.prompt(val_q)
            if not val_a:
                print(f"\n  {C_RED}Wizard aborted.{C_RESET}")
                sys.exit(0)

            new_val = val_a["value"].strip()
            if new_val:
                env_vars[env_key] = new_val
        save_env(env_vars)


def wizard_model_management(env_vars):
    disabled = load_disabled_models()
    all_models = get_all_models(env_vars)

    while True:
        print_header("Step 4: Model Visibility & Sentiment")
        print_status(
            "Toggle models 'ON' or 'OFF' and select the Sentiment Analysis model.\n"
        )

        if not all_models:
            print_status("No models found! Check your API keys in Step 3.", "warn")
            questions = [
                inquirer.List(
                    "no_models",
                    message="Options",
                    choices=[("Refresh Discovery", "r"), ("Go Back", "b")],
                )
            ]
            ans = inquirer.prompt(questions)
            if not ans or ans["no_models"] == "b":
                return
            if ans["no_models"] == "r":
                print_status("Scanning for models...")
                all_models = get_all_models(env_vars)
                continue

        # Step 4.1: Toggle active models
        model_choices = [(m["name"], m["id"]) for m in all_models]
        default_checked = [m["id"] for m in all_models if m["id"] not in disabled]

        questions = [
            inquirer.Checkbox(
                "active_models",
                message="Toggle models ON [Space] and continue [Enter]",
                choices=model_choices,
                default=default_checked,
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            print(f"\n  {C_RED}Wizard aborted.{C_RESET}")
            sys.exit(0)

        active_ids = answers["active_models"]
        disabled = set(m["id"] for m in all_models if m["id"] not in active_ids)

        active_model_choices = [
            (m["name"], m["id"]) for m in all_models if m["id"] in active_ids
        ]

        if not active_model_choices:
            print_status("You must have at least one active model.", "error")
            time.sleep(2)
            continue

        # Step 4.2: Select sentiment model
        sentiment_all_choices = [(m["name"], m["id"]) for m in all_models]
        sentiment_q = [
            inquirer.List(
                "sentiment_model",
                message="Select Sentiment Analysis model",
                choices=sentiment_all_choices,
                default=env_vars.get("SENTIMENT_MODEL_ID")
                if env_vars.get("SENTIMENT_MODEL_ID") in [m["id"] for m in all_models]
                else None,
            )
        ]

        sentiment_a = inquirer.prompt(sentiment_q)
        if not sentiment_a:
            print(f"\n  {C_RED}Wizard aborted.{C_RESET}")
            sys.exit(0)

        env_vars["SENTIMENT_MODEL_ID"] = sentiment_a["sentiment_model"]

        save_disabled_models(disabled)
        env_vars["DISABLED_MODELS"] = ",".join(list(disabled))
        save_env(env_vars)
        break


def start_server(env_vars):
    print_header("Final Step: Ignition")
    print_status("Building environment and launching core...")

    env = os.environ.copy()
    env.update(env_vars)
    # Ensure PYTHONPATH includes the absolute path to the core source
    env["PYTHONPATH"] = os.path.abspath(REALITY_ROUTER_DIR)

    print(f"\n  {C_GREEN}{C_BOLD}Server active at http://0.0.0.0:8000{C_RESET}")
    sentiment_model = env_vars.get("SENTIMENT_MODEL_ID", "Not Configured")
    print(f"  {C_YELLOW}Sentiment Model: {sentiment_model}{C_RESET}")
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
            cwd=REALITY_ROUTER_DIR,
            env=env,
        )
    except KeyboardInterrupt:
        print(f"\n\n  {C_YELLOW}Shutdown signal received. Server stopped.{C_RESET}")
    except Exception as e:
        print_status(f"Crash detected: {e}", "error")


def deploy_docker(env_vars):
    print_header("Final Step: Docker Ignition")
    print_status("Preparing Docker environment...")

    # Generate docker-compose.yml in project root
    compose_path = os.path.join(SCRIPT_DIR, "docker-compose.yml")

    # Use absolute path for volumes to avoid Docker mounting issues
    abs_app_home = os.path.abspath(APP_HOME)

    compose_content = f"""version: '3.8'

services:
  reality-router:
    build: .
    image: reality-router:latest
    container_name: reality-router
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - {abs_app_home}:/root/.reality_router
    environment:
      - REALITY_ROUTER_HOME=/root/.reality_router
"""

    try:
        with open(compose_path, "w") as f:
            f.write(compose_content)
        print_status(f"Generated {compose_path}", "success")

        print_status("Building and launching Docker containers...")
        # Check for docker compose vs docker-compose
        cmd = ["docker", "compose", "up", "-d", "--build"]

        subprocess.run(cmd, cwd=SCRIPT_DIR, check=True)

        print(f"\n  {C_GREEN}{C_BOLD}RealityRouter is now running in Docker!{C_RESET}")
        print(f"  {C_CYAN}Endpoint: http://localhost:8000{C_RESET}")
        print(f"  {C_CYAN}Auto-restart: ENABLED{C_RESET}")
        print(f"\n  {C_YELLOW}Useful commands:{C_RESET}")
        print(f"  - View Logs:  docker logs -f reality-router")
        print(f"  - Stop:       docker compose down")
        print(f"  - Rebuild:    docker compose up -d --build")
        print(f"\n  {C_GREEN}Wizard complete. Goodbye!{C_RESET}\n")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print_status(f"Docker command failed: {e}", "error")
        print(f"  Please ensure Docker is installed and your user has permissions.")
        input(f"\n  Press [Enter] to return...")
    except Exception as e:
        print_status(f"Docker deployment failed: {e}", "error")
        input(f"\n  Press [Enter] to return...")


def main():
    logger.debug("Starting Reality Router Setup Wizard.")
    env_vars = load_env()
    has_docker = check_docker()

    # Check if we should skip to start
    if os.path.exists(ENV_FILE):
        print_header("Reality Router")
        print_status("Welcome back! Existing config detected.\n")
        if not env_vars.get("SENTIMENT_MODEL_ID"):
            print_status(
                "A Sentiment Model has not been configured yet. Reconfiguration required.",
                "warn",
            )
            action = "r"
            time.sleep(2)
        else:
            choices = [("Start Server (Local)", "s")]
            if has_docker:
                choices.append(("Start Server (Docker)", "d"))
            choices.append(("Reconfigure", "r"))

            action_q = [
                inquirer.List(
                    "action",
                    message="Welcome back",
                    choices=choices,
                    default="s",
                )
            ]
            action_a = inquirer.prompt(action_q)
            if not action_a:
                sys.exit(0)
            action = action_a["action"]

        if action == "s":
            start_server(env_vars)
            return
        elif action == "d":
            deploy_docker(env_vars)
            return

    try:
        print_header("Reality Router Setup")
        print(
            f"  Welcome to the {C_BOLD}Reality Router{C_RESET} initialization wizard."
        )
        print(f"  Optimized for {C_GREEN}Utility{C_RESET}.\n")

        begin_q = [
            inquirer.List(
                "begin",
                message="Begin Setup?",
                choices=[("Yes", "y"), ("No, exit", "n")],
            )
        ]
        begin_a = inquirer.prompt(begin_q)
        if not begin_a or begin_a["begin"] == "n":
            sys.exit(0)

        wizard_routing_strategy(env_vars)
        wizard_global_settings(env_vars)
        wizard_providers(env_vars)
        wizard_model_management(env_vars)

        if has_docker:
            deploy_q = [
                inquirer.List(
                    "deploy",
                    message="Choose Deployment Mode",
                    choices=[
                        ("Local Process (Manual Control)", "l"),
                        ("Docker Container (Auto-Restart)", "d"),
                    ],
                    default="l",
                )
            ]
            deploy_a = inquirer.prompt(deploy_q)

            if deploy_a and deploy_a["deploy"] == "d":
                deploy_docker(env_vars)
                return

        start_server(env_vars)

    except (KeyboardInterrupt, EOFError):
        print(f"\n\n  {C_RED}Setup aborted.{C_RESET}")
    except Exception as e:
        logger.error(f"Fatal crash: {e}")


if __name__ == "__main__":
    main()
