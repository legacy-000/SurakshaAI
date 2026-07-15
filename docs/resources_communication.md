# SURAKSHA Police FIR System — Resource Allocation, Permissions & Communication

**Document Version:** 1.0  
**Last Updated:** 2026-07-15  
**Audience:** System Architects, Backend Engineers, Security Officers, UI Designers

---

## 1. Organizational Hierarchy & Authority Structure

### 1.1 Hierarchical Authority Model

```
┌─────────────────────────────────────────────────────────────┐
│                    STATE LEVEL                              │
│  State Police Commissioner (Chief Administrator)            │
│  Manages: All districts, intelligence policy, resources     │
│  Controls: State-wide forecasts, alerts, offender pool      │
│  Communicates via: State Deputy Commander Node              │
└─────────────────────┬───────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┐
      │               │               │
┌─────▼──────┐ ┌──────▼──────┐ ┌──────▼──────┐
│  District 1│ │  District 2 │ │ District N  │
│    (DSP)   │ │    (DSP)    │ │   (DSP)     │
└─────┬──────┘ └──────┬──────┘ └──────┬──────┘
      │               │               │
      │     ┌─────────┼─────────┐     │
      │     │         │         │     │
┌─────▼──┐┌─▼──┐ ┌────▼──┐ ┌──▼──┐┌─▼──┐
│Station1││Stn2│ │Station3│ │Stn4 ││StnN│
│(SHO)  ││SHO ││ (SHO)  │ │(SHO)││SHO │
└─────┬──┘└──┬──┘ └───┬───┘ └──┬──┘└─┬──┘
      │      │       │        │     │
    ┌─┴──┬───┴─┐   ┌─┴───┬───┬┴──┬──┴──┐
    │    │     │   │     │   │   │     │
  ┌─▼─┐┌▼──┐ ┌▼─┐┌▼──┐ │  ┌▼─┐┌▼──┐
  │IO ││Cons│ │Const││ │  │IO││Cons│
  └───┘└────┘ └─────┘└────┘  └────┘└────┘
```

### 1.2 Role Definitions & Authority Scope

| Role | Rank | Post | Org Unit | Authority Scope | Data Scope | Resource Control |
|---|---|---|---|---|---|---|
| **State Commissioner** | Top | State HQ | State | All districts, policy | All cases, all data | Budget, enforcement policy, state-level resources |
| **DSP (Deputy Superintendent)** | High | District HQ | District | All stations in district | All cases in district | District budget, inter-station coordination, briefings |
| **SHO (Station House Officer)** | Mid-High | Police Station | Station | All cases in own station | All cases in own station | Station budget, staff, case allocation |
| **Sub-Inspector (IO)** | Mid | Police Station | Station | Assigned cases only | Assigned cases + visible cases | Investigation planning, evidence, evidence storage |
| **Constable** | Base | Police Station | Station | Assigned patrol areas | Own filings + assigned cases | Report filing, patrol logs |
| **Analyst** | Mid | District HQ | District | Intelligence analysis | Read-only: patterns, networks, forecasts | Analysis queries, report generation (read-only) |

### 1.3 Authority Tree: Decision Rights by Post

```
┌─ STATE COMMISSIONER ────────────────────────────────────┐
│ Can:                                                    │
│  ✓ Create/delete districts, units, stations             │
│  ✓ Approve DSP actions (policy decisions)               │
│  ✓ Access all cases, offender pool, alerts              │
│  ✓ Declare emergency (suspend normal data access)       │
│  ✓ Generate state-level briefings                       │
│  ✓ Audit trails, officer activity logs                  │
│  ✗ Approve chargesheet (DSP/SHO authority)              │
└────────────────────────────────────────────────────────┘
       ↓ Delegates to:
┌─ DSP (District) ────────────────────────────────────────┐
│ Can:                                                    │
│  ✓ Approve chargesheet (prosecutor role)                │
│  ✓ See all cases in own district                        │
│  ✓ Reassign investigations (IO reassignment)            │
│  ✓ Approve inter-station case hand-off                  │
│  ✓ Generate district briefings, forecasts, alerts       │
│  ✓ Offender pool management (priority ranking)          │
│  ✓ Create cross-station task forces                     │
│  ✗ Approve arrest (IO/SHO authority)                    │
│  ✗ Delete cases (audit trail prevents)                  │
└────────────────────────────────────────────────────────┘
       ↓ Delegates to:
┌─ SHO (Station House Officer) ──────────────────────────┐
│ Can:                                                    │
│  ✓ Approve chargesheet (initial review before DSP)      │
│  ✓ Reassign cases within own station                    │
│  ✓ Approve arrest (officer in custody authority)        │
│  ✓ Allocate cases to IOs                                │
│  ✓ Approve FIR registration (validation)                │
│  ✓ View all cases in own station                        │
│  ✗ Approve across stations (DSP authority)              │
│  ✗ Offender pool management (DSP authority)             │
└────────────────────────────────────────────────────────┘
       ↓ Delegates to:
┌─ Sub-Inspector (IO) ───────────────────────────────────┐
│ Can:                                                    │
│  ✓ Full investigation (evidence, arrests, witnesses)    │
│  ✓ Record arrests/surrenders in own cases               │
│  ✓ Draft chargesheet                                    │
│  ✓ Request case hand-off to another IO                  │
│  ✓ View linked cases (same accused, location, etc.)     │
│  ✓ Communicate with accused, witnesses, victims         │
│  ✗ Approve chargesheet (SHO/DSP authority)              │
│  ✗ Reassign own cases (SHO authority)                   │
│  ✗ Cross-station coordination (DSP/SHO authority)       │
└────────────────────────────────────────────────────────┘
       ↓ Delegates to:
┌─ Constable ────────────────────────────────────────────┐
│ Can:                                                    │
│  ✓ File initial complaint / FIR                         │
│  ✓ Record complainant details                           │
│  ✓ Record victim/accused basic info                     │
│  ✓ Submit for SHO approval (case registration)          │
│  ✗ Approve FIR registration (SHO authority)             │
│  ✗ Open investigation (IO authority)                    │
└────────────────────────────────────────────────────────┘
```

---

## 2. Permission Model & Access Control Framework

### 2.1 Permission Architecture (Fine-Grained)

Permissions are composed of:
- **Resource type** (Case, Offender, Message, Report, Alert, etc.)
- **Action** (Read, Create, Update, Delete, Approve, Forward)
- **Scope** (Own | Own Station | Own District | Own State | All)
- **Conditions** (Case status, offender priority, time-based, role-based)

### 2.2 Permission Matrix by Role & Resource

```
PERMISSION MATRIX:
================

Resource: CASE_MASTER (FIR Record)
┌──────────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ Action/Role      │ Constable  │ IO/Sub-Insp│ SHO        │ DSP        │ Commissioner│
├──────────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ Create (File)    │ ✓ Own Stn  │ ✓ Own Stn  │ ✓ Any      │ ✓ Any      │ ✓ Any       │
│ Read             │ ✓ Own Stn  │ ✓ Assigned │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Update           │ ✗          │ ✓ Assigned │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Delete           │ ✗          │ ✗          │ ✗          │ ✗          │ ✗ (audit)   │
│ Approve (FIR)    │ ✗          │ ✗          │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Reassign         │ ✗          │ ✗          │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Export/PDF       │ ✓ Own Stn  │ ✓ Assigned │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
└──────────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘

Resource: ARREST_SURRENDER (Arrest Record)
┌──────────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ Action/Role      │ Constable  │ IO/Sub-Insp│ SHO        │ DSP        │ Commissioner│
├──────────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ Create           │ ✗          │ ✓ Own Case │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Read             │ ✓ Own Stn  │ ✓ Assigned │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Update Bail      │ ✗          │ ✓ Own Case │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Update Custody   │ ✗          │ ✗          │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Record Escape    │ ✗          │ ✓ Own Case │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
└──────────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘

Resource: CHARGESHEET
┌──────────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ Action/Role      │ Constable  │ IO/Sub-Insp│ SHO        │ DSP        │ Commissioner│
├──────────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ Create (Draft)   │ ✗          │ ✓ Own Case │ ✗          │ ✗          │ ✗          │
│ Read             │ ✓ Own Stn  │ ✓ Assigned │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Update (Draft)   │ ✗          │ ✓ Own Case │ ✗          │ ✗          │ ✗          │
│ Approve/Submit   │ ✗          │ ✗          │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Final Approval   │ ✗          │ ✗          │ ✓ (initial)│ ✓ Final    │ ✓ Final     │
│ Reject           │ ✗          │ ✗          │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
└──────────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘

Resource: OFFENDER_POOL (Offender Dossier)
┌──────────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ Action/Role      │ Constable  │ IO/Sub-Insp│ SHO        │ DSP        │ Commissioner│
├──────────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ Read             │ ✓ Same Stn │ ✓ District │ ✓ District │ ✓ District │ ✓ All       │
│ Add note         │ ✗          │ ✓ Own Case │ ✓ Own Stn  │ ✓ Dist     │ ✓ All       │
│ Update priority  │ ✗          │ ✗          │ ✗          │ ✓ Dist     │ ✓ All       │
│ Flag for alert   │ ✗          │ ✗          │ ✗          │ ✓ Dist     │ ✓ All       │
└──────────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘

Resource: MESSAGES & COMMUNICATION
┌──────────────────┬────────────┬────────────┬────────────┬────────────┬────────────┐
│ Action/Role      │ Constable  │ IO/Sub-Insp│ SHO        │ DSP        │ Commissioner│
├──────────────────┼────────────┼────────────┼────────────┼────────────┼────────────┤
│ Send (up)        │ ✓ To SHO   │ ✓ To SHO   │ ✓ To DSP   │ ✓ To State │ ✗          │
│ Send (lateral)   │ ✗          │ ✓ To IO    │ ✓ To SHO   │ ✓ To DSP   │ ✗          │
│ Send (down)      │ ✗          │ ✗          │ ✓ To IO    │ ✓ To SHO   │ ✓ To DSP    │
│ Read (inbox)     │ ✓          │ ✓          │ ✓          │ ✓          │ ✓          │
│ Forward          │ ✗          │ ✓ (copy SHO)│ ✓ (copy DSP) │ ✓ (copy State) │ ✗ │
│ Broadcast        │ ✗          │ ✗          │ ✓ Station  │ ✓ District │ ✓ State     │
└──────────────────┴────────────┴────────────┴────────────┴────────────┴────────────┘
```

