import logging
import sys
import os
from flask import Request, make_response, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from functions.main import SurakshaAIHandler
from models.dto import UserContextDTO

logger = logging.getLogger()
handler = SurakshaAIHandler()

def handler_fn(request: Request):
    body = request.get_json(silent=True) or {}

    action = body.get("action", "")
    params = body.get("params", {})
    session = body.get("session", {})
    user_context = session.get("user_context", {})

    try:
        if action in ("get_crime_stats", "chat_query"):
            message = params.get("message", params.get("query", ""))
            result = handler.chat.handle_query(
                query=message,
                user_context=UserContextDTO(
                    user_id=user_context.get("user_id", "convokraft"),
                    role_id=user_context.get("role_id", 1),
                    district_id=user_context.get("district_id"),
                )
            )
            return jsonify({
                "text": result.get("content_text", ""),
                "text_kn": result.get("content_kannada", ""),
                "metadata": {
                    "sql": result.get("sql_text"),
                    "chart": result.get("chart_recommendation"),
                    "evidence": result.get("evidence_refs", []),
                }
            }), 200

        elif action == "search_offender":
            name = params.get("name", "")
            result = handler.offender.profile_offender(name)
            return jsonify({
                "text": f"Offender {name}: Score {result.get('total_score', 'N/A')} - {result.get('risk_tier', 'Unknown')}",
                "text_kn": f"ಆರೋಪಿ {name}: ಸ್ಕೋರ್ {result.get('total_score', 'N/A')} - {result.get('risk_tier', 'Unknown')}",
                "metadata": result
            }), 200

        elif action == "get_trends":
            result = handler.trends.analyze_trends(params)
            return jsonify({
                "text": f"Crime trends analyzed across {len(result.get('data', []))} periods.",
                "metadata": result
            }), 200

        elif action == "get_hotspots":
            result = handler.hotspots.detect_hotspots(params)
            return jsonify({
                "text": f"Found {len(result.get('clusters', []))} crime hotspots.",
                "text_kn": f"{len(result.get('clusters', []))} ಅಪರಾಧ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳು ಪತ್ತೆಯಾಗಿವೆ.",
                "metadata": result
            }), 200

        else:
            return jsonify({
                "text": f"Unknown action '{action}'. Available: chat_query, search_offender, get_trends, get_hotspots.",
                "text_kn": f"ಅಜ್ಞಾತ ಕ್ರಿಯೆ '{action}'."
            }), 200

    except Exception as e:
        logger.exception("Nethra action error")
        return jsonify({
            "text": f"Error: {str(e)}",
            "text_kn": "ದೋಷ ಸಂಭವಿಸಿದೆ."
        }), 500
