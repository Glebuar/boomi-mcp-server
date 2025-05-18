import asyncio
from src.tools import mcp


def test_create_component_tool_registered():
    tools = asyncio.run(mcp.get_tools())
    assert "create_component" in tools
    tool = tools["create_component"]
    assert tool.parameters["properties"]["xml_path"]["type"] == "string"


def test_health_check_tool_registered():
    tools = asyncio.run(mcp.get_tools())
    assert "health_check" in tools
