import re

with open("src/router/core.py", "r") as f:
    content = f.read()

# Remove the incorrectly placed router_core instantiation that causes the issue
bad_str = """# Global instance
router_core = RouterCore()"""
good_str = """# Global instance\n# (RouterCore instantiated below)"""

content = content.replace(bad_str, good_str)

# Ensure the actual initialization is done exactly once near the bottom
init_block = """
# Initialize single global instance
try:
    router_core = RouterCore()
except Exception as e:
    logger.error(f"Failed to initialize router core: {e}")
    router_core = None

"""

if "router_core = RouterCore()" not in content:
    content += init_block

with open("src/router/core.py", "w") as f:
    f.write(content)

