# SURAKSHA Police FIR System — Technical Support & System Maintenance Role

**Document Version:** 1.0  
**Last Updated:** 2026-07-15  
**Audience:** System Administrators, Technical Support Engineers, Database Administrators, DevOps Engineers  
**Confidentiality:** Internal Use Only

---

## 1. Technical Support Role Definition

### 1.1 Role Overview

The **Technical Support Engineer (TSE)** / **System Technician** is a cross-organizational role that provides diagnostic, debugging, and maintenance support across all layers of the SURAKSHA system **without direct access to operational case data**.

| Attribute | Value |
|---|---|
| **Role Name** | Technical Support Engineer / System Technician |
| **Org Level** | State / Central Support Hub (crosses all districts/stations) |
| **Primary Authority** | System Health, Debugging, Configuration, Schema Integrity |
| **Data Access Scope** | Metadata, logs, schema, configuration, query plans — NOT case data |
| **Cross-Organizational Authority** | YES — unrestricted across districts, stations, units |
| **Emergency Authority** | Can escalate issues to State Commissioner for emergency overrides |
| **Audit Trail Visibility** | Can view audit logs for debugging (filtered for system errors, not data) |

### 1.2 Key Distinction: "Technical Access vs Data Access"

```
┌─────────────────────────────────────────────────────────────┐
│  TECHNICAL SUPPORT ENGINEER                                 │
│                                                              │
│  ✓ CAN:                          ✗ CANNOT:                 │
│  • Query schema structure         • View case data           │
│  • Execute diagnostic queries     • Access FIR details       │
│  • Read error logs                • See victim/accused info  │
│  • Check query performance        • Read witness statements  │
│  • Validate SQL correctness       • Access evidence storage  │
│  • Fix configuration issues       • View location data       │
│  • Modify system parameters       • Query offender pool      │
│  • Reset cached data              • Generate case reports    │
│  • Check authentication tokens    • Access arrest records    │
│  • Monitor database health        • See chargesheet details  │
│  • Review audit trails (errors)   • Query network analytics  │
│  • Patch schema/structure bugs    • Access forecasting data  │
│                                    • View intelligence alerts │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Authority Scope & Decision Rights

### 2.1 Full Technical Authority Matrix

| Task Category | Scope | Authority | Limitations |
|---|---|---|---|
| **Schema Debugging** | All tables, stored procs, views | Unrestricted | Cannot alter data; only structure/indexes |
| **Query Optimization** | All queries (across all roles) | Unrestricted | Cannot execute against live data (must use explain/plan) |
| **Error Log Access** | All error/exception logs | Unrestricted | System errors only; data access errors filtered for PII |
| **Configuration Management** | All system settings, parameters | Unrestricted | Must log changes; requires peer review for critical params |
| **Performance Monitoring** | CPU, memory, disk, query plans | Unrestricted | Cannot access query result sets |
| **Authentication & Tokens** | Session tokens, JWT inspection | Unrestricted | Cannot use tokens to access user data |
| **Backup & Recovery** | Database backups, restore procedures | Restricted | Requires State Commissioner approval for restore |
| **Schema Patches** | Bug fixes, index creation, constraints | Restricted | Requires peer review + DSP approval |
| **API Gateway Debugging** | Request/response logs, rate limits | Unrestricted | Headers/payloads only; no decrypted data |
| **Cache Operations** | Clear caches, validate cache integrity | Unrestricted | No data visibility |
| **Permission Audits** | Role-based access lists, effective permissions | Restricted | Read-only; cannot modify permissions (admin-only) |

### 2.2 Authority Tree for Technical Support

```
┌─ TECHNICAL SUPPORT ENGINEER ────────────────────────────────┐
│ Can:                                                        │
│  ✓ Diagnose errors without viewing data                     │
│  ✓ Execute EXPLAIN/ANALYZE on queries across all roles      │
│  ✓ Read system logs, error traces, stack traces             │
│  ✓ Inspect database schema across all tables                │
│  ✓ Create/modify indexes for performance                    │
│  ✓ Reset database sessions, kill hung queries               │
│  ✓ Verify SQL syntax and execution plans                    │
│  ✓ Check authentication/authorization mechanisms           │
│  ✓ Monitor system resources (CPU, memory, disk)             │
│  ✓ Validate data integrity (constraints, referential)       │
│  ✓ Access all audit trails filtered for system events       │
│  ✓ Patch schema bugs and deployment errors                  │
│  ✓ Configure system parameters and feature flags            │
│  ✓ Escalate critical issues to State Commissioner           │
│  ✓ Communicate technical findings to operators              │
│  ✗ View case data, victims, accused, evidence               │
│  ✗ Modify permissions or role assignments                   │
│  ✗ Approve chargesheet or operational actions               │
│  ✗ Access investigation details or arrest records           │
│  ✗ Generate intelligence products or forecasts              │
│  ✗ Restore backups without State Commissioner approval      │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Operational Responsibilities

