class _BaseLLM:
    def generate(self, *args, **kwargs):
        try:
            return self._generate(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in generate: {e}")
            raise

    def _generate(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._generate()")
