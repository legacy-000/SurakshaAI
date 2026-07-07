-- CaseMaster indexes
CREATE INDEX IF NOT EXISTS idx_cm_date ON CaseMaster(CrimeRegisteredDate);
CREATE INDEX IF NOT EXISTS idx_cm_station ON CaseMaster(PoliceStationID);
CREATE INDEX IF NOT EXISTS idx_cm_status ON CaseMaster(CaseStatusID);
CREATE INDEX IF NOT EXISTS idx_cm_crimehead ON CaseMaster(CrimeMinorHeadID);
CREATE INDEX IF NOT EXISTS idx_cm_gps ON CaseMaster(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_cm_category ON CaseMaster(CaseCategoryID);

-- Accused indexes
CREATE INDEX IF NOT EXISTS idx_acc_name ON Accused(AccusedName);
CREATE INDEX IF NOT EXISTS idx_acc_case ON Accused(CaseMasterID);

-- ArrestSurrender indexes
CREATE INDEX IF NOT EXISTS idx_as_date ON ArrestSurrender(ArrestSurrenderDate);
CREATE INDEX IF NOT EXISTS idx_as_accused ON ArrestSurrender(AccusedMasterID);

-- QueryExecution indexes
CREATE INDEX IF NOT EXISTS idx_qe_user ON QueryExecution(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_qe_conv ON QueryExecution(conversation_id);

-- EarlyWarningAlert indexes
CREATE INDEX IF NOT EXISTS idx_awa_district ON EarlyWarningAlert(district_id, created_at);

-- AuditLog indexes
CREATE INDEX IF NOT EXISTS idx_al_user ON AuditLog(user_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_al_trace ON AuditLog(trace_id);

-- Conversation indexes
CREATE INDEX IF NOT EXISTS idx_conv_user ON Conversation(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON ConversationMessage(conversation_id, created_at);

-- Investigation indexes
CREATE INDEX IF NOT EXISTS idx_inv_user ON Investigation(user_id, status);
