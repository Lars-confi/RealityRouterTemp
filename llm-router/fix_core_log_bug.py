import re

with open("src/router/core.py", "r") as f:
    content = f.read()

bad_str_true = "self.log_routing_decision(request, decision, True, elapsed_time, response)"
good_str_true = "self.log_routing_decision(decision, request, response, db)"

bad_str_false = "self.log_routing_decision(request, decision, False, time.time() - start_time, None)"
good_str_false = "self.log_routing_decision(decision, request, {}, db)"

# Also need to make sure we inject `db = next(get_db())` into route_request if it's missing,
# but we can just use `next(get_db())` directly in the call.

if "db = next(get_db())" not in content.split("async def route_request")[1]:
    good_str_true = "self.log_routing_decision(decision, request, response, next(get_db()))"
    good_str_false = "self.log_routing_decision(decision, request, {}, next(get_db()))"

content = content.replace(bad_str_true, good_str_true)
content = content.replace(bad_str_false, good_str_false)

with open("src/router/core.py", "w") as f:
    f.write(content)

