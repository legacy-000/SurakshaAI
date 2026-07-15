import json, uuid
from datetime import datetime
from typing import Optional
from models.dto import MessageDTO, MessageSenderDTO, OrgUnitDTO, MessageRecipientStatus, MessageAttachmentDTO


class MessageEngine:
    def __init__(self, db=None):
        self._db = db
        self._messages = {}
        self._threads = {}
        self._table = "CommsMessages"

    def _is_live(self):
        return self._db and self._db.is_connected

    def _row_to_dto(self, row: dict) -> Optional[MessageDTO]:
        try:
            return MessageDTO(
                message_id=row.get("message_id", ""),
                type=row.get("type", "STATUS_UPDATE"),
                sender=MessageSenderDTO(**json.loads(row.get("sender_json", "{}"))),
                recipients=[MessageRecipientStatus(**r) for r in json.loads(row.get("recipients_json", "[]"))],
                cc=[MessageRecipientStatus(**r) for r in json.loads(row.get("cc_json", "[]"))],
                subject=row.get("subject", ""),
                body=row.get("body", ""),
                linked_resources=json.loads(row.get("linked_resources_json", "[]")),
                attachments=[MessageAttachmentDTO(**a) for a in json.loads(row.get("attachments_json", "[]"))],
                priority=row.get("priority", "NORMAL"),
                status=row.get("status", "SENT"),
                created_at=row.get("created_at", ""),
                sent_at=row.get("sent_at"),
                parent_message_id=row.get("parent_message_id"),
                thread_id=row.get("thread_id"),
            )
        except Exception:
            return None

    def _upsert(self, msg: MessageDTO):
        self._messages[msg.message_id] = msg
        tid = msg.thread_id or msg.message_id
        if tid not in self._threads:
            self._threads[tid] = []
        if msg.message_id not in self._threads[tid]:
            self._threads[tid].append(msg.message_id)

    def send(self, msg_type: str, sender_id: int, sender_rank: str,
             sender_unit_id: int, sender_unit_name: str,
             to_ids: list[int], subject: str, body: str,
             cc_ids: list[int] = None, linked_resources: list[dict] = None,
             attachments: list[dict] = None, priority: str = "NORMAL",
             parent_message_id: str = None) -> MessageDTO:
        now = datetime.now().isoformat()
        thread_id = parent_message_id or str(uuid.uuid4())
        if parent_message_id and parent_message_id in self._messages:
            p = self._messages[parent_message_id]
            thread_id = p.thread_id or p.message_id

        msg = MessageDTO(
            message_id=str(uuid.uuid4()),
            type=msg_type,
            sender=MessageSenderDTO(employee_id=sender_id, rank=sender_rank, unit=OrgUnitDTO(unit_id=sender_unit_id, unit_name=sender_unit_name)),
            recipients=[MessageRecipientStatus(employee_id=eid, status="sent", delivered_at=now) for eid in to_ids],
            cc=[MessageRecipientStatus(employee_id=eid, status="sent", delivered_at=now) for eid in (cc_ids or [])],
            subject=subject, body=body,
            linked_resources=linked_resources or [],
            attachments=[MessageAttachmentDTO(**a) for a in (attachments or [])],
            priority=priority, status="SENT", created_at=now, sent_at=now,
            parent_message_id=parent_message_id, thread_id=thread_id,
        )
        if self._is_live():
            self._db.execute_non_query(
                f"INSERT INTO {self._table} (message_id, type, sender_json, recipients_json, cc_json, subject, body, linked_resources_json, attachments_json, priority, status, created_at, sent_at, parent_message_id, thread_id) VALUES ("
                f"'{msg.message_id}','{msg.type}','{json.dumps(msg.sender.model_dump()).replace(chr(39),chr(39)+chr(39))}',"
                f"'{json.dumps([r.model_dump() for r in msg.recipients]).replace(chr(39),chr(39)+chr(39))}',"
                f"'{json.dumps([r.model_dump() for r in msg.cc]).replace(chr(39),chr(39)+chr(39))}',"
                f"'{msg.subject.replace(chr(39),chr(39)+chr(39))}','{msg.body.replace(chr(39),chr(39)+chr(39))}',"
                f"'{json.dumps(msg.linked_resources).replace(chr(39),chr(39)+chr(39))}',"
                f"'{json.dumps([a.model_dump() for a in msg.attachments]).replace(chr(39),chr(39)+chr(39))}',"
                f"'{msg.priority}','{msg.status}','{msg.created_at}','{msg.sent_at}',"
                f"{'NULL' if not msg.parent_message_id else chr(39)+msg.parent_message_id.replace(chr(39),chr(39)+chr(39))+chr(39)},"
                f"'{msg.thread_id}')"
            )
        self._upsert(msg)
        return msg

    def get(self, message_id: str) -> Optional[MessageDTO]:
        if message_id in self._messages:
            return self._messages[message_id]
        if self._is_live():
            res = self._db.execute_non_query(f"SELECT * FROM {self._table} WHERE message_id='{message_id.replace(chr(39),chr(39)+chr(39))}'")
            if res.get("rows"):
                m = self._row_to_dto(dict(zip(res["columns"], res["rows"][0])))
                if m:
                    self._messages[m.message_id] = m
                    return m
        return None

    def list_inbox(self, employee_id: int, unread_only: bool = False,
                   priority_filter: str = None, since: str = None) -> list[MessageDTO]:
        if self._is_live():
            sql = f"SELECT * FROM {self._table} WHERE status!='DRAFT'"
            if since:
                sql += f" AND sent_at>'{since.replace(chr(39),chr(39)+chr(39))}'"
            res = self._db.execute_non_query(sql)
            if res.get("rows"):
                for row in res["rows"]:
                    m = self._row_to_dto(dict(zip(res["columns"], row)))
                    if m:
                        self._upsert(m)
        msgs = []
        for m in self._messages.values():
            if since and (m.sent_at or m.created_at) <= since:
                continue
            is_recip = any(r.employee_id == employee_id for r in m.recipients)
            is_cc = any(c.employee_id == employee_id for c in m.cc)
            if not is_recip and not is_cc:
                continue
            if unread_only and m.status in ("READ", "ACKNOWLEDGED"):
                continue
            if priority_filter and m.priority != priority_filter:
                continue
            msgs.append(m)
        return sorted(msgs, key=lambda m: m.sent_at or m.created_at, reverse=True)

    def mark_read(self, message_id: str, employee_id: int) -> bool:
        msg = self._messages.get(message_id)
        if not msg and self._is_live():
            msg = self.get(message_id)
        if not msg:
            return False
        for r in msg.recipients:
            if r.employee_id == employee_id:
                r.status = "READ"
                r.read_at = datetime.now().isoformat()
        for c in msg.cc:
            if c.employee_id == employee_id:
                c.status = "READ"
                c.read_at = datetime.now().isoformat()
        all_read = all(r.status in ("READ", "ACKNOWLEDGED") for r in msg.recipients)
        if all_read:
            msg.status = "READ"
        if self._is_live():
            recipients_json = json.dumps([r.model_dump() for r in msg.recipients])
            cc_json = json.dumps([r.model_dump() for r in msg.cc])
            self._db.execute_non_query(
                f"UPDATE {self._table} SET recipients_json='{recipients_json.replace(chr(39),chr(39)+chr(39))}',cc_json='{cc_json.replace(chr(39),chr(39)+chr(39))}',status='{msg.status}' WHERE message_id='{message_id.replace(chr(39),chr(39)+chr(39))}'"
            )
        return True

    def acknowledge(self, message_id: str, employee_id: int) -> bool:
        msg = self._messages.get(message_id)
        if not msg and self._is_live():
            msg = self.get(message_id)
        if not msg:
            return False
        for r in msg.recipients:
            if r.employee_id == employee_id:
                r.status = "ACKNOWLEDGED"
        msg.status = "ACKNOWLEDGED"
        if self._is_live():
            recipients_json = json.dumps([r.model_dump() for r in msg.recipients])
            self._db.execute_non_query(
                f"UPDATE {self._table} SET recipients_json='{recipients_json.replace(chr(39),chr(39)+chr(39))}',status='{msg.status}' WHERE message_id='{message_id.replace(chr(39),chr(39)+chr(39))}'"
            )
        return True

    def get_thread(self, message_id: str) -> list[MessageDTO]:
        msg = self.get(message_id)
        if not msg:
            return []
        tid = msg.thread_id or msg.message_id
        return [self._messages[mid] for mid in self._threads.get(tid, []) if mid in self._messages]

    def list_all(self) -> list[MessageDTO]:
        if self._is_live():
            res = self._db.execute_non_query(f"SELECT * FROM {self._table}")
            if res.get("rows"):
                for row in res["rows"]:
                    m = self._row_to_dto(dict(zip(res["columns"], row)))
                    if m:
                        self._upsert(m)
        return list(self._messages.values())
