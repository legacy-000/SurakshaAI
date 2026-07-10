import { ValidationError } from './errors.js';

export function validateRequest(body) {
  if (!body || typeof body !== 'object') {
    throw new ValidationError('Request body must be a JSON object');
  }

  const question = body.question || body.userInput;
  if (!question || typeof question !== 'string' || question.trim().length === 0) {
    throw new ValidationError("Missing or invalid required field: 'question' or 'userInput'");
  }

  if (body.session_id && typeof body.session_id !== 'string') {
    throw new ValidationError("'session_id' must be a string");
  }

  if (body.user_id && typeof body.user_id !== 'string') {
    throw new ValidationError("'user_id' must be a string");
  }

  return {
    question: question.trim(),
    session_id: body.session_id || body.user?.id || null,
    user_id: body.user_id || body.user?.id || null,
  };
}

export function validateEnvironment() {
  const required = [];
  if (!process.env.CATALYST_PROJECT) required.push('CATALYST_PROJECT');
  if (required.length > 0) {
    console.warn(`Missing environment variables: ${required.join(', ')}`);
  }
}
