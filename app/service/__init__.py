import asyncio


class _BaseAsyncMCPClient:
    async def connect(self, *args, **kwargs):
        try:
            return await self._connect(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in connect: {e}")
            raise

    async def call_tool(self, *args, **kwargs):
        try:
            return await self._call_tool(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in call_tool: {e}")
            raise

    async def close(self, *args, **kwargs):
        try:
            return await self._close(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in close: {e}")
            raise

    async def _connect(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._connect()")

    async def _call_tool(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._call_tool()")

    async def _close(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._close()")


class _BaseMCPClientWrapper:
    def __init__(self, client: _BaseAsyncMCPClient):
        self._client = client()
        self._connected = False
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def connect(self, *args, **kwargs):
        try:
            return self._connect(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in connect: {e}")
            raise

    def call_tool(self, *args, **kwargs):
        try:
            return self._call_tool(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in call_tool: {e}")
            raise

    def close(self, *args, **kwargs):
        try:
            return self._close(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in close: {e}")
            raise

    def _connect(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._connect()")

    def _call_tool(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._call_tool()")

    def _close(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._close()")
