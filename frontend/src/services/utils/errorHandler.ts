import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  code?: string;
  field?: string;
}

export class ErrorHandler {
  static getErrorMessage(error: unknown): string {
    if (error instanceof AxiosError) {
      // Handle Axios error responses
      if (error.response?.data) {
        const data = error.response.data;
        if (typeof data === 'string') {
          return data;
        }
        if (data.message) {
          return data.message;
        }
        if (data.detail) {
          return data.detail;
        }
        if (Array.isArray(data)) {
          return data[0]?.message || 'An error occurred';
        }
      }
      return error.message;
    }

    if (error instanceof Error) {
      return error.message;
    }

    return 'An unexpected error occurred';
  }

  static isNetworkError(error: unknown): boolean {
    return error instanceof AxiosError && !error.response;
  }

  static isAuthenticationError(error: unknown): boolean {
    return error instanceof AxiosError && error.response?.status === 401;
  }

  static isAuthorizationError(error: unknown): boolean {
    return error instanceof AxiosError && error.response?.status === 403;
  }

  static isValidationError(error: unknown): boolean {
    return error instanceof AxiosError && error.response?.status === 400;
  }

  static isNotFoundError(error: unknown): boolean {
    return error instanceof AxiosError && error.response?.status === 404;
  }

  static getFieldErrors(error: unknown): Record<string, string> | null {
    if (error instanceof AxiosError && error.response?.data) {
      const data = error.response.data;
      if (typeof data === 'object' && !Array.isArray(data)) {
        const fieldErrors: Record<string, string> = {};
        Object.entries(data).forEach(([key, value]) => {
          if (Array.isArray(value)) {
            fieldErrors[key] = value[0];
          } else if (typeof value === 'string') {
            fieldErrors[key] = value;
          }
        });
        return fieldErrors;
      }
    }
    return null;
  }
}

export const handleApiError = (error: unknown): ApiError => {
  const message = ErrorHandler.getErrorMessage(error);
  const fieldErrors = ErrorHandler.getFieldErrors(error);

  if (fieldErrors) {
    const [field, fieldMessage] = Object.entries(fieldErrors)[0];
    return {
      message: fieldMessage,
      field,
    };
  }

  let code: string | undefined;
  if (ErrorHandler.isNetworkError(error)) {
    code = 'NETWORK_ERROR';
  } else if (ErrorHandler.isAuthenticationError(error)) {
    code = 'AUTHENTICATION_ERROR';
  } else if (ErrorHandler.isAuthorizationError(error)) {
    code = 'AUTHORIZATION_ERROR';
  } else if (ErrorHandler.isValidationError(error)) {
    code = 'VALIDATION_ERROR';
  } else if (ErrorHandler.isNotFoundError(error)) {
    code = 'NOT_FOUND_ERROR';
  }

  return {
    message,
    code,
  };
};

export const createApiError = (message: string, code?: string): ApiError => ({
  message,
  code,
});

export const getUserFacingMessageFromApiError = (error: ApiError): string => {
  switch (error.code) {
    case 'NETWORK_ERROR':
      return 'Network error. Please check your connection and try again.';
    case 'AUTHENTICATION_ERROR':
      return 'Your session has expired. Please sign in again.';
    case 'AUTHORIZATION_ERROR':
      return 'You do not have access to this resource.';
    case 'NOT_FOUND_ERROR':
      return 'Requested resource was not found.';
    case 'VALIDATION_ERROR':
      return error.message || 'Invalid request.';
    default:
      return error.message || 'An unexpected error occurred.';
  }
};

export const getUserFacingErrorMessage = (
  error: unknown,
  fallback: string
): string => {
  const apiError = handleApiError(error);

  switch (apiError.code) {
    case 'NETWORK_ERROR':
      return 'Network error. Please check your connection and try again.';
    case 'AUTHENTICATION_ERROR':
      return 'Your session has expired. Please sign in again.';
    case 'AUTHORIZATION_ERROR':
      return 'You do not have access to this resource.';
    case 'NOT_FOUND_ERROR':
      return 'Requested resource was not found.';
    case 'VALIDATION_ERROR':
      return apiError.message || fallback;
    default:
      return apiError.message || fallback;
  }
};