### 3.1 Daily Monitoring & Health Checks

| Task | Frequency | Tool/Method | Success Criteria |
|---|---|---|---|
| Database connectivity check | Every 4 hours | `SELECT 1` heartbeat | <100ms response time |
| Query performance baseline | Daily 08:00 | Query execution stats | No queries >30s without explanation |
| Error log aggregation | Every 2 hours | Log aggregator (ELK/Splunk) | Review top 10 errors, escalate >10 same error |
| Cache hit rate validation | Daily 18:00 | Cache metrics dashboard | >85% hit rate for all caches |
| Authentication token validity | Hourly | JWT inspection tool | No expired tokens in active sessions |
| Schema integrity checks | Daily 09:00 | Foreign key/constraint validation | All constraints pass; zero orphaned rows |
| Storage capacity forecast | Weekly | Disk usage trend | Alert if projected full in <30 days |
| Backup completeness | Daily 23:30 | Backup log verification | All daily backups completed, checksums match |

### 3.2 Incident Response Responsibilities

#### **Incident Category 1: Query Performance Degradation**

| Trigger | Investigation | Resolution | Escalation |
|---|---|---|---|
| A query >30s without known reason | 1. EXPLAIN ANALYZE<br>2. Check index usage<br>3. Review query plan<br>4. Check table stats | 1. Create index if missing<br>2. Suggest query rewrite<br>3. Analyze hints to developer<br>4. Test on staging | If root cause is data growth: DSP approval needed |

#### **Incident Category 2: Authentication Failures**

| Trigger | Investigation | Resolution | Escalation |
|---|---|---|---|
| >5 failed logins in 5 minutes | 1. Check token generation<br>2. Inspect JWT payload<br>3. Verify key rotation<br>4. Check LDAP connectivity | 1. Restart auth service<br>2. Rotate keys if stale<br>3. Sync LDAP if out of sync<br>4. Clear session cache | If LDAP unavailable: State-level incident |

#### **Incident Category 3: Data Corruption / Constraint Violation**

| Trigger | Investigation | Resolution | Escalation |
|---|---|---|---|
| Referential integrity alert | 1. Identify orphaned rows<br>2. Determine cause (stale code? bug?)<br>3. Validate across instances | 1. Run constraint check<br>2. Log details for audit<br>3. Propose fix (if safe)<br>4. Test fix on staging | Requires DSP approval before executing fix |

#### **Incident Category 4: System Resource Exhaustion**

| Trigger | Investigation | Resolution | Escalation |
|---|---|---|---|
| Disk >85% OR CPU >90% sustained | 1. Identify consuming process<br>2. Check log file growth<br>3. Verify backup chaining<br>4. Inspect temp space | 1. Archive old logs (safe)<br>2. Clear temp space<br>3. Scale resources if needed<br>4. Alert on thresholds | If requires hardware change: State Commissioner approval |

### 3.3 Proactive Maintenance Tasks

#### **Monthly Maintenance Schedule**

| Week | Task | Duration | Impact | Approval Needed |
|---|---|---|---|---|
| Week 1 | Query plan analysis & optimization report | 4 hours | None (read-only) | DSP (informational) |
| Week 2 | Index fragmentation check & rebuild if needed | 2-4 hours | Requires brief maintenance window | DSP (schedule coordination) |
| Week 3 | Role-based access control audit | 3 hours | None (audit-only) | None (report to State Commissioner) |
| Week 4 | Database statistics refresh | 1 hour | May improve query performance | DSP (optional) |

#### **Quarterly Maintenance Tasks**

