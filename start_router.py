#!/usr/bin/env python3
import os
import json
import subprocess
import sys
import time
import urllib.request
import ssl

ENV_FILE = ".env"

PROVIDER_KEYS = {
    'openai': [('OPENAI_API_KEY', 'OpenAI API Key')],
    'anthropic': [('ANTHROPIC_API_KEY', 'Anthropic API Key')],
    'cohere': [('COHERE_API_KEY', 'Cohere API Key')],
    'huggingface': [('HUGGINGFACE_API_KEY', 'Hugging Face API Key')],
    'gemini': [('GEMINI_API_KEY', 'Google Gemini API Key')],
    'custom/local': [
        ('CUSTOM_LLM_BASE_URL', 'Base URL (e.g., http://localhost:11434/v1)'),
        ('CUSTOM_LLM_API_KEY', 'API Key (or dummy)')
    ]
}

def load_env():
    env_vars = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, val = line.split("=", 1)
                        env_vars[key.strip()] = val.strip().strip("'").strip('"')
    return env_vars

def save_env(env_vars):
    with open(ENV_FILE, "w") as f:
        for k, v in env_vars.items():
            f.write(f"{k}={v}\n")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def prompt(text, default=""):
    prompt_str = f"{text} [{default}]: " if default else f"{text}: "
    val = input(prompt_str).strip()
    return val if val else default

def print_header(title):
    clear_screen()
    print("=" * 60)
    print(f" {title:^58} ")
    print("=" * 60)
    print()

def sync_discover_ollama(base_url="http://localhost:11434"):
    discovered = []
    try:
        url = base_url.replace("/v1", "/api/tags") if base_url.endswith("/v1") else f"{base_url}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                for model in data.get("models", []):
                    name = model.get("name")
                    if name:
                        discovered.append(f"Ollama: {name}")
    except Exception:
        pass
    return discovered

def sync_discover_openai_compat(base_url, api_key, provider_name):
    discovered = []
    try:
        url = f"{base_url}/models" if not base_url.endswith("/") else f"{base_url}models"
        req = urllib.request.Request(url)
        if api_key and api_key != "dummy" and api_key != "sk-dummy":
            req.add_header("Authorization", f"Bearer {api_key}")
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, timeout=3, context=ctx) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                for model in data.get("data", []):
                    model_id = model.get("id")
                    if model_id:
                        if provider_name == 'openai' and ('gpt' not in model_id and 'o1' not in model_id):
                            continue
                        discovered.append(f"{provider_name.title()}: {model_id}")
    except Exception:
        pass
    return discovered

def display_discovered_models(env_vars):
    print("\n--- Currently Discovered Models ---")
    found_any = False
    
    # Check Ollama/Custom
    custom_url = env_vars.get("CUSTOM_LLM_BASE_URL")
    custom_key = env_vars.get("CUSTOM_LLM_API_KEY", "dummy")
    if custom_url:
        if "11434" in custom_url:
            models = sync_discover_ollama(custom_url)
            for m in models:
                print(f"  ✓ {m}")
                found_any = True
        else:
            models = sync_discover_openai_compat(custom_url, custom_key, "Custom Endpoint")
            for m in models:
                print(f"  ✓ {m}")
                found_any = True
                
    # Check OpenAI
    openai_key = env_vars.get("OPENAI_API_KEY")
    if openai_key and openai_key != "dummy" and openai_key != "sk-dummy":
        models = sync_discover_openai_compat("https://api.openai.com/v1", openai_key, "openai")
        for m in models:
            print(f"  ✓ {m}")
            found_any = True
            
    # Check Gemini
    gemini_key = env_vars.get("GEMINI_API_KEY")
    if gemini_key and gemini_key != "dummy":
        models = sync_discover_openai_compat("https://generativelanguage.googleapis.com/v1beta/openai", gemini_key, "gemini")
        for m in models:
            print(f"  ✓ {m}")
            found_any = True
            
    if not found_any:
        print("  (None found. Configure a provider below to see models here!)")
    print("-----------------------------------")


def wizard_global_settings(env_vars):
    print_header("Step 1: Expected Utility Coefficients")
    print("These coefficients decide how the router balances trade-offs.")
    print("Press [Enter] to keep the current/default values.\n")
    
    env_vars['REWARD'] = prompt("Reward (R) - Value of a correct answer", env_vars.get('REWARD', '1.0'))
    env_vars['COST_SENSITIVITY'] = prompt("Cost Sensitivity (α) - How much you care about cost", env_vars.get('COST_SENSITIVITY', '0.5'))
    env_vars['TIME_SENSITIVITY'] = prompt("Time Sensitivity (β) - How much you care about speed", env_vars.get('TIME_SENSITIVITY', '0.5'))
    
    save_env(env_vars)

def wizard_providers(env_vars):
    while True:
        print_header("Step 2: Configured LLM Providers")
        print("The router dynamically fetches all models from your configured providers.")
        
        display_discovered_models(env_vars)
                
        print("\nOptions:")
        print("  [1] Configure OpenAI")
        print("  [2] Configure Google Gemini")
        print("  [3] Configure Anthropic")
        print("  [4] Configure Cohere")
        print("  [5] Configure Custom/Local (e.g. Ollama/vLLM)")
        print("  [c] Continue to start server")
        
        choice = prompt("\nWhat would you like to do?", "c").lower()
        
        if choice == 'c':
            break
            
        mapping = {'1': 'openai', '2': 'gemini', '3': 'anthropic', '4': 'cohere', '5': 'custom/local'}
        if choice in mapping:
            provider = mapping[choice]
            print(f"\n--- Setting up {provider.title()} ---")
            for env_key, desc in PROVIDER_KEYS[provider]:
                current_val = env_vars.get(env_key, "")
                masked = current_val if "URL" in env_key else (current_val[:4] + "*" * (len(current_val)-4) if len(current_val) > 8 else "Not Set")
                new_val = prompt(f"{desc} (Current: {masked})")
                if new_val:
                    env_vars[env_key] = new_val
            save_env(env_vars)

def start_server(env_vars):
    print_header("Step 3: Starting the Router")
    
    print("Applying configurations & verifying discovery...")
    env = os.environ.copy()
    for k, v in env_vars.items():
        env[k] = v
    env["PYTHONPATH"] = "llm-router"
    
    python_exe = sys.executable
    
    print("Launching Uvicorn server on http://0.0.0.0:8000 ...")
    print("Press [CTRL+C] at any time to stop the server.\n")
    print("-" * 60)
    
    try:
        subprocess.run([python_exe, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd="llm-router", env=env)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user. Goodbye!")
    except Exception as e:
        print(f"\nFailed to start server: {e}")

def main():
    env_vars = load_env()
    
    if os.path.exists(ENV_FILE):
        print_header("LLM Rerouter")
        print("Existing configuration found!")
        try:
            action = prompt("Do you want to (s)tart the server directly, or (r)econfigure the router?", "s").lower()
            if action == 's':
                start_server(env_vars)
                return
        except EOFError:
            # If input is piped or EOF is hit unexpectedly, default to start
            start_server(env_vars)
            return

    try:
        print_header("Welcome to LLM Rerouter Setup")
        print("This wizard will guide you through setting up your router.")
        print("Press Enter to begin...")
        input()
        
        wizard_global_settings(env_vars)
        wizard_providers(env_vars)
        start_server(env_vars)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting setup.")

if __name__ == "__main__":
    main()
