export function formatSuccess(answer, intent = 'general', source = 'chat_service', extra = {}) {
  return {
    success: true,
    answer,
    metadata: {
      processing_time: `${Date.now() - global._requestStart || 0}ms`,
      source,
      intent,
      language: extra.lang || 'en',
      ...(extra.sql ? { sql: extra.sql } : {}),
    },
  };
}

export function formatError(error) {
  return {
    success: false,
    error: {
      code: error.code || 'INTERNAL_ERROR',
      message: error.message || 'An unexpected error occurred',
    },
    metadata: {
      processing_time: `${Date.now() - global._requestStart || 0}ms`,
      source: 'error_handler',
      intent: 'error',
    },
  };
}
