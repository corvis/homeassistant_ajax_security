class UnknownMessageError(Exception):
    pass


class RestartRequiredException(Exception):
    def __init__(self, cause: Exception = None, *args) -> None:
        self.cause = cause
        super().__init__(*args)
