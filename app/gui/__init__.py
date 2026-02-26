class _BaseGUI:
    def run(self, *args, **kwargs):
        try:
            return self._run(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in run: {e}")
            raise

    def _run(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._run()")