### 2.3 Row-Level Security (RLS) - Data Visibility Rules

**Rule Engine:** Permissions checked at query-time and render-time.

#### 2.3.1 Case Visibility Rules

```sql
-- Pseudocode for RLS on CaseMaster
SELECT * FROM CaseMaster c
WHERE (
    -- Case filed at officer's own station
    c.PoliceStationID = @CurrentOfficerUnitID
    
    -- OR case assigned to officer for investigation
    OR EXISTS (
        SELECT 1 FROM Investigation inv
        WHERE inv.CaseMasterID = c.CaseMasterID
        AND inv.AssignedToIOID = @CurrentOfficerID
    )
    
    -- OR officer is SHO of case's station
    OR EXISTS (
        SELECT 1 FROM Employee e
        WHERE e.EmployeeID = @CurrentOfficerID
        AND e.DesignationID = @SHODesignationID
        AND e.UnitID = c.PoliceStationID
    )
    
    -- OR officer is DSP of case's district (read-only)
    OR EXISTS (
        SELECT 1 FROM Employee e
        INNER JOIN Unit u ON e.UnitID = u.UnitID
        INNER JOIN District d ON u.DistrictID = d.DistrictID
        INNER JOIN CaseMaster c2 ON c2.PoliceStationID = u.UnitID
        WHERE e.EmployeeID = @CurrentOfficerID
        AND e.RankID = @DSPRankID
        AND c2.CaseMasterID = c.CaseMasterID
    )
    
    -- OR officer is State Commissioner
    OR @CurrentOfficerRankID = @CommissionerRankID
)
AND (
    -- Hide minors' names/details (PII masking)
    CASE 
        WHEN c.VictimAge < 18 THEN @CurrentOfficerRolePermissions & PERM_VIEW_MINOR_DATA
        ELSE 1
    END = 1
)
AND c.IsDeleted = 0
```

#### 2.3.2 Column-Level Masking (PII Protection)

| Table | Column | Constable | IO | SHO | DSP | State |
|---|---|---|---|---|---|---|
| Victim | VictimName (if age < 18) | ✗ Masked | ✗ Masked | ✓ Show | ✓ Show | ✓ Show |
| Victim | VictimName (if age ≥ 18) | ✓ Show | ✓ Show | ✓ Show | ✓ Show | ✓ Show |
| ComplainantDetails | Contact (phone/email) | ✓ Show | ✓ Show | ✓ Show | ✗ Masked | ✗ Masked |
| Employee | KGID (gov ID) | ✗ Hidden | ✗ Hidden | ✓ Show | ✓ Show | ✓ Show |
| ArrestSurrender | CustodyDetails | ✓ Show | ✓ Show | ✓ Show | ✓ Show | ✓ Show |

### 2.4 Action-Level Permissions (Workflow Gates)

Each action has a gate that checks:

```typescript
interface PermissionGate {
  resource: "CASE" | "ARREST" | "CHARGESHEET" | "MESSAGE" | "REPORT";
  action: "CREATE" | "READ" | "UPDATE" | "APPROVE" | "FORWARD" | "DELETE";
  subject: User; // officer making request
  object: Case | Arrest | Chargesheet; // resource being accessed
  conditions: {
    resourceStatus?: string; // case status (filed, under investigation, chargesheeted)
    ownershipMatch?: boolean; // does subject own or investigate this?
    hierarchyCheck?: boolean; // is subject in higher authority chain?
    timeConstraint?: { validAfter?: Date; validBefore?: Date }; // time-gated actions
    emergencyMode?: boolean; // suspend normal rules in emergency
  };
}

// Example: Can IO approve chargesheet?
canApprove(chargesheet) {
  return (
    this.role === "IO" && 
    this.casesInvestigating.includes(chargesheet.caseId) &&
    chargesheet.status === "DRAFT" &&
    false // IO cannot approve; only draft
  );
}

// Example: Can SHO approve chargesheet?
canApprove(chargesheet) {
  return (
    this.role === "SHO" &&
    this.station.cases.includes(chargesheet.caseId) &&
    chargesheet.status === "DRAFT_PENDING_SHO_REVIEW" &&
    true // SHO can approve chargesheet
  );
}
```

---

## 3. Resource Allocation & Sharing Model

### 3.1 Resource Types & Ownership

| Resource | Owner | Share Scope | Modify Scope | Delete Allowed |
|---|---|---|---|---|
| **Case (CaseMaster)** | SHO (station) | District (via DSP) | SHO + DSP | ✗ (audit trail) |
| **Investigation** | Assigned IO | Station + IO | IO + SHO | ✗ (audit trail) |
| **Arrest** | IO (investigator) | Station + District | IO + SHO + DSP | ✗ (audit trail) |
| **Chargesheet** | IO (drafter) | Station + District + State | IO (draft) + SHO (review) + DSP (final) | ✗ (immutable) |
| **Message** | Sender | Recipients + CC + Broadcast scope | Sender (before send) | ✓ (after 24h, audit logged) |
| **Report** | Generator | Distribution list | Generator + Approver | ✓ (versioned) |
| **Alert** | DSP/Commander | District + relevant stations | DSP + State | ✗ (audit trail) |
| **Offender Dossier** | Analyst | District + officers | Analyst + DSP | ✗ (historical) |

### 3.2 Resource Lifecycle & Handoff Workflow

#### 3.2.1 Case Lifecycle with Resource Transfer

```
Constable files FIR
     ↓
SHO approves & registers (CaseMaster created)
     ↓
SHO assigns to IO (Investigation created, ownership transferred)
     ↓
IO investigates (Investigation record locked to IO, Arrest/Evidence owned by IO)
     ↓
IO requests hand-off OR SHO reassigns (notify other IO, prior IO can view history)
     ↓
New IO continues investigation (both have read access, only new IO can modify)
     ↓
IO drafts chargesheet (ChargesheetDetails owned by IO, status = DRAFT_PENDING_SHO_REVIEW)
     ↓
SHO reviews & approves (Chargesheet status = APPROVED_BY_SHO, forwarded to DSP)
     ↓
DSP final review (status = APPROVED_BY_DSP)
     ↓
Case ready for court (status = READY_FOR_PROSECUTION, all data frozen)
```

#### 3.2.2 Investigation Hand-off (Inter-Station Transfer)

**Scenario:** Case needs to be transferred from Station A (IO1) to Station B (IO2)

**Workflow:**

```
Step 1: IO1 requests hand-off
├─ Via message to SHO1: "Request case hand-off to IO2, Station B"
├─ Reason field (optional): "IO2 has expertise in this crime type"
├─ Attachment: current investigation summary
└─ Status: PENDING_SHO_APPROVAL

Step 2: SHO1 approves + forwards to DSP
├─ SHO1 reviews hand-off request
├─ Via message to DSP: "Approve hand-off of Case [ID] to IO2, Station B"
├─ DSP checks: both stations in same district? Yes
├─ DSP approves cross-station hand-off
└─ Status: APPROVED_BY_DSP

Step 3: SHO2 receives notification + confirms receipt
├─ System notification: "Case [ID] handed off to your station, assign to IO"
├─ SHO2 reviews case summary
├─ SHO2 assigns to IO2 via message
└─ Status: ASSIGNED_TO_IO2

Step 4: IO1 → IO2 ownership transfer
├─ All prior Investigation records visible to IO1 (read-only)
├─ New Investigation record created for IO2 (modifiable)
├─ Arrest/Evidence records ownership transferred to IO2
├─ IO1 remains as "prior investigator" (audit trail)
└─ Status: OWNERSHIP_TRANSFERRED

Step 5: Audit trail captures
├─ Who: IO1, SHO1, DSP, SHO2, IO2
├─ What: Case [ID], hand-off reason, approval chain
├─ When: timestamps for each step
├─ Why: context from messages
└─ Stored: AuditLog table, linked to Investigation record
```

