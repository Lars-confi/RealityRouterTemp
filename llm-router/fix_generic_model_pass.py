import re

with open("src/adapters/generic_openai_adapter.py", "r") as f:
    content = f.read()

# Make absolutely sure that the request model is ignored if we have an explicit adapter model
# Why? Because if the editor requests 'gpt-3.5-turbo' but the router decides to use 'ollama_gemma4:31b',
# the GenericOpenAIAdapter shouldn't pass 'gpt-3.5-turbo' down to Ollama (which would 404).
# It MUST pass the adapter's mapped model name!

bad_str = """            if request.parameters:
                if "messages" in request.parameters:
                    params["messages"] = request.parameters["messages"]
                    temp_params = dict(request.parameters)
                    del temp_params["messages"]
                    params.update(temp_params)
                else:
                    params.update(request.parameters)"""

good_str = """            if request.parameters:
                temp_params = dict(request.parameters)
                if "messages" in temp_params:
                    params["messages"] = temp_params["messages"]
                    del temp_params["messages"]
                    
                # NEVER overwrite the mapped model name for custom endpoints
                # Otherwise if the user requested 'gpt-3.5' and we routed to 'llama3',
                # passing 'gpt-3.5' to Ollama will result in a 404.
                if "model" in temp_params:
                    del temp_params["model"]
                    
                params.update(temp_params)"""

content = content.replace(bad_str, good_str)

with open("src/adapters/generic_openai_adapter.py", "w") as f:
    f.write(content)
