export type AuditLogEntry = {
  id: string;
  actorId: number | null;
  eventType: string;
  resource: string;
  ipAddress: string | null;
  userAgent: string | null;
  metadata: Record<string, unknown> | null;
  message: string | null;
  createdAt: Date;
};

export type AuditLogList = {
  total: number;
  limit: number;
  offset: number;
  logs: AuditLogEntry[];
};
