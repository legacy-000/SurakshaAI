-- KSP SURAKSHA AI - 31 Prototype Tables
-- Version 1.0

CREATE TABLE IF NOT EXISTS AppUserProfile (
    user_id VARCHAR(50) PRIMARY KEY,
    kgid VARCHAR(20) UNIQUE,
    first_name VARCHAR(100) NOT NULL,
    email VARCHAR(200) UNIQUE,
    role_id INT NOT NULL,
    unit_id INT,
    district_id INT,
    language_preference VARCHAR(5) DEFAULT 'en',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS RolePermission (
    role_id INT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    permitted_apis JSON NOT NULL,
    permitted_screens JSON NOT NULL,
    permitted_tables JSON NOT NULL,
    can_view_sql BOOLEAN DEFAULT FALSE,
    can_view_audit BOOLEAN DEFAULT FALSE,
    can_export_pdf BOOLEAN DEFAULT TRUE,
    can_view_pii BOOLEAN DEFAULT FALSE,
    can_manage_users BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS UserDataScope (
    scope_id INT PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    scope_type VARCHAR(20) NOT NULL,
    scope_value INT NOT NULL,
    is_aggregate_scope BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS Conversation (
    conversation_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(200),
    language_code VARCHAR(5) DEFAULT 'en',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_archived BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS ConversationMessage (
    message_id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36) NOT NULL,
    message_type VARCHAR(20) NOT NULL,
    content_text TEXT NOT NULL,
    content_kannada TEXT,
    sql_text TEXT,
    query_id VARCHAR(36),
    evidence_refs JSON,
    confidence_class VARCHAR(20),
    grounding_status VARCHAR(20),
    model_version VARCHAR(20),
    prompt_version VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS QueryExecution (
    query_id VARCHAR(36) PRIMARY KEY,
    conversation_id VARCHAR(36),
    user_id VARCHAR(50) NOT NULL,
    original_query TEXT NOT NULL,
    normalized_query TEXT,
    detected_language VARCHAR(5),
    generated_sql TEXT,
    sql_validation_status VARCHAR(20),
    sql_repair_count INT DEFAULT 0,
    source_tables JSON,
    applied_filters JSON,
    execution_status VARCHAR(20),
    row_count INT,
    execution_time_ms INT,
    error_code VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS QueryEvidence (
    evidence_id VARCHAR(36) PRIMARY KEY,
    query_id VARCHAR(36) NOT NULL,
    evidence_type VARCHAR(30) NOT NULL,
    source_table VARCHAR(50),
    source_record_id VARCHAR(50),
    source_column VARCHAR(50),
    filter_summary TEXT,
    display_label TEXT,
    confidence DECIMAL(3,2)
);

CREATE TABLE IF NOT EXISTS SavedQuery (
    saved_query_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    query_label VARCHAR(200) NOT NULL,
    query_text TEXT NOT NULL,
    sql_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Investigation (
    investigation_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS InvestigationCase (
    link_id VARCHAR(36) PRIMARY KEY,
    investigation_id VARCHAR(36) NOT NULL,
    case_master_id INT NOT NULL,
    notes TEXT,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS InvestigationQuery (
    link_id VARCHAR(36) PRIMARY KEY,
    investigation_id VARCHAR(36) NOT NULL,
    query_id VARCHAR(36) NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS SavedGraph (
    saved_graph_id VARCHAR(36) PRIMARY KEY,
    investigation_id VARCHAR(36) NOT NULL,
    graph_label VARCHAR(200) NOT NULL,
    center_node_name VARCHAR(200),
    graph_depth INT DEFAULT 2,
    node_count INT,
    edge_count INT,
    graph_data_json JSON NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS EntityResolutionCandidate (
    candidate_id VARCHAR(36) PRIMARY KEY,
    accused_master_id_1 INT NOT NULL,
    accused_master_id_2 INT NOT NULL,
    match_type VARCHAR(30) NOT NULL,
    match_score DECIMAL(5,2),
    match_features JSON,
    resolved_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ResolvedPersonEntity (
    entity_id VARCHAR(36) PRIMARY KEY,
    canonical_name VARCHAR(200) NOT NULL,
    name_variants JSON,
    age_range_min INT,
    age_range_max INT,
    gender_id INT,
    case_count INT DEFAULT 0,
    resolution_confidence VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS PersonEntityRecordLink (
    link_id VARCHAR(36) PRIMARY KEY,
    entity_id VARCHAR(36) NOT NULL,
    accused_master_id INT NOT NULL,
    link_confidence DECIMAL(3,2)
);

CREATE TABLE IF NOT EXISTS GraphProjectionRun (
    run_id VARCHAR(36) PRIMARY KEY,
    center_entity_name VARCHAR(200),
    graph_depth INT,
    node_count INT,
    edge_count INT,
    execution_time_ms INT,
    graph_json JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS GraphMetric (
    metric_id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    node_id VARCHAR(200) NOT NULL,
    degree_centrality DECIMAL(10,6),
    betweenness_centrality DECIMAL(10,6),
    weighted_degree DECIMAL(10,2),
    community_id INT
);

CREATE TABLE IF NOT EXISTS PriorityScoreExecution (
    execution_id VARCHAR(36) PRIMARY KEY,
    entity_id VARCHAR(36) NOT NULL,
    score_version VARCHAR(10) NOT NULL,
    total_score DECIMAL(5,2),
    risk_tier VARCHAR(20),
    raw_features_json JSON,
    normalized_features_json JSON,
    weights_json JSON,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    computed_by VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS PriorityScoreFeature (
    feature_id VARCHAR(36) PRIMARY KEY,
    execution_id VARCHAR(36) NOT NULL,
    feature_name VARCHAR(50) NOT NULL,
    feature_value_raw DECIMAL(10,4),
    feature_value_normalized DECIMAL(5,4),
    weight DECIMAL(3,2),
    contribution DECIMAL(5,4),
    is_missing BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS SimilarCaseIndex (
    index_id VARCHAR(36) PRIMARY KEY,
    case_master_id_1 INT NOT NULL,
    case_master_id_2 INT NOT NULL,
    similarity_score DECIMAL(5,4),
    similarity_features JSON,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS InvestigativeLead (
    lead_id VARCHAR(36) PRIMARY KEY,
    case_master_id INT NOT NULL,
    lead_type VARCHAR(50) NOT NULL,
    lead_description TEXT NOT NULL,
    confidence_class VARCHAR(20) NOT NULL,
    confidence_score DECIMAL(3,2),
    is_viewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS LeadEvidence (
    evidence_id VARCHAR(36) PRIMARY KEY,
    lead_id VARCHAR(36) NOT NULL,
    evidence_type VARCHAR(30) NOT NULL,
    source_table VARCHAR(50),
    source_record_id VARCHAR(50),
    evidence_description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ForecastRun (
    run_id VARCHAR(36) PRIMARY KEY,
    district_id INT,
    crime_sub_head_id INT,
    model_version VARCHAR(20) NOT NULL,
    training_window_days INT NOT NULL,
    forecast_horizon_days INT NOT NULL,
    mae DECIMAL(10,4),
    rmse DECIMAL(10,4),
    baseline_mae DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ForecastMetric (
    metric_id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    forecast_date DATE NOT NULL,
    predicted_count DECIMAL(10,2),
    lower_bound DECIMAL(10,2),
    upper_bound DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS CrimeForecast (
    forecast_id VARCHAR(36) PRIMARY KEY,
    run_id VARCHAR(36) NOT NULL,
    district_id INT,
    forecast_date DATE NOT NULL,
    predicted_cases DECIMAL(10,2),
    confidence_lower DECIMAL(10,2),
    confidence_upper DECIMAL(10,2),
    alert_triggered BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS EarlyWarningAlert (
    alert_id VARCHAR(36) PRIMARY KEY,
    rule_id VARCHAR(30) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    triggering_condition TEXT NOT NULL,
    district_id INT,
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS AlertEvidence (
    evidence_id VARCHAR(36) PRIMARY KEY,
    alert_id VARCHAR(36) NOT NULL,
    evidence_type VARCHAR(30) NOT NULL,
    evidence_data JSON NOT NULL,
    evidence_description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ReportJob (
    job_id VARCHAR(36) PRIMARY KEY,
    investigation_id VARCHAR(36),
    requested_by VARCHAR(50) NOT NULL,
    report_type VARCHAR(30) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    stratus_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS AuditLog (
    audit_id VARCHAR(36) PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trace_id VARCHAR(36) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    role_id INT,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(50),
    outcome VARCHAR(20) NOT NULL,
    error_code VARCHAR(20),
    client_ip VARCHAR(45),
    request_duration_ms INT,
    details_json JSON
);

CREATE TABLE IF NOT EXISTS SchemaMetadata (
    table_name VARCHAR(50),
    column_name VARCHAR(50),
    data_type VARCHAR(50),
    is_primary_key BOOLEAN DEFAULT FALSE,
    is_foreign_key BOOLEAN DEFAULT FALSE,
    references_table VARCHAR(50),
    references_column VARCHAR(50),
    description TEXT,
    pii_classification VARCHAR(20),
    is_queryable BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (table_name, column_name)
);

CREATE TABLE IF NOT EXISTS BusinessGlossary (
    term_id VARCHAR(36) PRIMARY KEY,
    term_english VARCHAR(200) NOT NULL,
    term_kannada VARCHAR(200),
    definition_english TEXT,
    definition_kannada TEXT,
    related_tables JSON,
    category VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS NLSQLExample (
    example_id VARCHAR(36) PRIMARY KEY,
    natural_language_query TEXT NOT NULL,
    generated_sql TEXT NOT NULL,
    intent_type VARCHAR(30),
    tables_used JSON,
    complexity_score INT
);

CREATE TABLE IF NOT EXISTS ModelRegistry (
    model_id VARCHAR(36) PRIMARY KEY,
    model_name VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    deployed_at TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    parameters_json JSON
);

CREATE TABLE IF NOT EXISTS PromptTemplateRegistry (
    template_id VARCHAR(36) PRIMARY KEY,
    template_name VARCHAR(50) NOT NULL,
    template_version VARCHAR(20) NOT NULL,
    template_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS FeatureFlag (
    flag_id VARCHAR(36) PRIMARY KEY,
    flag_name VARCHAR(50) NOT NULL UNIQUE,
    flag_value BOOLEAN DEFAULT FALSE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS FinancialAccount (
    account_id VARCHAR(36) PRIMARY KEY,
    account_number VARCHAR(50) NOT NULL,
    account_holder_name VARCHAR(200),
    bank_name VARCHAR(100),
    account_type VARCHAR(20),
    is_synthetic BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS FinancialTransaction (
    transaction_id VARCHAR(36) PRIMARY KEY,
    account_id VARCHAR(36),
    transaction_date DATE,
    amount DECIMAL(15,2),
    transaction_type VARCHAR(20),
    beneficiary_account VARCHAR(50),
    is_synthetic BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS CaseTransactionAssociation (
    association_id VARCHAR(36) PRIMARY KEY,
    case_master_id INT,
    transaction_id VARCHAR(36),
    is_synthetic BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS UserFeedback (
    feedback_id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(50),
    conversation_id VARCHAR(36),
    query_id VARCHAR(36),
    rating INT,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── Phase 5 — AI Governance (Gov* prefix) ────────────────────────────
-- Append-only durable mirror of in-memory registries in
-- functions/suraksha_ai/common/governance/governance.py.
-- State changes persist a fresh full row; cold-start hydrate keeps the
-- row with the highest ROWID per logical key. JSON columns are TEXT;
-- catalyst.json does not declare table schemas — this file is canonical.

CREATE TABLE IF NOT EXISTS GovModel (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    ModelId VARCHAR(36) NOT NULL,
    ModelName VARCHAR(100) NOT NULL,
    ModelVersion VARCHAR(50) NOT NULL,
    Provider VARCHAR(100),
    CapabilitiesJson TEXT,
    ParametersJson TEXT,
    RegisteredAt VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS GovPrompt (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    PromptId VARCHAR(36) NOT NULL,
    PromptName VARCHAR(100) NOT NULL,
    Template TEXT,
    PromptVersion VARCHAR(50),
    ModelId VARCHAR(36),
    CreatedAt VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS GovAgentCapability (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    AgentName VARCHAR(100) NOT NULL,
    CapabilitiesJson TEXT,
    Description TEXT,
    RequiredPermissionsJson TEXT,
    UpdatedAt VARCHAR(40)
);

CREATE TABLE IF NOT EXISTS GovExecution (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    ExecutionId VARCHAR(36) NOT NULL,
    MissionId VARCHAR(36),
    AgentName VARCHAR(100),
    Intent VARCHAR(100),
    InputQuery TEXT,
    StartedAt VARCHAR(40),
    CompletedAt VARCHAR(40),
    Status VARCHAR(20),
    OutputSummary TEXT,
    EvidenceIdsJson TEXT,
    Error TEXT
);

CREATE TABLE IF NOT EXISTS GovMission (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    MissionId VARCHAR(36) NOT NULL,
    Query TEXT,
    UserId VARCHAR(50),
    IntentsJson TEXT,
    Status VARCHAR(20),
    Summary TEXT,
    CreatedAt VARCHAR(40),
    CompletedAt VARCHAR(40),
    DetailsJson TEXT
);

CREATE TABLE IF NOT EXISTS GovMissionTask (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    TaskId VARCHAR(36) NOT NULL,
    MissionId VARCHAR(36) NOT NULL,
    AgentName VARCHAR(100),
    Intent VARCHAR(100),
    InputQuery TEXT,
    Status VARCHAR(20),
    StartedAt VARCHAR(40),
    CompletedAt VARCHAR(40),
    ResultJson TEXT,
    EvidenceJson TEXT,
    Error TEXT
);

CREATE TABLE IF NOT EXISTS GovClaim (
    ROWID INT AUTO_INCREMENT PRIMARY KEY,
    ClaimId VARCHAR(36) NOT NULL,
    Statement TEXT,
    Classification VARCHAR(50),
    Producer VARCHAR(100),
    ModelVersion VARCHAR(50),
    EvidenceRefsJson TEXT,
    Confidence DECIMAL(5,4),
    ConfidenceLabel VARCHAR(10),
    ValidationStatus VARCHAR(50),
    GrantedAt VARCHAR(40),
    ExpiresAt VARCHAR(40),
    Status VARCHAR(50),
    SourceExecutionId VARCHAR(36),
    ClaimMetadataJson TEXT
);
