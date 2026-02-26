class _BaseGuard:
    def filter(self, *args, **kwargs):
        try:
            return self._filter(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in filter: {e}")
            raise

    def _filter(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}.filter()")


class _BaseRAGPipeline:
    def answer(self, *args, **kwargs):
        try:
            return self._answer(*args, **kwargs)
        except Exception as e:
            print(f"{self.__class__.__name__} Error in answer: {e}")
            raise

    def _answer(self, *args, **kwargs):
        raise NotImplementedError(f"{self.__class__.__name__}._answer()")
