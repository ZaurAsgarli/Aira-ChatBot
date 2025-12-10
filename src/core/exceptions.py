class AiraBaseException(Exception):
    """Base exception for all Aira application errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class VectorDBException(AiraBaseException):
    """Raised when Qdrant fails to connect or search."""

    pass


class LLMGenerationException(AiraBaseException):
    """Raised when OpenAI fails to generate a response."""

    pass


class ExternalToolException(AiraBaseException):
    """Raised when Web Search or other tools fail."""

    pass
