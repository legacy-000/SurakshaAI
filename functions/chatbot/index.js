import catalyst from 'zcatalyst-sdk-node';
import { validateRequest, validateEnvironment } from './lib/validator.js';
import { formatSuccess, formatError } from './lib/response.js';
import { AppError, handleError } from './lib/errors.js';
import ChatService from './services/chatService.js';
import { logger } from './utils/logger.js';

validateEnvironment();

function parseBody(request) {
  return new Promise((resolve, reject) => {
    let body = '';
    request.on('data', chunk => { body += chunk; });
    request.on('end', () => {
      try {
        resolve(body ? JSON.parse(body) : {});
      } catch {
        reject(new AppError('Invalid JSON in request body', 400, 'PARSE_ERROR'));
      }
    });
    request.on('error', () => reject(new AppError('Request stream error', 400, 'STREAM_ERROR')));
  });
}

async function handler(request, response) {
  global._requestStart = Date.now();

  response.setHeader('Content-Type', 'application/json');
  response.setHeader('Access-Control-Allow-Origin', '*');
  response.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  response.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (request.method === 'OPTIONS') {
    response.writeHead(204);
    response.end();
    return;
  }

  if (request.method !== 'POST') {
    response.writeHead(405);
    response.end(JSON.stringify(formatError(new AppError('Method not allowed. Use POST.', 405, 'METHOD_NOT_ALLOWED'))));
    return;
  }

  let rawBody = {};
  try {
    const app = catalyst.initialize(request);
    rawBody = await parseBody(request);
    const { question, session_id, user_id } = validateRequest(rawBody);

    const chatService = new ChatService(app);
    const result = await chatService.processMessage(question, session_id, user_id);

    const isConvoKraft = rawBody.todo && rawBody.action;
    const formatted = isConvoKraft
      ? { status: 'execution', message: result.answer, card: [], data: { intent: result.intent, source: result.source }, broadcast: {}, trigger: {}, followup: {} }
      : formatSuccess(result.answer, result.intent, result.source, { lang: result.lang, sql: result.sql });

    logger.info('Request completed', { session_id, user_id, intent: result.intent });

    response.writeHead(200);
    response.end(JSON.stringify(formatted));
  } catch (error) {
    logger.error('Request failed', { error: error.message, stack: error.stack });
    const errorResponse = error instanceof AppError ? formatError(error) : handleError(error);
    const status = error instanceof AppError ? error.statusCode : 500;
    const isConvoKraft = rawBody.todo && rawBody.action;

    response.writeHead(status);
    response.end(JSON.stringify(isConvoKraft
      ? { status: 'execution', message: errorResponse.error?.message || 'An error occurred', card: [], data: {}, broadcast: {}, trigger: {}, followup: {} }
      : errorResponse));
  }
}

export default handler;
