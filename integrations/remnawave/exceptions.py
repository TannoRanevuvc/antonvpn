class RemnawaveApiError(Exception):
    def __init__(self, message: str, status: int | None = None, url: str = "", response: dict | None = None):
        super().__init__(message)
        self.status = status
        self.url = url
        self.response = response or {}

    def __str__(self) -> str:
        return f"RemnawaveApiError(status={self.status}, url={self.url}, msg={super().__str__()})"