| Task | Scope | Impact | Approval |
|---|---|---|---|
| Full schema review for consistency | All tables, views, stored procs | None (review-only) | DSP briefing |
| Backup restore testing | Staging environment (copy of schema) | Staging only; no production impact | None required |
| Security audit (authentication/encryption) | All API endpoints, token rotation | None (audit-only) | State Commissioner (summary) |
| Performance regression testing | Baseline queries across all agents | Staging only | DSP (optimization recommendations) |

---

## 4. Debug Access & Query Patterns

### 4.1 Allowed Debug Queries (Schema/Metadata/Logs)

```sql
-- ✓ ALLOWED: Schema inspection
SELECT * FROM information_schema.tables WHERE table_schema = 'public';
SELECT * FROM information_schema.columns WHERE table_name = 'CaseMaster';
SELECT * FROM pg_indexes WHERE tablename = 'Victim';

-- ✓ ALLOWED: Query execution plans (no result viewing)
EXPLAIN ANALYZE SELECT * FROM CaseMaster LIMIT 1;
EXPLAIN (FORMAT JSON) SELECT * FROM Accused WHERE AgeYear > 50;

-- ✓ ALLOWED: Index statistics
SELECT * FROM pg_stat_user_indexes WHERE relname = 'idx_case_status';
SELECT * FROM pg_stat_user_tables;

-- ✓ ALLOWED: Error logs (filtered)
SELECT error_timestamp, error_code, stack_trace FROM system_logs 
  WHERE log_level = 'ERROR' AND error_timestamp > NOW() - INTERVAL 24 HOUR;

-- ✓ ALLOWED: Session inspection
SELECT pid, usename, application_name, state FROM pg_stat_activity;

-- ✓ ALLOWED: Cache statistics
SELECT cache_name, hit_rate, eviction_count FROM cache_metrics;

-- ✓ ALLOWED: Authentication audit (logged)
SELECT token_id, token_issuer, issued_at, expires_at FROM auth_tokens 
  WHERE status = 'EXPIRED' AND expires_at > NOW() - INTERVAL 7 DAY;
```

### 4.2 Forbidden Queries (Data Access)

```sql
-- ✗ FORBIDDEN: Accessing case data
SELECT * FROM CaseMaster;
SELECT crime_no, brief_facts FROM CaseMaster;

-- ✗ FORBIDDEN: Accessing personal information
SELECT victim_name, age FROM Victim;
SELECT accused_name, address FROM Accused;

-- ✗ FORBIDDEN: Accessing investigation details
SELECT * FROM Evidence WHERE case_id = ?;
SELECT witness_statement FROM Witness_Deposition;

-- ✗ FORBIDDEN: Accessing charges and legal information
SELECT * FROM ActSectionAssociation WHERE case_id = ?;
SELECT chargesheet_details FROM ChargesheetDetails;

-- ✗ FORBIDDEN: Accessing results of intelligence operations
SELECT * FROM CaseNetwork_Graph;
SELECT * FROM Offender_Similarity_Scores;
SELECT forecast_data FROM Trend_Forecasts;
```

### 4.3 Audit Trail for Technical Access

Every technical support query is logged with:

```
{
  "timestamp": "2026-07-15T14:32:05Z",
  "technician_id": "TSE_001",
  "query_type": "SCHEMA_INSPECTION",
  "target_table": "CaseMaster",
  "action": "EXPLAIN_ANALYZE",
  "result_summary": "Query plan retrieved; 3 sequential scans identified",
  "data_accessed": false,
  "approval_required": false,
  "audit_id": "AUD_20260715_000234"
}
```

---

## 5. Communication & Escalation Protocols

### 5.1 Issue Communication Matrix

| Issue Severity | Reporter | Communication | Escalation Path | Response Time |
|---|---|---|---|---|
| **Critical** (System Down) | All users report to TSE via hotline | Email + SMS to DSP + State Commissioner | DSP → State Commissioner (immediate) | 15 minutes |
| **High** (Performance Impair) | Users via ticket system | Slack + email to DSP | TSE → DSP → State if >1 hour | 30 minutes |
| **Medium** (Minor Error) | Users via ticket system | Email to DSP (informational) | TSE → DSP (next business day) | 4 hours |
| **Low** (Optimization) | TSE proactive detection | Monthly report to DSP | TSE → DSP (scheduled) | Next week |

### 5.2 Escalation Decision Tree

