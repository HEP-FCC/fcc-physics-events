"""
Standardized Error Handling for FCC Physics Events Backend
Provides consistent error response formats matching frontend expectations
"""

from typing import Any

from fastapi import HTTPException, status
from pydantic import BaseModel


# Error type constants that match frontend global-error-handler.client.ts
class ErrorTypes:
    """Error type constants for consistent error responses."""

    # Authentication errors (401)
    AUTHENTICATION_FAILED = "authentication_failed"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "invalid_token"
    TOKEN_MISSING = "missing_token"
    SESSION_ERROR = "session_error"
    NO_REFRESH_TOKEN = "no_refresh_token"
    REFRESH_FAILED = "refresh_failed"

    # Authorization errors (403)
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    ROLE_REQUIRED = "role_required"

    # Validation errors (400)
    INVALID_INPUT = "invalid_input"
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"

    # Client errors (4xx)
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"

    # Rate limiting (429)
    RATE_LIMITED = "rate_limited"

    # Server errors (5xx)
    INTERNAL_ERROR = "internal_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    SERVER_UNAVAILABLE = "server_unavailable"
    SERVICE_TIMEOUT = "service_timeout"


class ErrorDetail(BaseModel):
    """Error detail structure for standardized error responses."""

    error: str  # Error type identifier (required)
    message: str  # Detailed technical message (required)
    code: str | None = None  # Specific error code
    retry_after: int | None = None  # For 429 rate limiting (seconds)
    required_role: str | None = None  # For 403 authorization
    validation_errors: dict[str, list[str]] | None = None  # For 400 validation


class StandardErrorResponse(BaseModel):
    """Standard error response format that matches frontend expectations."""

    message: str  # User-friendly message
    status: int  # HTTP status code
    details: ErrorDetail


