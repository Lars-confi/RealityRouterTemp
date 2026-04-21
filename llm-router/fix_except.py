import sys

with open('src/router/core.py', 'r') as f:
    content = f.read()

content = content.replace('''        except Exception as e:
            logger.error(f"Routing error: {e}")
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")''', '''        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Routing error: {e}")
            raise HTTPException(status_code=500, detail=f"Routing error: {str(e)}")''')

with open('src/router/core.py', 'w') as f:
    f.write(content)
