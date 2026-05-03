from __future__ import annotations


class IMSException(Exception):
    pass


class InvalidStateTransition(IMSException):
    pass


class MissingRCA(IMSException):
    pass


class RateLimitExceeded(IMSException):
    pass
