import json
import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationStore:
    def __init__(self, db_client):
        self._db = db_client

    def _esc(self, s):
        if s is None:
            return ''
        return str(s).replace("'", "''")

    def _json(self, v):
        if isinstance(v, (list, dict)):
            return json.dumps(v)
        return v or ''

    def create(self, user_id, language_code="en"):
        cid = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = (
            f"INSERT INTO Conversations (conversation_id, user_id, title, "
            f"language_code, created_at, updated_at, is_archived) "
            f"VALUES ('{cid}', '{self._esc(user_id)}', 'New Chat', '{language_code}', "
            f"'{now}', '{now}', false)"
        )
        r = self._db.execute_non_query(sql)
        if r.get("error"):
            logger.error("create_conversation failed: %s", r.get("message"))
            return None
        return cid

    def add_message(self, conv_id, **kw):
        mid = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = (
            f"INSERT INTO ChatMessages (message_id, conversation_id, role, "
            f"content_text, content_kannada, sql_text, confidence_class, "
            f"evidence_json, followups_json, message_type, created_at) VALUES ("
            f"'{mid}', '{conv_id}', '{self._esc(kw.get('role', ''))}', "
            f"'{self._esc(kw.get('content_text', ''))}', "
            f"'{self._esc(kw.get('content_kannada', ''))}', "
            f"'{self._esc(kw.get('sql_text', ''))}', "
            f"'{self._esc(kw.get('confidence_class', ''))}', "
            f"'{self._esc(self._json(kw.get('evidence_json', '')))}', "
            f"'{self._esc(self._json(kw.get('followups_json', '')))}', "
            f"'{self._esc(kw.get('message_type', ''))}', '{now}')"
        )
        r = self._db.execute_non_query(sql)
        if r.get("error"):
            logger.error("add_message failed: %s", r.get("message"))
            return None
        self._db.execute_non_query(
            f"UPDATE Conversations SET updated_at = '{now}' WHERE conversation_id = '{conv_id}'"
        )
        title = kw.get('content_text', '')[:200]
        if kw.get('role') == 'user' and title:
            self._db.execute_non_query(
                f"UPDATE Conversations SET title = '{self._esc(title)}' "
                f"WHERE conversation_id = '{conv_id}' AND title = 'New Chat'"
            )
        return mid

    def add_attachment(self, conv_id, msg_id, file_name, mime_type, size_bytes, stratus_file_id):
        aid = str(uuid.uuid4())
        now = datetime.now().isoformat()
        sql = (
            f"INSERT INTO ChatAttachments (attachment_id, message_id, conversation_id, "
            f"file_name, mime_type, size_bytes, stratus_file_id, created_at) VALUES ("
            f"'{aid}', '{msg_id}', '{conv_id}', '{self._esc(file_name)}', "
            f"'{self._esc(mime_type)}', {size_bytes}, "
            f"'{self._esc(stratus_file_id)}', '{now}')"
        )
        self._db.execute_non_query(sql)

    def get_messages(self, conv_id, limit=100):
        sql = (
            f"SELECT message_id, role, content_text, content_kannada, sql_text, "
            f"confidence_class, evidence_json, followups_json, message_type, created_at "
            f"FROM ChatMessages WHERE conversation_id = '{conv_id}' "
            f"ORDER BY created_at ASC LIMIT {limit}"
        )
        r = self._db.execute(sql)
        if r.get("error"):
            return []
        cols = r.get("columns", [])
        return [dict(zip(cols, row)) for row in r.get("rows", [])]

    def get(self, conv_id):
        sql = (
            f"SELECT conversation_id, user_id, title, language_code, created_at, "
            f"updated_at FROM Conversations "
            f"WHERE conversation_id = '{conv_id}'"
        )
        r = self._db.execute(sql)
        if r.get("error") or r.get("row_count", 0) == 0:
            return None
        cols = r.get("columns", [])
        conv = dict(zip(cols, r["rows"][0]))
        conv["messages"] = self.get_messages(conv_id)
        return conv

    def list(self, user_id, limit=50):
        sql = (
            f"SELECT conversation_id, title, language_code, created_at, "
            f"updated_at FROM Conversations "
            f"WHERE user_id = '{self._esc(user_id)}' "
            f"ORDER BY updated_at DESC LIMIT {limit}"
        )
        r = self._db.execute(sql)
        if r.get("error"):
            return []
        cols = r.get("columns", [])
        return [dict(zip(cols, row)) for row in r.get("rows", [])]

    def delete(self, conv_id):
        self._db.execute_non_query(
            f"DELETE FROM ChatMessages WHERE conversation_id = '{conv_id}'"
        )
        self._db.execute_non_query(
            f"DELETE FROM ChatAttachments WHERE conversation_id = '{conv_id}'"
        )
        self._db.execute_non_query(
            f"DELETE FROM Conversations WHERE conversation_id = '{conv_id}'"
        )
