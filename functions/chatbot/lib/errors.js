export class AppError extends Error {
  constructor(message, statusCode = 500, code = 'INTERNAL_ERROR') {
    super(message);
    this.name = 'AppError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

export class ValidationError extends AppError {
  constructor(message) {
    super(message, 400, 'VALIDATION_ERROR');
    this.name = 'ValidationError';
  }
}

export class NotFoundError extends AppError {
  constructor(message = 'Resource not found') {
    super(message, 404, 'NOT_FOUND');
    this.name = 'NotFoundError';
  }
}

export function handleError(error) {
  if (error instanceof AppError) {
    return {
      success: false,
      error: { code: error.code, message: error.message },
      metadata: { processing_time: '0ms', source: 'error_handler', intent: 'error' },
    };
  }
  return {
    success: false,
    error: { code: 'INTERNAL_ERROR', message: 'An unexpected error occurred' },
    metadata: { processing_time: '0ms', source: 'error_handler', intent: 'error' },
  };
}
