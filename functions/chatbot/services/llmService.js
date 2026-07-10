import catalyst from 'zcatalyst-sdk-node';
import config from '../lib/config.js';
import { logger } from '../utils/logger.js';

const LLM_ENDPOINT = 'https://llm-ai.catalystserverless.in/v1/chat/completions';

const INTENT_SYSTEM = `Classify the user's crime-related question into one intent.
Return ONLY the intent label string, no explanation.
Labels: crime_query, trend_query, hotspot_query, offender_search, forecast_query, case_status, legal_reference, general`;

const NL2SQL_SYSTEM = `You are a ZCQL (Zoho Catalyst Query Language) expert for a Karnataka Police FIR database.
Generate ONLY the ZCQL query string, no explanation.
Tables: CaseMaster(CaseMasterID,CrimeRegisteredDate,CrimeMinorHeadID,PoliceStationID,StatusID),
Unit(UnitID,UnitName,DistrictID), District(DistrictID,DistrictName),
CrimeSubHead(CrimeSubHeadID,CrimeHeadName), Accused(AccusedID,CaseMasterID,AccusedName),
Victim(VictimID,CaseMasterID,VictimName),
ActSectionAssociation(CaseMasterID,ActID,SectionID),
Section(SectionID,SectionCode,SectionDescription)
Use ZCQL syntax (similar to MySQL, use CURRENT_DATE, YEAR(), MONTH(), COUNT(), GROUP BY, ORDER BY, LIMIT).`;

const ANSWER_SYSTEM = `You are Nethra (ನೇತ್ರ), a Karnataka Police AI assistant.
Answer the user's crime data question in a clear, concise manner.
If the user wrote in Kannada, respond in Kannada.
Use the query results provided. Be factual and precise.`;

class LLMService {
  constructor(catalystApp) {
    this.catalystApp = catalystApp;
    this._sdkAvailable = typeof catalystApp.quickML === 'function';
  }

  async _callSDK(prompt, system, maxTokens = 300) {
    try {
      const model = this.catalystApp.quickML().model('llm');
      const result = await model.predict({
        messages: [
          { role: 'system', content: system },
          { role: 'user', content: prompt }
        ],
        max_tokens: maxTokens,
        temperature: 0.1,
      });
      return result?.output || result?.text || null;
    } catch (err) {
      logger.warn('QuickML SDK call failed', { error: err.message });
      return null;
    }
  }

  async _callREST(prompt, system, maxTokens = 300) {
    try {
      const token = await this._getOAuthToken();
      const resp = await fetch(LLM_ENDPOINT, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'catalyst-llm',
          messages: [
            { role: 'system', content: system },
            { role: 'user', content: prompt }
          ],
          max_tokens: maxTokens,
          temperature: 0.1,
        }),
      });
      if (!resp.ok) return null;
      const data = await resp.json();
      return data?.choices?.[0]?.message?.content?.trim() || null;
    } catch (err) {
      logger.warn('REST LLM call failed', { error: err.message });
      return null;
    }
  }

  async _getOAuthToken() {
    try {
      const oauth = this.catalystApp.oauth();
      const token = await oauth.generateAccessToken();
      return token?.access_token;
    } catch {
      return process.env.CATALYST_OAUTH_TOKEN || '';
    }
  }

  async _call(prompt, system, maxTokens = 300) {
    if (this._sdkAvailable) {
      const result = await this._callSDK(prompt, system, maxTokens);
      if (result) return result;
    }
    return this._callREST(prompt, system, maxTokens);
  }

  async classifyIntent(question) {
    const result = await this._call(question, INTENT_SYSTEM, 50);
    const valid = ['crime_query', 'trend_query', 'hotspot_query', 'offender_search', 'forecast_query', 'case_status', 'legal_reference', 'general'];
    if (result && valid.includes(result.toLowerCase())) {
      return result.toLowerCase();
    }
    return null;
  }

  async generateSql(question, crimeType, district) {
    const prompt = `User question: "${question}"
${crimeType ? `Crime type context: ${crimeType}` : ''}
${district ? `District context: ${district}` : ''}
Generate a valid ZCQL query for this question.`;
    return this._call(prompt, NL2SQL_SYSTEM, 400);
  }

  async generateAnswer(question, sqlResult, intent, lang) {
    const context = sqlResult ? JSON.stringify(sqlResult.slice(0, 10)) : 'No data returned';
    const prompt = `User question: "${question}"
Language: ${lang === 'kn' ? 'Kannada' : 'English'}
Intent: ${intent}
Query result: ${context}
Generate a helpful answer.`;
    return this._call(prompt, ANSWER_SYSTEM, 300);
  }
}

export default LLMService;
