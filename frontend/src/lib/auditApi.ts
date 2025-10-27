import { httpClient } from "./httpClient";
import type { AuditLogEntry, AuditLogList } from "../types/audit";

type RawAuditLogEntry = {
  id: string;
  actor_id: number | null;
  event_type: string;
  resource: string;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown> | null;
  message: string | null;
  created_at: string;
};

type RawAuditLogResponse = {
  total: number;
  limit: number;
  offset: number;
  logs: RawAuditLogEntry[];
};

export type ListAuditLogsOptions = {
  limit?: number;
  offset?: number;
  eventType?: string | null;
  resource?: string | null;
  actorId?: number | null;
};

const parseDate = (value: string): Date => {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? new Date(0) : parsed;
};

const mapEntry = (payload: RawAuditLogEntry): AuditLogEntry => ({
  id: payload.id,
  actorId: payload.actor_id,
  eventType: payload.event_type,
  resource: payload.resource,
  ipAddress: payload.ip_address,
  userAgent: payload.user_agent,
  metadata: payload.metadata,
  message: payload.message,
  createdAt: parseDate(payload.created_at),
});

export const listAuditLogs = async (options: ListAuditLogsOptions = {}): Promise<AuditLogList> => {
  const params: Record<string, unknown> = {
    limit: options.limit ?? 50,
    offset: options.offset ?? 0,
  };

  if (options.eventType) {
    params.event_type = options.eventType;
  }
  if (options.resource) {
    params.resource = options.resource;
  }
  if (typeof options.actorId === "number") {
    params.actor_id = options.actorId;
  }

  const response = await httpClient.get<RawAuditLogResponse>("/api/v1/audit/logs", { params });

  return {
    total: response.data.total,
    limit: response.data.limit,
    offset: response.data.offset,
    logs: response.data.logs.map(mapEntry),
  };
};
