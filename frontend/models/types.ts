// SURAKSHA AI - Global TypeScript Types

export interface User {
  id: number;
  username: string;
  email: string;
  fullName?: string;
  role: "admin" | "investigator" | "officer";
  badgeNumber?: string;
  isActive: boolean;
  createdAt: string;
}

export interface Case {
  id: number;
  firNumber: string;
  title: string;
  description?: string;
  status: "Open" | "Investigating" | "Closed" | "ChargeSheeted";
  crimeType: string;
  locationName?: string;
  occurrenceDate: string;
  createdAt: string;
}

export interface Accused {
  id: number;
  fullName: string;
  aliases?: string;
  gender?: string;
  age?: number;
  address?: string;
  phoneNumber?: string;
  previousConvictions?: string;
  status: "Suspect" | "Apprehended" | "Absconding" | "Released";
}

export interface Victim {
  id: number;
  fullName: string;
  gender?: string;
  age?: number;
  contactNumber?: string;
  address?: string;
  statementSummary?: string;
}

export interface Officer {
  id: number;
  badgeNumber: string;
  name: string;
  rank: string;
  postingStation: string;
  contactNumber?: string;
}

export interface CrimePattern {
  id: number;
  patternName: string;
  description?: string;
  crimeType: string;
  hotspotRadiusMeters: number;
  temporalSignature?: string;
  modusOperandiTags?: string;
}

export interface Alert {
  id: number;
  title: string;
  message: string;
  severity: "Low" | "Medium" | "High" | "Critical";
  alertType: string;
  isRead: boolean;
  resolved: boolean;
  createdAt: string;
}

export interface Prediction {
  id: number;
  targetArea: string;
  crimeType: string;
  probability: number;
  forecastWindowStart: string;
  forecastWindowEnd: string;
  contributingFactors?: string;
}

export interface ChatContext {
  id: number;
  sessionId: string;
  userId: number;
  historyJson?: string;
  metadataJson?: string;
}

export interface Investigation {
  id: number;
  caseId: number;
  assignedOfficerId: number;
  summary?: string;
  leadsDetails?: string;
  status: string;
}

export interface BehaviorProfile {
  id: number;
  accusedId: number;
  riskScore: number;
  behavioralTraits?: string;
  propensityTags?: string;
}

export interface TimelineEvent {
  id: number;
  caseId: number;
  eventTitle: string;
  description?: string;
  eventTimestamp: string;
  eventType?: string;
}
