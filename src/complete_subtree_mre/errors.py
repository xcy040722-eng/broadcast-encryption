"""Errors for the unified Complete Subtree backend."""


class CompleteSubtreeError(Exception):
    """Base class for Complete Subtree backend errors."""


class CsEnvelopeError(CompleteSubtreeError):
    """Raised when a decrypted CS key envelope has invalid binding/format."""
