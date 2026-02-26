from app.core import _BaseGuard


class CarNumberPIIGuard(_BaseGuard):
    def _filter(self, text: str) -> str:
        import re
        return re.sub(r'\b[A-Z]{2}\d{4}[A-Z]{2}\b', 'CAR_NUMBER', text)
