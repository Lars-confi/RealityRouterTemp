with open("src/main.py", "r") as f:
    content = f.read()

content = content.replace(
    'app.include_router(router_router, prefix="/v1", tags=["routing"])',
    'app.include_router(router_router, prefix="/v1", tags=["routing"])\napp.include_router(router_router, tags=["routing_root"])'
)

with open("src/main.py", "w") as f:
    f.write(content)
