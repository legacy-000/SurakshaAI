import json
import logging

from common.sql.query_executor import QueryExecutor
from common.ai.schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    def __init__(self, catalyst_app=None):
        self.executor = QueryExecutor(catalyst_app)
        self.schema = SchemaRegistry(catalyst_app)

    @property
    def tool_def(self) -> dict:
        return self.schema.generate_tool_def()

    @property
    def system_prompt(self) -> str:
        return self.schema.generate_system_prompt()

    def execute_tool_call(self, tool_call: dict) -> dict:
        try:
            func_name = tool_call.get("function", {}).get("name", "")
            if func_name != "query_datastore":
                return {"error": "UNKNOWN_TOOL", "message": f"Unknown tool: {func_name}"}

            args_raw = tool_call.get("function", {}).get("arguments", "{}")
            if isinstance(args_raw, str):
                params = json.loads(args_raw)
            else:
                params = args_raw

            validation = self.schema.validate_tool_params(params)
            if not validation.get("valid"):
                return {"error": "INVALID_TOOL_PARAMS", "errors": validation.get("errors", [])}

            zcql = self.schema.build_zcql(params)
            result = self.executor.execute(zcql)
            result["tool_params"] = params
            result["generated_zcql"] = zcql
            return result

        except json.JSONDecodeError as e:
            return {"error": "INVALID_JSON", "message": f"Tool call arguments are not valid JSON: {e}"}
        except Exception as e:
            logger.exception("Tool execution failed")
            return {"error": "TOOL_EXECUTION_FAILED", "message": str(e)}