```
Issue Detected by TSE
        │
        ├─ CAN FIX WITHOUT PRODUCTION RISK?
        │  ├─ YES → Execute fix (log it) → Notify DSP (email) → DONE
        │  └─ NO → Continue
        │
        ├─ INVOLVES SCHEMA/DATA INTEGRITY?
        │  ├─ YES → Get DSP approval → Execute → Log → Notify SHO/Station
        │  └─ NO → Continue
        │
        ├─ REQUIRES SYSTEM DOWNTIME?
        │  ├─ YES → Get State Commissioner approval → Schedule → Execute
        │  └─ NO → Continue
        │
        └─ CRITICAL (SYSTEM DOWN)?
           ├─ YES → Escalate immediately → Page on-call DSP → Engage all resources
           └─ NO → Standard escalation path
```

### 5.3 Communication Templates

#### **Template 1: Diagnostic Report (to DSP)**

```
SUBJECT: SURAKSHA System Diagnostic Report — [DATE]

TO: DSP [District]
FROM: Technical Support Engineer [TSE_ID]
CC: State Commissioner (informational)

ISSUE SUMMARY:
[Brief description of findings]

TECHNICAL DETAILS:
├─ Component Affected: [DB/API/Auth/Cache/etc]
├─ Severity: [Critical/High/Medium/Low]
├─ User Impact: [None/Minor/Significant/Total outage]
├─ Root Cause: [Technical analysis without data details]
├─ Recommended Action: [Fix/Workaround/Monitor]
└─ Estimated Resolution Time: [X hours/days]

NEXT STEPS:
[ ] Awaiting DSP approval to proceed
[ ] Fix deployed to staging for testing
[ ] Ready for production deployment

---
Report generated: [timestamp]
Audit Trail: AUD_[ID]
```

#### **Template 2: Issue Escalation (Critical)**

```
ALERT: CRITICAL SYSTEM ISSUE

TO: State Commissioner, DSP [District]
FROM: Technical Support Engineer [TSE_ID]

ISSUE: [One-line critical issue]
STATUS: ACTIVE
IMPACT: [Users affected / Data at risk / Service degraded]

IMMEDIATE ACTIONS TAKEN:
1. [Diagnostic step taken]
2. [Mitigation step taken]
3. [Rollback if needed]

CURRENT STATE:
├─ System Status: [Up/Degraded/Down]
├─ User Impact: [Affected stations/districts]
└─ Next Action: [Escalation to State Commissioner]

COMMUNICATION:
- State Commissioner notified: ✓ [time]
- SHO notified: ✓ [time]
- Users notified: ✓ [time]

Standing by for approval to execute permanent fix.
```

---

## 6. Tools & Access Credentials

### 6.1 Required System Access

| Tool | Purpose | Access Level | Credential Type |
|---|---|---|---|
| **PostgreSQL/Oracle Client** | Direct database access | Read-only for schema/logs | Service account (TSE_SVC) |
| **Query Profiler** (pgAdmin/TOAD) | Query plan analysis | Read-only for schema | Service account |
| **Log Aggregator** (ELK/Splunk) | Error log analysis | Read filter: system logs only | Single sign-on (SSO) |
| **Performance Dashboard** (Grafana) | System metrics monitoring | Read-only | SSO |
| **API Gateway Console** (Kong/AWS) | Request/response logs | Read headers/status only | SSO |
| **Git Repository** | Schema version control, deployment scripts | Read-only for production | SSO + 2FA |
| **VPN/Bastion Host** | Secure access to production systems | IP-restricted, MFA required | SSH keys (rotated quarterly) |
| **Ticket System** (Jira) | Issue tracking and approvals | Create, update tickets | SSO |
| **Audit Log Viewer** | Technical audit trail inspection | Filtered view (system events) | SSO |

### 6.2 Credential Rotation Policy

| Credential Type | Rotation Frequency | Owner | Approval |
|---|---|---|---|
| Database service account | Quarterly | State DBA | State Commissioner |
| SSH private keys | Quarterly | TSE + Admin | State Commissioner |
| API tokens | Monthly | TSE | DSP |
| Cache keys | Upon refresh | TSE | DSP |

---

## 7. Limitations & Restrictions

