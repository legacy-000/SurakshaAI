import config from '../lib/config.js';

const LOG_LEVELS = { debug: 0, info: 1, warn: 2, error: 3 };

function shouldLog(level) {
  return LOG_LEVELS[level] >= (LOG_LEVELS[config.logLevel] || 1);
}

function formatMessage(level, message, data) {
  const entry = {
    timestamp: new Date().toISOString(),
    level,
    message,
    ...(data ? { data } : {}),
  };
  return JSON.stringify(entry);
}

export const logger = {
  debug(message, data) {
    if (shouldLog('debug')) console.debug(formatMessage('debug', message, data));
  },
  info(message, data) {
    if (shouldLog('info')) console.info(formatMessage('info', message, data));
  },
  warn(message, data) {
    if (shouldLog('warn')) console.warn(formatMessage('warn', message, data));
  },
  error(message, data) {
    if (shouldLog('error')) console.error(formatMessage('error', message, data));
  },
};
