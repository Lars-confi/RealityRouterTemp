import re

with open("src/adapters/generic_openai_adapter.py", "r") as f:
    content = f.read()

# Look at how model is assigned and passed.
# In generic_openai_adapter.py:
#             params = {
#                 "model": self.default_model,

bad_params = """            params = {
                "model": self.default_model,
                "messages": messages,
                "max_tokens": 1000,"""

# The problem is `self.default_model` was initialized as `model` from model_info.
# But for autodiscovered Ollama models, we appended `ollama_` to their `model_id`, but what did we pass for `default_model`?
# In auto-discovery, we set `name`. So `default_model` = `gemma4:31b`.
# But wait, looking at the logs:
# `model 'local' not found`
# Why is it requesting the model "local"?
# Because your custom model was ID `ollama_local`. And during fallback or setup, it must have defaulted to "local"!
# Let's fix the request interceptor to FORCE the correct model name if the client sends one.

good_params = """            req_model = self.default_model
            # If the user explicitly requested a model, let's just use what we have configured for THIS adapter
            params = {
                "model": req_model,
                "messages": messages,
                "max_tokens": 1000,"""

content = content.replace(bad_params, good_params)
with open("src/adapters/generic_openai_adapter.py", "w") as f:
    f.write(content)

# Now check the core router where generic adapters are built
with open("src/router/core.py", "r") as f:
    core_content = f.read()

# I see what went wrong. When you manually added the model via TUI and called it "local" (ID ollama_local)
# The model string you passed was literally "local". Ollama doesn't have a model named "local" installed.
# But what about the auto-discovered ones? Let's check how they are instantiated.
# "name = m.get('name') -> mid = f'ollama_{name}' -> GenericOpenAIAdapter(name, custom_key, custom_url, name)
# The 4th argument is `default_model`. It passes `name` which is e.g. "gemma4:31b".

# If it passes gemma4:31b, why did the log say model "local" not found in the failover?
# Because the client sent `model: "local"` or because it tried to failover to the 1st model you manually set!