### 7.1 Hard Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│ ABSOLUTE RESTRICTIONS FOR TECHNICAL SUPPORT ENGINEERS       │
│                                                              │
│ ✗ CANNOT modify user permissions or roles                   │
│ ✗ CANNOT decrypt encryption keys or access encrypted data  │
│ ✗ CANNOT approve or reject operational decisions            │
│ ✗ CANNOT restore backups without State Commissioner approval│
│ ✗ CANNOT access case data under any circumstance            │
│ ✗ CANNOT bypass audit trails or delete logs                 │
│ ✗ CANNOT create new roles or modify role definitions        │
│ ✗ CANNOT export data in any form (even aggregate)           │
│ ✗ CANNOT share credentials with non-TSE personnel           │
│ ✗ CANNOT perform operations outside documented scope        │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Conditional Restrictions

| Scenario | Restriction | Reason | Workaround |
|---|---|---|---|
| Requires schema changes to fix bug | Must get DSP + peer review approval | Data integrity risk | Submit change request 48 hours in advance |
| Requires database restart | Must get State Commissioner approval | Operational disruption | Schedule during maintenance window |
| Diagnose user permission issue | Cannot view user's actual permissions | Privacy + audit control | Request formal permission audit via DSP |
| Need to copy production data to staging | Cannot copy any data | Privacy + compliance | Use schema-only scripts + synthetic data |
| Cache invalidation affects performance | Can clear cache freely | System health | Log cache clears in audit trail |

### 7.3 Seasonal/Emergency Overrides

In **emergency situations** (system completely down, critical security breach), a TSE may:

1. **Escalate directly to State Commissioner** for emergency override
2. **Execute critical patches** with concurrent State Commissioner notification
3. **Authorize temporary relaxation** of normal approval workflows
4. **Maintain detailed audit trails** of all emergency actions

After emergency resolution, a **post-incident review** is mandatory within 24 hours.

---

## 8. Security & Compliance

### 8.1 Confidentiality Commitments

Every TSE must sign:

```
CONFIDENTIALITY & NON-DISCLOSURE AGREEMENT

I, [Name], as Technical Support Engineer, acknowledge:

1. I will access SURAKSHA systems ONLY for legitimate technical debugging
2. I will NOT view, access, or disclose any case data, even if encountered
3. I will NOT discuss technical findings with unauthorized personnel
4. I understand that all my actions are logged and auditable
5. Violation of this agreement will result in immediate termination and criminal prosecution

Signature: ________________
Date: ________________
Witness (DSP): ________________
```

### 8.2 Security Training Requirements

| Training | Frequency | Certification | Mandatory |
|---|---|---|---|
| SURAKSHA Data Handling & Privacy | Annual | Yes | YES |
| SQL Injection & Database Security | Annual | Yes | YES |
| Incident Response Protocol | Annual | Yes | YES |
| Audit Trail & Compliance | Annual | Yes | YES |
| Emergency Escalation Procedures | Semi-annual | Yes | YES |

### 8.3 Audit & Oversight

```
AUDIT COVERAGE FOR TECHNICAL SUPPORT ENGINEERS:

Every Query/Action:
├─ Automatically logged with timestamp, TSE_ID, query type
├─ Filtered for compliance (data access attempts blocked before logging)
├─ Reviewed weekly by State DBA
└─ Spot-checked monthly by State Commissioner's audit team

Monthly Compliance Report:
├─ Total queries executed
├─ Data access attempts (should be zero)
├─ Escalations handled
├─ Approval compliance (% with required signatures)
├─ Response time metrics
└─ Incidents resolved / pending

Annual Security Audit:
├─ Full credential rotation verification
├─ Unauthorized access attempt detection
├─ Data disclosure risk assessment
└─ Training certification renewal
```

---

## 9. Organizational Placement & Reporting

### 9.1 Reporting Structure

```
┌──────────────────────────────────────┐
│   STATE COMMISSIONER                 │
│   (Top Authority)                    │
└─────────────┬────────────────────────┘
              │
┌─────────────▼────────────────────────┐
│   STATE DBA / IT DIRECTOR            │
│   (Direct supervisor for TSE)        │
└─────────────┬────────────────────────┘
              │
┌─────────────▼────────────────────────┐
│   TECHNICAL SUPPORT ENGINEER (TSE)   │
│   (Cross-organizational role)        │
│   • Supports all districts           │
│   • Escalates to State Commissioner  │
│   • Reports to State DBA daily       │
└──────────────────────────────────────┘
```

### 9.2 Coordination Channels