### 3.3 Resource Sharing Matrix (Who Can Access What)

```
STATION A (SHO_A, IO_1, IO_2, Constables_A)
├─ Cases filed at Station A → visible to all A officers, DSP (read-only)
├─ Cases assigned to IO_1 → modifiable by IO_1, SHO_A, DSP (read-only)
├─ Cases assigned to IO_2 → modifiable by IO_2, SHO_A, DSP (read-only)

STATION B (SHO_B, IO_3, Constables_B)
├─ Cases filed at Station B → visible to all B officers, DSP (read-only)

DSP DISTRICT LEVEL
├─ All cases from Station A, B, C, ... in district
├─ Can reassign between stations
├─ Can override SHO approval (escalation)
├─ Can see offender pool (all arrested in district)
├─ Can see all messages in district
├─ Can generate district-wide briefings

STATE LEVEL (Commissioner)
├─ All cases from all districts
├─ Can override DSP decisions
├─ Can create cross-district task forces
├─ Can manage state-level offender pool
```

---

## 4. Message Passing & Communication Protocol

### 4.1 Message Architecture

#### 4.1.1 Message Types

```typescript
enum MessageType {
  // Operational messages
  CASE_ASSIGNMENT = "CASE_ASSIGNMENT",           // SHO → IO: "Investigate case X"
  HAND_OFF_REQUEST = "HAND_OFF_REQUEST",         // IO → SHO: "Transfer case to IO2"
  APPROVAL_REQUEST = "APPROVAL_REQUEST",         // IO → SHO: "Review chargesheet"
  STATUS_UPDATE = "STATUS_UPDATE",               // IO → SHO: "Arrest made"
  
  // Administrative messages
  RESOURCE_REQUEST = "RESOURCE_REQUEST",         // IO → SHO: "Need forensics"
  COORDINATION_REQUEST = "COORDINATION_REQUEST", // SHO → DSP: "Inter-station help"
  ALERT_ESCALATION = "ALERT_ESCALATION",         // DSP → State: "Critical offender"
  
  // Intelligence sharing
  PATTERN_ALERT = "PATTERN_ALERT",               // DSP → Stations: "Robbery pattern detected"
  OFFENDER_ALERT = "OFFENDER_ALERT",             // Analyst → DSP: "Offender spotted in district"
  
  // Broadcast
  POLICY_UPDATE = "POLICY_UPDATE",               // Commissioner → All: "New procedure"
  EMERGENCY_BROADCAST = "EMERGENCY_BROADCAST",   // DSP → All: "Lockdown"
}

interface Message {
  messageId: UUID;
  type: MessageType;
  sender: {
    employeeId: int;
    rank: string; // "Constable" | "IO" | "SHO" | "DSP" | "Commissioner"
    unit: {
      unitId: int;
      unitName: string; // "Bengaluru South Police Station"
    };
  };
  recipients: {
    to: Employee[]; // Direct recipients
    cc: Employee[]; // Copied (read but not actionable)
    bcc?: Employee[]; // Hidden from others
  };
  subject: string;
  body: string; // Rich text (Kannada + English supported)
  linkedResources: {
    resourceType: "CASE" | "ARREST" | "CHARGESHEET" | "OFFENDER";
    resourceId: int;
  }[];
  
  attachments: {
    fileId: UUID;
    fileName: string;
    mimeType: string;
    sizeBytes: int;
  }[];
  
  metadata: {
    priority: "LOW" | "NORMAL" | "HIGH" | "CRITICAL";
    dueDate?: Date;
    tags: string[]; // ["urgent", "coordination", "inter-station"]
  };
  
  status: "DRAFT" | "SENT" | "DELIVERED" | "READ" | "ACKNOWLEDGED" | "ACTED_UPON";
  timestampCreated: DateTime;
  timestampSent: DateTime;
  timestampRead?: DateTime;
  timestampAcknowledged?: DateTime;
  
  workflowState?: {
    requiresApproval: boolean;
    approvalDeadline?: DateTime;
    approvalStatus: "PENDING" | "APPROVED" | "REJECTED";
    approvalBy?: Employee;
  };
  
  auditTrail: {
    action: string;
    actor: Employee;
    timestamp: DateTime;
  }[];
}
```

#### 4.1.2 Message Routing Rules

```
Routing Logic:
==============

IF message.type === CASE_ASSIGNMENT THEN
  sender = SHO
  recipients.to = [Target IO]
  recipients.cc = [Message sender's station team]
  linkedResources = [CaseMaster]
  requiresApproval = false (SHO decision is final)
  workflowState.requiresApproval = false

IF message.type === HAND_OFF_REQUEST THEN
  sender = IO
  recipients.to = [Sender's SHO]
  recipients.cc = [Assigned IO (if known)]
  linkedResources = [Investigation]
  requiresApproval = true (SHO must approve)
  workflowState.approvalDeadline = now() + 48 hours
  
  ON APPROVED BY SHO:
    ├─ Forward to target SHO (or DSP if cross-district)
    ├─ Create notification for target IO
    ├─ Lock current Investigation (read-only for IO)
    └─ Create new Investigation for target IO

IF message.type === APPROVAL_REQUEST THEN
  sender = IO
  recipients.to = [SHO]
  cc = [DSP (if chargesheet ready for final approval)]
  linkedResources = [ChargesheetDetails]
  requiresApproval = true
  workflowState.approvalDeadline = now() + 7 days
  
  ON APPROVED BY SHO:
    ├─ Chargesheet status = APPROVED_BY_SHO
    ├─ Auto-forward to DSP with summary
    └─ DSP receives approval notification

IF message.type === STATUS_UPDATE THEN
  sender = IO | SHO
  recipients.to = [SHO] (if from IO) | [DSP] (if from SHO)
  linkedResources = [CaseMaster, ArrestSurrender]
  requiresApproval = false (informational)
  auto-update = true (updates case record)

IF message.type === PATTERN_ALERT THEN
  sender = DSP | Analyst
  recipients.to = [All SHOs in district]
  recipients.cc = [Relevant IOs (flagged for crime category)]
  broadcast = true (all-hands alert)
  priority = HIGH | CRITICAL
  workflowState.requiresApproval = false
  
  Auto-create Alert record + log to AlertLog

IF message.type === EMERGENCY_BROADCAST THEN
  sender = Commissioner | DSP
  recipients.to = [All officers in district/state]
  broadcast = true
  priority = CRITICAL
  Suspend normal permission rules (emergency mode ON)
  
  ON RECEIVED: All officers must acknowledge within 1 hour
```

### 4.2 Message Delivery Guarantees

```
Delivery Model:
===============

SYNCHRONOUS (Blocking):
├─ Used for: Approval requests, critical alerts
├─ Behavior: Message sent, system waits for ACK, return status
├─ Timeout: 30 seconds (async fallback if timeout)
└─ Guarantee: At-least-once delivery

ASYNCHRONOUS (Non-blocking):
├─ Used for: Status updates, informational messages, broadcasts
├─ Behavior: Message queued, sender proceeds, async delivery
├─ Queue: Catalyst Job Scheduling
├─ Retry: 3 attempts with exponential backoff (1s, 10s, 60s)
└─ Guarantee: At-least-once delivery (eventually consistent)

BROADCAST:
├─ Used for: Policy updates, emergency alerts, pattern alerts
├─ Behavior: Message sent to all recipients in group simultaneously
├─ Method: Fan-out async delivery to all recipients
├─ Acknowledgment: Each recipient ACKs independently
└─ Guarantee: Eventually all will receive (resilient to partial failures)
```

### 4.3 Message Priority & Escalation

```
Priority Escalation Chain:
==========================

NORMAL (Green ✓)
├─ Typical case updates, routine messages
├─ Response deadline: 24-48 hours
├─ Auto-escalate: After 72 hours (unread)

HIGH (Yellow ⚠️)
├─ Approval requests, resource needs, inter-station coordination
├─ Response deadline: 4-8 hours
├─ Auto-escalate: After 24 hours (unread) → CC to DSP

CRITICAL (Red 🔴)
├─ Officer safety alerts, active fugitive, emergency coordination
├─ Response deadline: < 1 hour
├─ Auto-escalate: After 30 min (unread) → Escalate to DSP + State
├─ Auto-action: System sends SMS + call to recipient's phone

Message auto-escalation:
├─ Message created with HIGH priority
├─ No read after 4 hours → system sends SMS reminder
├─ No acknowledgment after 8 hours → message auto-CC to DSP
├─ If DSP doesn't respond after 24 hours → escalate to Commissioner
```

