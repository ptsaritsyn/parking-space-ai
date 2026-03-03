import os
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.service import _BaseAsyncMCPClient, _BaseMCPClientWrapper


class MCPAsyncStdioClient(_BaseAsyncMCPClient):
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.stdio = None
        self.write = None

    async def _connect(self, server_script_path=None):
        if server_script_path is None:
            server_script_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), '..', 'service', 'mcp_server.py')
            )

        server_params = StdioServerParameters(
            command="python",
            args=[server_script_path]
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        tools_result = await self.session.list_tools()

        for tool in tools_result.tools:
            print(f"--- Available Tools ---")
            print(f"--- {tool.name}: {tool.description}")

    async def _call_tool(self, tool_name, **params):
        result = await self.session.call_tool(
            name=tool_name,
            arguments=params
        )
        return result

    async def close(self):
        await self.exit_stack.aclose()


class MCPClientWrapper(_BaseMCPClientWrapper):
    def _connect(self):
        if self._connected:
            return

        self._loop.run_until_complete(self._client._connect())
        self._connected = True

    def _call_tool(self, tool_name, **params):
        return self._loop.run_until_complete(self._client.call_tool(tool_name, **params))

    def _close(self):
        if self._connected:
            self._loop.run_until_complete(self._client.close())
            self._loop.close()
            self._connected = False


if __name__ == '__main__':
    service = MCPClientWrapper(MCPAsyncStdioClient)
    service.connect()
