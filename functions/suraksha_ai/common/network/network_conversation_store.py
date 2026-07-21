import uuid
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class NetworkConversationStore:
    def __init__(self, db_client):
        self._db = db_client

    def _esc(self, s):
        if s is None:
            return ''
        return str(s).replace("'", "''")

    def create(self, user_id, title="New Network Chat"):
        cid = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = (
            f"INSERT INTO NetworkConversations (conversation_id, user_id, title, "
            f"created_at, updated_at) VALUES ("
            f"'{cid}', '{self._esc(user_id)}', '{self._esc(title)}', "
            f"'{now}', '{now}')"
        )
        r = self._db.execute_non_query(sql)
        if r.get("error"):
            logger.error("create_network_conversation failed: %s", r.get("message"))
            return None
        return cid

    def add_message(self, conv_id, role, content_text):
        mid = str(uuid.uuid4())
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sql = (
            f"INSERT INTO NetworkChatMessages (message_id, conversation_id, role, "
            f"content_text, created_at) VALUES ("
            f"'{mid}', '{conv_id}', '{self._esc(role)}', "
            f"'{self._esc(content_text)}', '{now}')"
        )
        r = self._db.execute_non_query(sql)
        if r.get("error"):
            logger.error("add_network_message failed: %s", r.get("message"))
            return None
        self._db.execute_non_query(
            f"UPDATE NetworkConversations SET updated_at = '{now}' WHERE conversation_id = '{conv_id}'"
        )
        if role == 'user' and content_text:
            title = content_text[:200]
            self._db.execute_non_query(
                f"UPDATE NetworkConversations SET title = '{self._esc(title)}' "
                f"WHERE conversation_id = '{conv_id}' AND title = 'New Network Chat'"
            )
        return mid

    def get_messages(self, conv_id, limit=100):
        sql = (
            f"SELECT message_id, role, content_text, created_at "
            f"FROM NetworkChatMessages WHERE conversation_id = '{conv_id}' "
            f"ORDER BY created_at ASC LIMIT {limit}"
        )
        r = self._db.execute(sql)
        if r.get("error"):
            return []
        cols = r.get("columns", [])
        return [dict(zip(cols, row)) for row in r.get("rows", [])]

    def get(self, conv_id):
        sql = (
            f"SELECT conversation_id, user_id, title, created_at, "
            f"updated_at FROM NetworkConversations "
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
            f"SELECT conversation_id, title, created_at, "
            f"updated_at FROM NetworkConversations "
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
            f"DELETE FROM NetworkChatMessages WHERE conversation_id = '{conv_id}'"
        )
        self._db.execute_non_query(
            f"DELETE FROM NetworkConversations WHERE conversation_id = '{conv_id}'"
        )
