from boolean_algebra_engine.mcp.server import *  # noqa: F401, F403
from boolean_algebra_engine.mcp.server import check_prompt_logic, mcp
if __name__ == "__main__":
    mcp.run(transport="stdio")