def create_standard_http_exception(
    status_code: int,
    error_type: str,
    user_message: str,
    technical_message: str,
    code: str | None = None,
    retry_after: int | None = None,
    required_role: str | None = None,
    validation_errors: dict[str, list[str]] | None = None,
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """
    Create a standardized HTTPException with consistent error format.

    Args:
        status_code: HTTP status code
        error_type: Error type from ErrorTypes constants
        user_message: User-friendly message for frontend display
        technical_message: Detailed technical message for debugging
        code: Optional specific error code
        retry_after: Optional retry delay in seconds (for 429 errors)
        required_role: Optional required role (for 403 errors)
        validation_errors: Optional validation error details (for 400 errors)
        headers: Optional HTTP headers

    Returns:
        HTTPException with standardized error format
    """
    detail: dict[str, Any] = {
        "message": user_message,
        "status": status_code,
        "details": {
            "error": error_type,
            "message": technical_message,
        },
    }

    # Add optional fields if provided
    details: dict[str, Any] = detail["details"]
    if code:
        details["code"] = code
    if retry_after:
        details["retry_after"] = retry_after
    if required_role:
        details["required_role"] = required_role
    if validation_errors:
        details["validation_errors"] = validation_errors

    return HTTPException(status_code=status_code, detail=detail, headers=headers)


# Convenience functions for common error types


def unauthenticated_error(
    error_type: str = ErrorTypes.AUTHENTICATION_FAILED,
    message: str = "Authentication failed",
    user_message: str = "Your session has expired. Please log in again.",
    headers: dict[str, str] | None = None,
) -> HTTPException:
    """
    Create a standardized 401 Unauthenticated error.
    Used when we cannot verify the user's identity:
    - Invalid/missing credentials
    - Expired tokens
    - Malformed authentication data
    """
    error_headers = headers or {"WWW-Authenticate": "Bearer"}
    return create_standard_http_exception(
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_type=error_type,
        user_message=user_message,
        technical_message=message,
        headers=error_headers,
    )


def unauthorized_error(
    error_type: str = ErrorTypes.INSUFFICIENT_PERMISSIONS,
    message: str = "Insufficient permissions to access this resource",
    user_message: str = "You don't have permission to perform this action.",
    required_role: str | None = None,
) -> HTTPException:
    """
    Create a standardized 403 Forbidden error.
    Used when we know who the user is but they lack permissions:
    - Valid identity but wrong role
    - Missing required permissions
    - Access to restricted resources
    """
    return create_standard_http_exception(
        status_code=status.HTTP_403_FORBIDDEN,
        error_type=error_type,
        user_message=user_message,
        technical_message=message,
        required_role=required_role,
    )


def authorization_error(
    user_message: str = "You don't have permission to perform this action",
    technical_message: str = "Insufficient permissions for requested operation",
    required_role: str | None = None,
) -> HTTPException:
    """Create a standardized 403 authorization error."""
    error_type = (
        ErrorTypes.ROLE_REQUIRED
        if required_role
        else ErrorTypes.INSUFFICIENT_PERMISSIONS
    )

    return create_standard_http_exception(
        status_code=status.HTTP_403_FORBIDDEN,
        error_type=error_type,
        user_message=user_message,
        technical_message=technical_message,
        required_role=required_role,
    )


def validation_error(
    error_type: str = ErrorTypes.INVALID_INPUT,
    message: str = "Request validation failed",
    user_message: str = "Invalid request data. Please check your input.",
    validation_errors: dict[str, list[str]] | None = None,
) -> HTTPException:
    """Create a standardized 400 validation error."""
    return create_standard_http_exception(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type=error_type,
        user_message=user_message,
        technical_message=message,
        validation_errors=validation_errors,
    )


def not_found_error(
    error_type: str = ErrorTypes.NOT_FOUND,
    message: str = "Resource not found in database",
    user_message: str = "The requested resource was not found",
) -> HTTPException:
    """Create a standardized 404 not found error."""
    return create_standard_http_exception(
        status_code=status.HTTP_404_NOT_FOUND,
        error_type=error_type,
        user_message=user_message,
        technical_message=message,
    )


def server_error(
    error_type: str = ErrorTypes.INTERNAL_ERROR,
    message: str = "Internal server error",
    user_message: str = "An internal server error occurred. Please try again later.",
) -> HTTPException:
    """Create a standardized 500 server error."""
    return create_standard_http_exception(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type=error_type,
        user_message=user_message,
        technical_message=message,
    )


def database_error(
    user_message: str = "A database error occurred. Please try again later.",
    technical_message: str = "Database operation failed",
) -> HTTPException:
    """Create a standardized database error."""
    return create_standard_http_exception(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type=ErrorTypes.DATABASE_ERROR,
        user_message=user_message,
        technical_message=technical_message,
    )


def external_service_error(
    user_message: str = "An external service is temporarily unavailable. Please try again later.",
    technical_message: str = "External service request failed",
) -> HTTPException:
    """Create a standardized external service error."""
    return create_standard_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type=ErrorTypes.EXTERNAL_SERVICE_ERROR,
        user_message=user_message,
        technical_message=technical_message,
        headers={"Retry-After": "300"},  # Suggest retry after 5 minutes
    )


def service_unavailable_error(
    user_message: str = "The service is temporarily unavailable. Please try again later.",
    technical_message: str = "Service is currently unavailable",
    retry_after: int = 300,
) -> HTTPException:
    """Create a standardized 503 service unavailable error."""
    return create_standard_http_exception(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        error_type=ErrorTypes.SERVER_UNAVAILABLE,
        user_message=user_message,
        technical_message=technical_message,
        headers={"Retry-After": str(retry_after)},
    )


def gateway_timeout_error(
    user_message: str = "The server took too long to respond. Please try again.",
    technical_message: str = "Gateway timeout occurred",
) -> HTTPException:
    """Create a standardized 504 gateway timeout error."""
    return create_standard_http_exception(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        error_type=ErrorTypes.SERVICE_TIMEOUT,
        user_message=user_message,
        technical_message=technical_message,
    )
