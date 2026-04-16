import re

with open("src/adapters/generic_openai_adapter.py", "r") as f:
    content = f.read()

# I see what the issue is! We are unpacking parameters incorrectly in generic_openai_adapter
# Wait, look at this: `params["messages"] = temp_params["messages"]`
# If Zed is sending `request.messages` with complex dictionaries (like role: user, content: [{type: text, text: ...}]),
# the standard OpenAI proxy might reject it because it only expects string contents, not objects.
# The OpenAI SDK might be throwing a ValueError before it even makes the network call, OR the network call returns 404 because the model name is wrong.

# But the logs explicitly state: "Model ollama_nemotron-3-nano-30b failed: Error calling Custom OpenAI API: Error code: 404 - {'error': {'message': "model 'local' not found", 'type': 'not_found_error', 'param': None, 'code': None}}"
# "model 'local' not found" -- This means `req_model` is somehow STILL set to `"local"` instead of `"nemotron-3-nano:30b"`!

bad_str = """                            req_model = model_info.get('model') if isinstance(model_info, dict) else None
                            if not req_model: req_model = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id"""

good_str = """                            req_model = model_info.get('model') if isinstance(model_info, dict) else None
                            if not req_model: 
                                req_model = model_info.get('name', model_id) if isinstance(model_info, dict) else model_id
                            
                            # Clean up Ollama names if they were passed incorrectly
                            if req_model.startswith("ollama_"):
                                req_model = req_model.replace("ollama_", "").replace("-", ":")"""

with open("src/router/core.py", "r") as f:
    core = f.read()

core = core.replace(bad_str, good_str)
with open("src/router/core.py", "w") as f:
    f.write(core)

