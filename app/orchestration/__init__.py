class _BaseGraph:
    def build(self, *args, **kwargs):
        try:
            return self._build(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in build: {e}")
            raise

    def invoke(self, *args, **kwargs):
        try:
            return self._invoke(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in invoke: {e}")
            raise

    def _build(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._build()")

    def _invoke(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._invoke()")