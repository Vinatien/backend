class BusinessRuleException(Exception):
    """Raised when a business rule is violated"""
    pass


class ConflictException(Exception):
    """Raised when there's a conflict (e.g., resource already exists)"""
    pass


class NotFoundException(Exception):
    """Raised when a resource is not found"""
    pass


class ResourceNotFound(Exception):
    """Raised when a resource is not found (alias for NotFoundException)"""
    pass


class AuthenticationException(Exception):
    """Raised when authentication fails"""
    pass


class AuthorizationException(Exception):
    """Raised when authorization fails (forbidden access)"""
    pass