### 4.4 Message Conversation Threading

**Messages are threaded by linked resource.**

```
Example: Chargesheet approval workflow

Thread: [Case 104430006202600001 → Chargesheet Approval]

Message 1 (IO to SHO):
├─ Subject: "Chargesheet ready for review - Case 104...001"
├─ Body: "Attached chargesheet for robbery case..."
├─ LinkedResource: ChargesheetDetails ID 1234
├─ Attachment: chargesheet_draft.pdf
├─ Timestamp: 2026-07-10 15:30
└─ Status: DELIVERED

  Reply 1 (SHO to IO):
  ├─ Subject: "RE: Chargesheet ready for review - Case 104...001"
  ├─ Body: "Missing evidence documentation for item 5. Please add photos."
  ├─ LinkedResource: [same ChargesheetDetails]
  ├─ Timestamp: 2026-07-10 16:45
  ├─ Status: DELIVERED
  └─ Action: REQUEST_REVISION
  
    Reply 1.1 (IO to SHO):
    ├─ Subject: "RE: Chargesheet ready for review - Case 104...001"
    ├─ Body: "Updated chargesheet attached with evidence photos."
    ├─ Attachment: chargesheet_revised.pdf
    ├─ Timestamp: 2026-07-11 09:00
    └─ Status: DELIVERED
    
      Reply 2 (SHO to IO):
      ├─ Subject: "RE: Chargesheet ready for review - Case 104...001"
      ├─ Body: "Approved. Forwarding to DSP for final review."
      ├─ LinkedResource: [same ChargesheetDetails]
      ├─ Timestamp: 2026-07-11 10:15
      └─ Action: APPROVED
      └─ Auto-forward: Message sent to DSP
```

---

## 5. Access Management & Group Creation

### 5.1 Organizational Groups (Static)

These are **created by System Admin** and managed centrally.

```sql
-- OrgGroup (Organizational structure)
CREATE TABLE OrgGroup (
  groupId INT PRIMARY KEY,
  groupName VARCHAR(255), -- "Bengaluru South Police Station"
  groupType ENUM('STATION', 'DISTRICT', 'REGION', 'STATE'),
  parentGroupId INT, -- Hierarchical parent
  
  authority_level INT, -- 1=State, 2=District, 3=Station, 4=Sub-unit
  geo_area GEOMETRY, -- Geographic boundary (GIS polygon)
  
  createdBy INT (FK Employee),
  createdDate DATETIME,
  active BIT,
);

-- GroupMembership (Officers assigned to group)
CREATE TABLE GroupMembership (
  membershipId INT PRIMARY KEY,
  groupId INT (FK OrgGroup),
  employeeId INT (FK Employee),
  memberRole ENUM('ADMIN', 'MEMBER'), -- ADMIN=SHO, MEMBER=IO/Constable
  
  joinDate DATETIME,
  endDate DATETIME (NULL if active),
  active BIT,
  
  -- Permissions within group (overrides role-based defaults)
  customPermissions JSON,
);

Example OrgGroup Hierarchy:
STATE_KARNATAKA
├─ BENGALURU_DISTRICT
│  ├─ BENGALURU_SOUTH_STATION
│  │  ├─ SHO: Employee_001
│  │  ├─ IO: Employee_002, Employee_003
│  │  └─ Constables: Employee_004, Employee_005
│  ├─ BENGALURU_NORTH_STATION
│  │  ├─ SHO: Employee_006
│  │  └─ IOs: Employee_007
│  └─ BENGALURU_EAST_STATION
│     └─ ...
└─ KOLAR_DISTRICT
   └─ ...
```

### 5.2 Dynamic Access Groups (Temporary)

**Created for specific investigations or task forces.**

```sql
CREATE TABLE DynamicAccessGroup (
  groupId INT PRIMARY KEY,
  groupName VARCHAR(255), -- "Bangalore Rape Series Task Force"
  groupType ENUM('TASK_FORCE', 'INVESTIGATION', 'OPERATION'),
  
  linkedResources: {
    cases: [CaseMasterID, CaseMasterID, ...],
    offenders: [AccusedMasterID, ...],
    geographic_zone: GEOMETRY,
  },
  
  memberships: [
    {
      employeeId: INT,
      role: "LEAD" | "MEMBER",
      permissions: {canModify: bool, canApprove: bool, ...}
    }
  ],
  
  createdBy: INT (FK Employee),
  createdDate: DATETIME,
  dissolveDate: DATETIME (auto-dissolve after completion),
  active: BIT,
);

Example: Cross-Station Task Force
GROUP: "Jewelry Robbery Series - Jul 2026"
├─ Lead: DSP_Bengaluru (DSP)
├─ Members:
│  ├─ SHO_South (Station South)
│  ├─ IO_001 (Station South)
│  ├─ SHO_East (Station East)
│  ├─ IO_007 (Station East)
│  └─ Analyst_01 (District HQ)
├─ Linked cases: [Case_1001, Case_1002, Case_1003, Case_1004]
├─ Offenders: [Accused_A1, Accused_A2]
├─ Permissions:
│  ├─ Lead can: create new cases in task force, reassign IOs, approve chargesheet
│  ├─ Members can: view all linked cases, add evidence, coordinate
│  └─ Analyst can: read-only analysis of all linked data
└─ Auto-dissolve: 2026-09-15 (90 days after task force creation)
```

### 5.3 Permission Inheritance & Delegation

```
Permission Inheritance Chain:
=============================

DEFAULT ROLE PERMISSIONS (from Employee.RankID + DesignationID)
├─ Applied at login
├─ From RolePermissions lookup table
└─ Example: IO role → can create investigation, record arrest

+ OrgGroup MEMBERSHIP
├─ Officer assigned to Station A
├─ OrgGroup permissions override/augment role permissions
├─ Example: Station A has custom rule "IO cannot approve chargesheet"

+ DYNAMIC ACCESS GROUP
├─ Officer added to Task Force X
├─ Task Force permissions further override
├─ Example: Task Force X grants temporary "cross-station case approval"

= EFFECTIVE PERMISSIONS (at request time)
├─ Computed at every API call
├─ Cached for 5 minutes (expires on member/group change)
└─ Audit logged: "Computed effective permissions for officer_123"

DELEGATION (temporary elevation):
├─ SHO_A delegates authority to IO_1: "Approve chargesheet while I'm on leave"
├─ System creates TemporaryPermission record:
│  ├─ grantor: SHO_A
│  ├─ grantee: IO_1
│  ├─ permission: "APPROVE_CHARGESHEET"
│  ├─ scope: "Station A cases only"
│  ├─ validFrom: 2026-07-15
│  ├─ validUntil: 2026-07-22 (end of SHO's leave)
│  └─ audit: logged + require explanation
├─ IO_1 gains temporary permission (checked in effective permissions)
├─ After validUntil, permission expires + audit logged
└─ System sends reminder: "SHO's delegation expires in 2 days"
```

---

## 6. Inter-Station & Inter-District Communication

### 6.1 Inter-Station Coordination (Lateral Communication)

**Same district, different stations.**

```
Scenario: Robbery suspect from Station A fled to Station B

Step 1: IO_A detects suspect might be in Station B jurisdiction
├─ Searches case database for geographic matches
├─ Offender network shows suspect has relatives at Station B location
└─ Triggers: Cross-station coordination workflow

Step 2: IO_A sends message to SHO_A
├─ Type: COORDINATION_REQUEST
├─ Subject: "Suspect likely in Station B - request coordination"
├─ Body: Details + suspect photo + known associates
├─ LinkedResources: [Case_A001, Accused_X]
└─ Status: PENDING_SHO_APPROVAL

Step 3: SHO_A approves + forwards to DSP
├─ SHO_A reviews IO's request
├─ Sends message to DSP (district-level authority)
├─ Message type: COORDINATION_REQUEST (SHO → DSP)
├─ DSP sees: cross-station request, validates within same district
└─ DSP approves forwarding to Station B

Step 4: DSP forwards to SHO_B
├─ Message sent to SHO_B
├─ Type: CROSS_STATION_COORDINATION
├─ Body: "Suspect from your area, Station A IO seeking help"
├─ Includes: case summary, suspect details, investigator contact
└─ Requires acknowledgment from SHO_B

Step 5: SHO_B assigns IO_B
├─ SHO_B assigns IO_B to assist
├─ Message to IO_B: "Assist Station A IO in locating suspect"
├─ System creates shared Investigation (visibility only, modification by IO_A)
└─ Both IO_A and IO_B can see case, but modification rules apply

Step 6: Collaboration
├─ IO_A has read access to IO_B's findings
├─ IO_B can comment on case (message thread)
├─ DSP monitors coordination (oversight)
├─ Data flows: suspects → locations → evidence
└─ Audit trail: who saw what, when, why
```