| Stakeholder | Purpose | Frequency | Method |
|---|---|---|---|
| **State DBA** | Daily stand-up, escalations | Daily | Slack/Email |
| **DSP (District)** | Issue notification, approval requests | As-needed | Email |
| **SHO (Station)** | User impact notification | As-needed | Email |
| **State Commissioner** | Critical escalations, monthly reports | As-needed + monthly | Email + meeting |
| **API Gateway Team** | Cache/performance coordination | Weekly | Slack |

---

## 10. Training & Certification Path

### 10.1 Required Certifications

| Certification | Provider | Validity | Renewal |
|---|---|---|---|
| **Database Administration Fundamentals** | Oracle/PostgreSQL Academy | 2 years | Annual refresher |
| **SQL Performance Tuning** | Vendor-specific | 2 years | Annual refresher |
| **Linux System Administration** | LPI or equivalent | 3 years | Every 3 years |
| **Security & Compliance for Police IT** | State Police Academy | 1 year | Annual renewal |
| **SURAKSHA System Architecture** | Internal | 6 months | Semi-annual |

### 10.2 Career Progression

```
Level 1: Junior Technical Support Engineer
├─ Supervised query execution
├─ Read-only schema inspection
├─ Error log analysis
└─ No independent escalations

Level 2: Senior Technical Support Engineer (After 1 year + certifications)
├─ Independent schema patches (with peer review)
├─ Performance optimization authority
├─ Incident response ownership
├─ DSP-level escalations

Level 3: Lead Technical Support Engineer / State DBA (After 3 years)
├─ Full technical authority
├─ Disaster recovery oversight
├─ Mentoring junior TSEs
├─ State Commissioner-level escalations
```

---

## 11. Appendices

### A. Schema-Only Reference (No Data)

**Core Tables (Structure Only — No Querying Against Data):**

```sql
-- Examples of schema inspection tools/concepts:
-- • Column names, data types, nullable flags
-- • Primary & foreign key relationships
-- • Index names and columns
-- • Trigger definitions
-- • Stored procedure signatures
-- • View definitions (structure only)
```

### B. Common Debug Queries (Safe Patterns)

```sql
-- Performance Analysis (Safe)
SELECT query, calls, total_time FROM pg_stat_statements 
  ORDER BY total_time DESC LIMIT 10;

-- Session Status (Safe)
SELECT pid, usename, wait_event_type FROM pg_stat_activity 
  WHERE state != 'idle';

-- Index Validation (Safe)
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
  FROM pg_stat_user_indexes ORDER BY idx_scan DESC;

-- Constraint Check (Safe)
SELECT table_name, constraint_name FROM information_schema.table_constraints
  WHERE constraint_type = 'FOREIGN KEY';
```

### C. Escalation Checklist

```
BEFORE ESCALATING TO DSP:

☐ Reproduced issue consistently
☐ Reviewed error logs for root cause
☐ Checked system resources (CPU, memory, disk)
☐ Verified no recent schema changes
☐ Confirmed not related to known issues
☐ Attempted standard troubleshooting steps
☐ Documented findings with timestamps
☐ Prepared proposed fix or workaround
☐ Assessed user impact & affected stations
☐ Scheduled follow-up testing

BEFORE ESCALATING TO STATE COMMISSIONER:

☐ DSP approval obtained
☐ Risk assessment completed
☐ Backup/rollback plan prepared
☐ Change control documentation ready
☐ All testing completed on staging
☐ Downtime window coordinated (if needed)
☐ User communication drafted
☐ Emergency contact list verified
```

### D. Incident Response Runbook

**Quick Reference for Common Issues:**

| Issue | Diagnostic | Quick Fix | Escalate If |
|---|---|---|---|
| Slow query | EXPLAIN ANALYZE | Add index / rewrite | Cannot identify cause |
| Hung session | Check pg_stat_activity | Kill session | Recurring pattern |
| Disk full | df -h / du -sh | Archive logs | Insufficient space after cleanup |
| Auth failure | Check auth logs | Restart service | >10 min outage |
| Cache hit rate drop | Check cache metrics | Invalidate & reload | Indicates memory issues |

---

## 12. Document Control

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-07-15 | Technical Authority | Initial version |
| | | | • Defined TSE role with cross-org authority |
| | | | • Specified data-free debug access |
| | | | • Established escalation protocols |

**Next Review Date:** 2026-10-15  
**Owner:** State DBA  
**Approver:** State Commissioner  

---

**END OF DOCUMENT**
