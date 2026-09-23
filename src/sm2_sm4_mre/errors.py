"""Domain-specific exceptions for the SM2 + SM4 multi-recipient backend."""

from __future__ import annotations


class MREError(Exception):
    """Base exception for this package."""


class BackendUnavailableError(MREError):
    """Raised when the selected cryptographic backend is unavailable."""


class CryptoOperationError(MREError):
    """Raised when a backend cryptographic operation fails."""


class InvalidEnvelopeError(MREError):
    """Raised when a wrapped key envelope is malformed or mismatched."""


class InvalidPackageError(MREError):
    """Raised when a .smre package is malformed or unsupported."""