### 6.2 Inter-District Coordination (Hierarchical Communication)

**Different districts, requires DSP coordination.**

```
Scenario: Organized crime gang operates across Bengaluru + Kolar districts

Step 1: DSP_Bengaluru detects pattern
├─ Network Intelligence Agent flags criminal network spanning districts
├─ Multiple related FIRs in Bengaluru + Kolar
└─ Recommendation: Create cross-district task force

Step 2: DSP_Bengaluru initiates coordination
├─ Creates message to DSP_Kolar
├─ Type: CROSS_DISTRICT_COORDINATION
├─ Subject: "Organized crime network - Bengaluru + Kolar"
├─ Body: Pattern analysis, case summaries, offender dossiers
├─ LinkedResources: [Cases from both districts]
└─ Requires approval from both DSPs

Step 3: DSP_Kolar reviews + accepts
├─ DSP_Kolar reads case details
├─ Consults with SHOs in Kolar
├─ Responds: "Accept coordination, assign IO_8 + IO_9 from our district"
└─ Message status: APPROVED

Step 4: Create cross-district task force (DynamicAccessGroup)
├─ Task force name: "Organized Crime Task Force - Bengaluru Kolar Jul2026"
├─ Members:
│  ├─ Lead: DSP_Bengaluru (coordinating DSP)
│  ├─ Co-lead: DSP_Kolar
│  ├─ From Bengaluru: SHO_South, IO_1, IO_2
│  ├─ From Kolar: SHO_Kolar, IO_8, IO_9
│  └─ State analyst (optional)
├─ Permissions override:
│  ├─ All members can view cases from both districts (normally restricted)
│  ├─ IOs can comment/update across stations (normally restricted to own)
│  ├─ DSP_Bengaluru + DSP_Kolar share approval authority
│  └─ State Commissioner can monitor + override
└─ Duration: 90 days auto-dissolve

Step 5: Ongoing collaboration
├─ Shared investigation workspace (web panel)
├─ Message thread for task force (broadcast to all members)
├─ Unified offender dossier (compiled from both districts)
├─ Linked case view (all cases in task force)
├─ Regular briefings (shared insights, evidence)
└─ Audit: Every action logged with officer, timestamp, district context
```

### 6.3 State-Level Escalation

```
When does escalation to State Commissioner occur?

CONDITION 1: VIP case (celebrity, politician, police officer victim)
├─ Auto-flagged by system (lookup against VIP registry)
├─ Message sent to State Commissioner
├─ Commissioner gains read access (can override at any time)
└─ Investigation status visible in State dashboard

CONDITION 2: Critical alert (officer death, mass casualty, fugitive)
├─ Alert Intelligence Agent triggers CRITICAL alert
├─ Message auto-escalates to DSP + State Commissioner
├─ Emergency broadcast to all officers in affected districts
├─ State may declare emergency mode (suspend normal permissions)
└─ Coordination initiated at State level

CONDITION 3: Sensitive investigation (inter-district gang, terrorism)
├─ DSP recognizes need for state coordination
├─ Escalates to State Commissioner via formal message
├─ Commissioner may:
│  ├─ Assign state-level task force leader
│  ├─ Provide specialized resources (forensics, cyber team)
│  ├─ Coordinate with neighboring districts
│  └─ Notify federal agencies if needed

CONDITION 4: Chargesheet for serious crime (heinous offence)
├─ DSP final approval for chargesheet
├─ System auto-sends copy to State Commissioner
├─ Commissioner can review (oversight function)
├─ If rejected by Commissioner → case goes back to DSP
```

---

## 7. UI Implementation Details

### 7.1 Message Inbox & Communication Panel

**Location:** Left sidebar + modal panel (can be expanded)

#### 7.1.1 Inbox View

```
┌─────────────────────────────────────────┐
│  MESSAGES & COMMUNICATION               │ [Settings ⚙️]
├─────────────────────────────────────────┤
│ Filter by:  [All ▼] [Unread] [Urgent]  │
│ Sort by:    [Date ▼] [Priority ▼]      │
├─────────────────────────────────────────┤
│ 🟴 CRITICAL (3)                         │
│ ├─ 🔴 [10:30] Officer needs backup      │
│ │  Sender: DSP_Bengaluru                │
│ │  Preview: "Officer A attacked during..."
│ │  [ACK] [ACTION]                       │
│ │                                        │
│ ├─ 🔴 [09:45] Fugitive alert            │
│ │  Sender: DSP_Kolar                    │
│ │  Preview: "Offender X spotted in..."  │
│ │  [ACK] [ACTION]                       │
│ │                                        │
│ └─ 🔴 [08:15] Emergency broadcast       │
│    Sender: Commissioner                 │
│    Preview: "Lockdown declared in..."   │
│    [ACK]                                │
│                                          │
│ 🟡 HIGH (7)                             │
│ ├─ 🟠 [15:22] Case assignment           │
│ │  Sender: SHO_South                    │
│ │  Preview: "Investigate robbery case.."│
│ │  Response deadline: 2026-07-17        │
│ │  [ACCEPT] [DECLINE]                   │
│ │                                        │
│ ├─ 🟠 [14:55] Chargesheet review        │
│ │  Sender: IO_001 @ Station South       │
│ │  Preview: "Chargesheet ready, 2 files"│
│ │  Response deadline: 2026-07-18        │
│ │  [REVIEW] [REPLY]                     │
│ │                                        │
│ └─ 🟠 [13:30] Inter-station coordination│
│    Sender: SHO_East                     │
│    Preview: "Suspect fled to your area" │
│    Response deadline: 2026-07-17        │
│    [REVIEW] [REPLY]                     │
│                                          │
│ 🟢 NORMAL (12)                          │
│ ├─ 🟢 [11:00] Arrest update             │
│ │  Sender: IO_002 @ Station South       │
│ │  Preview: "Arrest completed for case" │
│ │  [READ]                               │
│ │                                        │
│ └─ 🟢 [Show 11 more...]                 │
│                                          │
└─────────────────────────────────────────┘
```

#### 7.1.2 Message Detail Panel (Expanded)

```
┌──────────────────────────────────────────────────────────┐
│ Message Details                                  [Close X] │
├──────────────────────────────────────────────────────────┤
│                                                           │
│ 🟠 HIGH PRIORITY                                          │
│ Subject: Chargesheet ready for review - Case 104...001   │
│                                                           │
│ From: IO_001 (Sub-Inspector) @ Bengaluru South Station   │
│ To:   SHO_South (Station House Officer)                  │
│ CC:   DSP_Bengaluru                                      │
│ Date: 2026-07-10 15:30 | Read: 2026-07-10 16:45         │
│ Linked: CaseMaster ID 104430006202600001 [VIEW]          │
│         ChargesheetDetails ID 1234 [VIEW]                │
│                                                           │
│ ─────────────────────────────────────────────────────────│
│                                                           │
│ Subject: Chargesheet ready for review - Case 104...001   │
│                                                           │
│ Body:                                                    │
│ ───────                                                  │
│ Dear SHO,                                                │
│                                                           │
│ I have completed the investigation into the robbery      │
│ case 104430006202600001. The chargesheet is attached     │
│ with all evidence documented.                            │
│                                                           │
│ Case Summary:                                            │
│ - Crime: Robbery (IPC 392, 397)                         │
│ - Suspect: Accused_X (arrested 2026-07-05)              │
│ - Evidence: 4 items documented, photos attached          │
│ - Witness statements: 3 witness testimonies             │
│                                                           │
│ Chargesheet status: DRAFT (requires your review)        │
│ Please review and provide feedback.                      │
│                                                           │
│ Regards,                                                 │
│ IO_001                                                   │
│                                                           │
│ ─────────────────────────────────────────────────────────│
│ Attachments:                                             │
│ ├─ chargesheet_draft.pdf (245 KB) [DOWNLOAD]            │
│ ├─ evidence_photos.zip (1.2 MB) [DOWNLOAD]              │
│ └─ witness_statements.docx (82 KB) [DOWNLOAD]           │
│                                                           │
│ ─────────────────────────────────────────────────────────│
│ Action Required:                                         │
│                                                           │
│ Response deadline: 2026-07-18 15:30 (8 days)            │
│                                                           │
│ [APPROVE] [REQUEST REVISION] [REJECT]                   │
│                                                           │
│ If requesting revision:                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Reason for revision (optional):                    │ │
│ │ ┌──────────────────────────────────────────────┐  │ │
│ │ │ [Text field...]                              │  │ │
│ │ └──────────────────────────────────────────────┘  │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ ─────────────────────────────────────────────────────────│
│ CONVERSATION HISTORY:                                    │
│                                                           │
│ Reply 1 - SHO_South (2026-07-10 16:45):                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ "Missing evidence documentation for item 5.         │ │
│ │  Please add photos."                                │ │
│ │                                                     │ │
│ │ [Status: REQUEST REVISION]                          │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ Reply 1.1 - IO_001 (2026-07-11 09:00):                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ "Updated chargesheet attached with evidence photos" │ │
│ │                                                     │ │
│ │ Attachment: chargesheet_revised.pdf (250 KB)       │ │
│ │ [Status: REVISION SUBMITTED]                       │ │
│ └─────────────────────────────────────────────────────┘ │
│                                                           │
│ ─────────────────────────────────────────────────────────│
│ [REPLY] [FORWARD] [ARCHIVE] [DELETE (after 24h)]        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### 7.2 Permissions & Access Control Panel

**Location:** Settings > Permissions (for admins) / My Access (for officers)

#### 7.2.1 Officer's "My Access" View

```
┌────────────────────────────────────────────────────────┐
│ MY ACCESS & PERMISSIONS                                │
├────────────────────────────────────────────────────────┤
│                                                         │
│ YOUR PROFILE:                                           │
│ ├─ Name: Officer_001                                   │
│ ├─ Rank: Sub-Inspector                                 │
│ ├─ Designation: Investigating Officer                  │
│ ├─ Station: Bengaluru South Police Station             │
│ ├─ District: Bengaluru                                 │
│ └─ Joined: 2024-01-15                                  │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ YOUR DEFAULT PERMISSIONS (Role-based):                 │
│                                                         │
│ Data Scope:
│ ├─ ✓ View cases in my station                          │
│ ├─ ✓ View cases assigned to me                         │
│ ├─ ✗ View cases in other stations                      │
│ └─ ✗ View offender pool (district-level)               │
│                                                         │
│ Case Actions:
│ ├─ ✓ Create investigations (for assigned cases)        │
│ ├─ ✓ Record arrests                                    │
│ ├─ ✓ Collect evidence                                  │
│ ├─ ✓ Draft chargesheet                                 │
│ ├─ ✗ Approve chargesheet (SHO only)                    │
│ └─ ✗ Reassign cases (SHO only)                         │
│                                                         │
│ Communication:
│ ├─ ✓ Send messages to my SHO                           │
│ ├─ ✓ Send messages to other IOs in my station          │
│ ├─ ✗ Send messages to DSP (via SHO)                    │
│ └─ ✓ Receive messages from any officer                 │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ TEMPORARY PERMISSION OVERRIDES:                        │
│                                                         │
│ 1. [Temporary] Approve Chargesheet (Delegation)        │
│    ├─ Granted by: SHO_South (2026-07-10)               │
│    ├─ Valid from: 2026-07-15                           │
│    ├─ Valid until: 2026-07-22 (SHO's leave)            │
│    ├─ Scope: Bengaluru South Station cases only        │
│    ├─ Status: ACTIVE ✓                                 │
│    └─ [REVOKE] [VIEW DETAILS]                          │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ ACTIVE GROUP MEMBERSHIPS:                              │
│                                                         │
│ 1. Bengaluru South Police Station (Primary)            │
│    ├─ Role in group: MEMBER                            │
│    ├─ Group permissions: (inherits from OrgGroup)      │
│    └─ Status: ACTIVE                                   │
│                                                         │
│ 2. Jewelry Robbery Series Task Force (Temporary)       │
│    ├─ Role in group: MEMBER                            │
│    ├─ Added: 2026-07-05                                │
│    ├─ Temporary permissions:                           │
│    │  ├─ ✓ View all task force cases (cross-station)   │
│    │  ├─ ✓ Modify task force cases                     │
│    │  └─ ✓ Communicate with task force members         │
│    ├─ Group dissolves: 2026-10-05 (3 months)           │
│    ├─ Status: ACTIVE ✓                                 │
│    └─ [LEAVE GROUP]                                    │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ [PRINT ACCESS SUMMARY] [AUDIT LOG]                     │
│                                                         │
└────────────────────────────────────────────────────────┘
```

#### 7.2.2 Admin Permission Management Panel

**Location:** Settings > Permission Management (SHO/DSP only)

```
┌────────────────────────────────────────────────────────┐
│ PERMISSION MANAGEMENT                                  │
│ (SHO / DSP view)                                       │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Filter by:  [Role ▼] [Station ▼] [Status ▼]           │
│ Search:     [Officer name...]                          │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ OFFICERS IN MY STATION:                                │
│                                                         │
│ Name           Rank      Permissions      Actions       │
│ ────────────────────────────────────────────────────────│
│ Officer_001    IO        Standard (view) [CUSTOMIZE]   │
│ Officer_002    IO        Standard (view) [CUSTOMIZE]   │
│ Officer_003    Const     Standard (view) [CUSTOMIZE]   │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ TEMPORARY OVERRIDES (Delegations):                     │
│                                                         │
│ Officer_001 - "Approve Chargesheet" (while on leave)   │
│ ├─ Valid: 2026-07-15 to 2026-07-22                    │
│ ├─ Scope: Station cases only                           │
│ ├─ Status: ACTIVE ✓                                   │
│ └─ [REVOKE] [EXTEND UNTIL...] [VIEW AUDIT]            │
│                                                         │
│ Officer_002 - "View DSP briefings" (task force)        │
│ ├─ Valid: 2026-07-05 to 2026-10-05                    │
│ ├─ Scope: Task Force X cases                          │
│ ├─ Status: ACTIVE ✓                                   │
│ └─ [REVOKE] [EXTEND UNTIL...] [VIEW AUDIT]            │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ GRANT NEW TEMPORARY PERMISSION:                        │
│                                                         │
│ Grant to:     [Officer_001 ▼]                         │
│ Permission:   [Approve Chargesheet ▼]                 │
│ Scope:        [Own station cases ▼]                   │
│ Valid from:   [Date picker] [Time picker]             │
│ Valid until:  [Date picker] [Time picker]             │
│ Reason:       [Text field - optional]                 │
│                                                         │
│ [GRANT] [PREVIEW]                                      │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ GROUP MANAGEMENT:                                      │
│                                                         │
│ [CREATE NEW GROUP] [MANAGE GROUPS]                     │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### 7.3 Inter-Station Communication UI

**Location:** Dashboard > Communication > Inter-Station Coordination

```
┌────────────────────────────────────────────────────────┐
│ INTER-STATION COORDINATION                             │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Active Coordination Requests:                          │
│                                                         │
│ [HIGH] Suspect location - Station East coordination    │
│ ├─ From: IO_001 @ Bengaluru South                      │
│ ├─ Request date: 2026-07-10 14:30                      │
│ ├─ Status: APPROVED_BY_DSP (forwarded to Station East)│
│ ├─ Assigned to: SHO_East (acknowledged)               │
│ ├─ Linked case: Case 104430006202600001               │
│ ├─ Suspect details: [VIEW]                             │
│ ├─ Status updates: [2 updates]                         │
│ │  1. SHO_South approved request                       │
│ │  2. DSP forwarded to Station East                    │
│ └─ [VIEW FULL THREAD] [ADD UPDATE]                     │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ [NORMAL] Forensics resource request - Station North    │
│ ├─ From: SHO_South                                     │
│ ├─ Request: Need forensics team for 3 cases            │
│ ├─ Request date: 2026-07-09 10:00                      │
│ ├─ Status: PENDING_DSP_APPROVAL                        │
│ ├─ Response deadline: 2026-07-11 (2 days remaining)    │
│ └─ [VIEW] [FOLLOW UP]                                  │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ CREATE NEW COORDINATION REQUEST:                       │
│                                                         │
│ Request type:     [Suspect location ▼]                │
│ To station:       [Bengaluru North ▼]                 │
│ Priority:         [HIGH ▼]                             │
│ Subject:          [Text field...]                      │
│ Details:          [Rich text field...]                 │
│ Linked case:      [Case search...]                     │
│ Suspect/details:  [Dropdown...]                        │
│ Required response: [Date/time picker]                 │
│                                                         │
│ [SEND TO MY SHO] [PREVIEW]                             │
│                                                         │
└────────────────────────────────────────────────────────┘
```

### 7.4 Task Force & Group Management UI

**Location:** Dashboard > Administration > Groups & Task Forces

```
┌────────────────────────────────────────────────────────┐
│ TASK FORCE & GROUP MANAGEMENT                          │
│ (DSP / Admin view)                                     │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Filter by: [Type ▼] [Status ▼] [District ▼]           │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ ACTIVE TASK FORCES:                                    │
│                                                         │
│ 1. Jewelry Robbery Series - Jul 2026                   │
│    ├─ Type: INVESTIGATION                              │
│    ├─ Created: 2026-07-05                              │
│    ├─ Lead: DSP_Bengaluru                              │
│    ├─ Members: 7 (2 SHOs, 3 IOs, 1 Analyst, 1 DSP)    │
│    ├─ Linked cases: 4 FIRs                             │
│    ├─ Linked offenders: 2 accused                      │
│    ├─ Dissolution date: 2026-10-05 (90 days)           │
│    ├─ Status: ACTIVE ✓                                │
│    ├─ Recent activity: [2026-07-11 update by IO_001]   │
│    └─ [VIEW] [EDIT MEMBERS] [ADD CASES] [DISSOLVE]    │
│                                                         │
│ 2. Organized Crime Network - Bengaluru & Kolar         │
│    ├─ Type: CROSS_DISTRICT_OPERATION                   │
│    ├─ Created: 2026-06-15                              │
│    ├─ Lead: DSP_Bengaluru (Co-lead: DSP_Kolar)         │
│    ├─ Members: 12 (multi-district)                     │
│    ├─ Linked cases: 8 FIRs                             │
│    ├─ Linked offenders: 6 accused                      │
│    ├─ Dissolution date: 2026-12-15 (6 months)          │
│    ├─ Status: ACTIVE ✓                                │
│    └─ [VIEW] [EDIT] [COMMUNICATE]                      │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ CREATE NEW TASK FORCE:                                 │
│                                                         │
│ Name:        [Text field...]                           │
│ Type:        [INVESTIGATION ▼]                         │
│ Lead DSP:    [DSP_Bengaluru ▼]                         │
│ Districts:   [Select...] ☑ Bengaluru ☑ Kolar          │
│ Duration:    [Date picker] to [Date picker]            │
│ Initial cases: [Case search + multi-select]            │
│ Members:     [Officer search + multi-select]           │
│ Custom perms: [Permission builder]                     │
│                                                         │
│ [CREATE] [PREVIEW]                                     │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ View task force details:                               │
│ Jewelry Robbery Series - Jul 2026                      │
│                                                         │
│ Members:                                               │
│ ├─ DSP_Bengaluru (Lead) - read all, approve all        │
│ ├─ SHO_South (Member) - read all, modify own station   │
│ ├─ SHO_East (Member) - read all, modify own station    │
│ ├─ IO_001 @ South (Member) - read all, modify          │
│ ├─ IO_002 @ South (Member) - read all, modify          │
│ ├─ IO_7 @ East (Member) - read all, modify             │
│ └─ Analyst_01 (Member) - read-only, generate reports   │
│                                                         │
│ Linked cases:  [4 cases] [+ADD] [-REMOVE]              │
│ Linked offenders: [2 accused] [+ADD] [-REMOVE]         │
│ Geographic zone: [MAP VIEW]                            │
│ Messages: [12 in thread] [VIEW THREAD]                 │
│                                                         │
│ Audit log: [VIEW AUDIT]                                │
│                                                         │
│ [EDIT] [ADD MEMBER] [REMOVE MEMBER] [DISSOLVE]         │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 8. Audit Trail & Compliance

### 8.1 Audit Log Schema

```sql
CREATE TABLE AuditLog (
  auditId BIGINT PRIMARY KEY AUTO_INCREMENT,
  
  -- Actor
  actorEmployeeId INT (FK Employee),
  actorRank VARCHAR(50), -- snapshot of rank at time of action
  actorUnit INT (FK Unit), -- snapshot of unit at time of action
  
  -- Action
  action VARCHAR(100), -- "READ_CASE", "APPROVE_CHARGESHEET", "SEND_MESSAGE"
  resourceType VARCHAR(50), -- "CASE", "CHARGESHEET", "MESSAGE"
  resourceId INT,
  
  -- Context
  requestPath VARCHAR(255), -- API endpoint or UI action
  ipAddress VARCHAR(45), -- IPv4/IPv6
  userAgent VARCHAR(500), -- Browser info
  
  -- Result
  actionStatus VARCHAR(50), -- "SUCCESS", "PERMISSION_DENIED", "RESOURCE_NOT_FOUND"
  errorMessage VARCHAR(1000), -- if failed
  
  -- Metadata
  beforeState JSON, -- object state before action (if update)
  afterState JSON, -- object state after action (if update)
  duration_ms INT, -- request processing time
  
  -- Timestamp
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
  
  -- Search optimization
  yearMonth INT, -- 202607 for July 2026 (partitioned by this)
);

CREATE INDEX idx_actor_timestamp ON AuditLog(actorEmployeeId, timestamp);
CREATE INDEX idx_resource_timestamp ON AuditLog(resourceType, resourceId, timestamp);
```

### 8.2 Audit Queries (Examples)

```sql
-- Who accessed case X in last 30 days?
SELECT DISTINCT
  actorEmployeeId, a.actorRank, e.FirstName, e.EmployeeID,
  COUNT(*) as access_count,
  MIN(timestamp) as first_access,
  MAX(timestamp) as last_access
FROM AuditLog a
JOIN Employee e ON a.actorEmployeeId = e.EmployeeID
WHERE resourceType = 'CASE' AND resourceId = 104430006202600001
  AND timestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY actorEmployeeId
ORDER BY last_access DESC;

-- What permissions was officer X granted/revoked?
SELECT
  timestamp,
  action, -- "GRANT_TEMPORARY_PERMISSION", "REVOKE_TEMPORARY_PERMISSION"
  beforeState->'$.permission' as permission,
  beforeState->'$.validUntil' as expiration,
  actorEmployeeId as granted_by
FROM AuditLog
WHERE resourceType = 'TEMPORARY_PERMISSION'
  AND resourceId = @TargetOfficerEmployeeId
ORDER BY timestamp DESC;

-- Compliance: Did chargesheet approval follow hierarchy?
SELECT
  a.timestamp,
  a.actorRank,
  a.action, -- "APPROVE_CHARGESHEET"
  a.resourceId as chargesheet_id,
  CASE
    WHEN a.actorRank = 'Sub-Inspector' THEN 'VIOLATION: IO cannot approve'
    WHEN a.actorRank = 'Station House Officer' THEN 'OK: SHO can approve'
    WHEN a.actorRank = 'Deputy Superintendent' THEN 'OK: DSP can approve'
    ELSE 'CHECK'
  END as compliance_status
FROM AuditLog a
WHERE a.action = 'APPROVE_CHARGESHEET'
  AND a.timestamp >= DATE_SUB(NOW(), INTERVAL 90 DAY)
ORDER BY a.timestamp DESC;
```

### 8.3 Audit Trail UI (Officer View)

```
┌────────────────────────────────────────────────────────┐
│ MY AUDIT LOG                                           │
│ (View your own access history)                         │
├────────────────────────────────────────────────────────┤
│                                                         │
│ Filter by: [Date range] [Action type] [Resource type] │
│ Search:    [Search audit entries...]                   │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ Recent Activity (last 30 days):                        │
│                                                         │
│ 2026-07-11 10:15 | READ | Case 104430006202600001     │
│ └─ From: 10.0.0.42 (Chrome 91.0)                       │
│    Duration: 145ms | Status: SUCCESS ✓                 │
│                                                         │
│ 2026-07-11 10:10 | UPDATE | Investigation_1001        │
│ └─ From: 10.0.0.42 (Chrome 91.0)                       │
│    Changed: Investigation notes (added 3 paragraphs)   │
│    Duration: 234ms | Status: SUCCESS ✓                 │
│    [VIEW CHANGES]                                      │
│                                                         │
│ 2026-07-11 09:45 | READ | ChargesheetDetails_1234     │
│ └─ From: 10.0.0.42 (Chrome 91.0)                       │
│    Duration: 89ms | Status: SUCCESS ✓                  │
│                                                         │
│ 2026-07-10 16:50 | SEND_MESSAGE | Message_5678        │
│ └─ From: 10.0.0.42 (Chrome 91.0)                       │
│    Recipients: SHO_South, DSP_Bengaluru               │
│    Duration: 156ms | Status: SUCCESS ✓                 │
│                                                         │
│ 2026-07-10 15:30 | CREATE | ChargesheetDetails_1234   │
│ └─ From: 10.0.0.42 (Chrome 91.0)                       │
│    Duration: 412ms | Status: SUCCESS ✓                 │
│    [VIEW INITIAL STATE]                                │
│                                                         │
│ ─────────────────────────────────────────────────────────│
│ [EXPORT AUDIT LOG] [PRINT]                             │
│                                                         │
└────────────────────────────────────────────────────────┘
```

---

## 9. Technical API Contracts

### 9.1 Permission Check Endpoint

```typescript
// POST /api/v1/permissions/check
interface PermissionCheckRequest {
  subject: {
    employeeId: int;
  };
  resource: {
    type: "CASE" | "ARREST" | "CHARGESHEET" | "MESSAGE" | "REPORT";
    id: int;
  };
  action: "CREATE" | "READ" | "UPDATE" | "DELETE" | "APPROVE" | "FORWARD";
  context?: {
    emergencyMode?: boolean;
    temporaryOverride?: string; // UUID of temporary permission
  };
}

interface PermissionCheckResponse {
  allowed: boolean;
  reason: string; // e.g., "Officer lacks DSP rank", "Resource in different district"
  
  permissions: {
    action: string;
    allowed: boolean;
    requiredConditions?: {
      rankRequired?: string;
      scopeRequired?: "OWN_STATION" | "OWN_DISTRICT" | "ALL";
      resourceStatusRequired?: string;
    };
    denialReason?: string;
  }[];
  
  auditLog: {
    checkId: UUID;
    timestamp: DateTime;
    actor: int; // who checked permissions
    result: "ALLOWED" | "DENIED";
  };
}

// Example: Can IO_001 approve chargesheet?
POST /api/v1/permissions/check
{
  "subject": { "employeeId": 1001 },
  "resource": { "type": "CHARGESHEET", "id": 1234 },
  "action": "APPROVE"
}

Response:
{
  "allowed": false,
  "reason": "Only SHO or higher rank can approve chargesheet",
  "permissions": [
    {
      "action": "APPROVE",
      "allowed": false,
      "requiredConditions": {
        "rankRequired": "SHO or DSP or Commissioner"
      },
      "denialReason": "Officer is IO; does not have required rank"
    }
  ],
  "auditLog": { ... }
}
```

### 9.2 Message Send Endpoint

```typescript
// POST /api/v1/messages/send
interface MessageSendRequest {
  type: MessageType;
  recipients: {
    to: int[]; // Employee IDs
    cc?: int[];
    bcc?: int[];
  };
  subject: string;
  body: string;
  linkedResources?: {
    resourceType: string;
    resourceId: int;
  }[];
  attachments?: UUID[]; // Pre-uploaded file UUIDs
  
  metadata: {
    priority: "LOW" | "NORMAL" | "HIGH" | "CRITICAL";
    dueDate?: Date;
  };
  
  workflowState?: {
    requiresApproval: boolean;
    approvalDeadline?: DateTime;
  };
}

interface MessageSendResponse {
  messageId: UUID;
  status: "SENT" | "QUEUED" | "FAILED";
  recipients: {
    employeeId: int;
    status: "SENT" | "QUEUED" | "PERMISSION_DENIED" | "INVALID_RECIPIENT";
    deliveredAt?: DateTime;
  }[];
  timestamp: DateTime;
  auditLog: { checkId: UUID };
}

// Example: SHO sends case assignment to IO
POST /api/v1/messages/send
{
  "type": "CASE_ASSIGNMENT",
  "recipients": {
    "to": [1001], // IO_001
    "cc": [5001]  // Station team
  },
  "subject": "Investigate Case 104430006202600001",
  "body": "Case assigned for investigation. See details below...",
  "linkedResources": [
    { "resourceType": "CASE", "resourceId": 10001 }
  ],
  "metadata": {
    "priority": "NORMAL",
    "dueDate": "2026-07-18"
  },
  "workflowState": {
    "requiresApproval": false
  }
}

Response:
{
  "messageId": "msg-abc-123-def",
  "status": "SENT",
  "recipients": [
    {
      "employeeId": 1001,
      "status": "SENT",
      "deliveredAt": "2026-07-11T10:15:00Z"
    },
    {
      "employeeId": 5001,
      "status": "SENT",
      "deliveredAt": "2026-07-11T10:15:00Z"
    }
  ]
}
```

### 9.3 Group Membership Endpoint

```typescript
// POST /api/v1/groups/{groupId}/members/add
interface GroupAddMemberRequest {
  employeeId: int;
  memberRole: "ADMIN" | "MEMBER";
  customPermissions?: {
    canModify?: boolean;
    canApprove?: boolean;
    dataScope?: "OWN_STATION" | "OWN_DISTRICT" | "ALL";
  };
}

interface GroupAddMemberResponse {
  membershipId: int;
  groupId: int;
  employeeId: int;
  joinDate: DateTime;
  status: "ACTIVE";
  permissions: {
    inherited: string[]; // from role
    custom: string[]; // from customPermissions
  };
  auditLog: { ... };
}

// Example: Add IO_001 to Task Force "Jewelry Robbery Series"
POST /api/v1/groups/task-force-123/members/add
{
  "employeeId": 1001,
  "memberRole": "MEMBER",
  "customPermissions": {
    "canModify": true,
    "canApprove": false,
    "dataScope": "ALL" // can see cases from all stations in task force
  }
}

Response:
{
  "membershipId": 9001,
  "groupId": "task-force-123",
  "employeeId": 1001,
  "joinDate": "2026-07-11T10:30:00Z",
  "status": "ACTIVE",
  "permissions": {
    "inherited": ["READ_CASE", "UPDATE_INVESTIGATION"],
    "custom": ["READ_CROSS_STATION_CASE", "MODIFY_CROSS_STATION_CASE"]
  }
}
```

---

## 10. Security Considerations

### 10.1 Permission Enforcement Points

```
Enforcement occurs at THREE LAYERS:

LAYER 1: API Gateway
├─ Authenticate request (Catalyst auth token)
├─ Extract officer identity + rank
├─ Route to appropriate backend function
└─ Reject unauthenticated requests

LAYER 2: Backend Function (Resource Access)
├─ Check permissions (call /permissions/check)
├─ Filter database query by RLS rules
├─ Mask sensitive columns (PII) before return
├─ Apply row-level security at SQL level
└─ Reject unauthorized access + log

LAYER 3: UI Rendering
├─ Hide buttons/fields if officer lacks permission
├─ Disable form submission if check fails
├─ Show "Access Denied" message with reason
└─ Client-side check (for UX, not security)

PRINCIPLE: Never trust client. Always re-check server-side.
```

### 10.2 Information Disclosure Prevention

```
PII Masking Rules:
═════════════════

Rule 1: Minors' identities
├─ If victim.age < 18 AND officer.rank < DSP
├─ Mask: victim.name → "[Minor, Age X]"
├─ Mask: victim.contact → "[Redacted]"
└─ Log access attempt

Rule 2: Contact information
├─ If officer.district != complainant.district
├─ Mask: complainant.phone → "[Redacted]"
├─ Mask: complainant.email → "[Redacted]"
└─ Exception: SHO/DSP/State can always see

Rule 3: Arrest details
├─ If officer.rank < SHO AND arrest.status = "IN_CUSTODY"
├─ Mask: detention_location → "[Secure location]"
├─ Mask: custody_notes → "[Redacted for security]"
└─ Full access for SHO/DSP/State
```

### 10.3 Message Encryption & Signing

```
Messages in transit:
├─ TLS 1.3 (HTTPS)
├─ 256-bit encryption

Messages at rest:
├─ AES-256-GCM encryption (in Data Store)
├─ Encryption keys managed by Catalyst
├─ Decrypted only when officer with permission accesses

Message signing:
├─ Each message digitally signed by sender
├─ Signature verified on delivery
├─ Prevents tampering / spoofing
├─ Audit log includes signature verification status

Approval workflows:
├─ Chargesheet approval signed by SHO
├─ Signature includes timestamp + officer ID
├─ Non-repudiation: officer cannot deny approval
├─ Audit trail: all signatures + verification results
```

---

## 11. Emergency Mode & Override Procedures

### 11.1 Emergency Declaration

```
Emergency Trigger: Commissioner declares emergency
├─ Reason: Officer death, mass casualty, fugitive, terrorism

Emergency Response:
├─ Permission rules SUSPENDED (all officers can see all cases)
├─ Communication fast-tracked (no approval gates)
├─ Data access fully opened (no masking)
├─ Emergency alerts broadcast to all officers
├─ Audit trail marked "EMERGENCY MODE" (all access logged with flags)

Duration:
├─ Manual end by Commissioner
├─ Auto-expire after 72 hours (must explicitly renew)

Coming out of emergency:
├─ Permissions restored to normal
├─ Audit log review: who accessed what in emergency (compliance)
├─ Report generated: emergency actions taken
```

---

## 12. Glossary & Key Concepts

| Term | Definition |
|---|---|
| **RLS (Row-Level Security)** | Database enforces which rows a user can see/modify based on permissions |
| **PII (Personally Identifiable Info)** | Sensitive data (names, contacts, addresses) requiring masking based on role |
| **OrgGroup** | Permanent organizational structure (Station, District, State) |
| **DynamicAccessGroup** | Temporary group for specific task force or investigation |
| **Permission Gate** | Logic that checks if an action is allowed before execution |
| **Audit Trail** | Immutable log of all actions (who, what, when, why, result) |
| **Delegation** | Temporary permission elevation (e.g., SHO delegates chargesheet approval to IO) |
| **Hand-off** | Transfer of case investigation from one IO to another |
| **Cross-Station Coordination** | Collaboration between officers from different stations in same district |
| **Cross-District Coordination** | Collaboration between officers from different districts (requires DSP approval) |

---

**Document Complete.**

**Next Steps:**
1. Implement permission check endpoint in backend (Catalyst function)
2. Set up audit logging infrastructure (Data Store tables)
3. Build message queue + delivery system (Catalyst Job Scheduling)
4. Create UI panels for inbox, permissions, group management
5. Conduct security review with compliance officer
6. User acceptance testing with police stakeholders (SHO, DSP, IO)

