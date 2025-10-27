import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { Modal } from "../../components/ui/Modal";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Spinner } from "../../components/ui/Spinner";
import { useTheme } from "../../components/ThemeProvider";
import { listAuditLogs } from "../../lib/auditApi";
import type { AuditLogEntry } from "../../types/audit";

type FilterFormState = {
  eventType: string;
  actorId: string;
  startDate: string;
  endDate: string;
};

type AppliedFilters = FilterFormState;

const DEFAULT_FILTERS: FilterFormState = {
  eventType: "",
  actorId: "",
  startDate: "",
  endDate: "",
};

const parseDateFilter = (value: string, endOfDay = false): Date | null => {
  if (!value) {
    return null;
  }

  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) {
    return null;
  }

  const date = new Date(
    year,
    month - 1,
    day,
    endOfDay ? 23 : 0,
    endOfDay ? 59 : 0,
    endOfDay ? 59 : 0,
    endOfDay ? 999 : 0
  );
  return Number.isNaN(date.getTime()) ? null : date;
};

const formatDateTime = (value: Date): string => {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(value);
};

export const AuditLogPage = () => {
  const theme = useTheme();
  const [filters, setFilters] = useState<FilterFormState>(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<AppliedFilters>(DEFAULT_FILTERS);
  const [entries, setEntries] = useState<AuditLogEntry[]>([]);
  const [totalEntries, setTotalEntries] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null);

  const loadLogs = useCallback(async (activeFilters: AppliedFilters) => {
    setIsLoading(true);
    setError(null);

    try {
      const actorIdNumber = activeFilters.actorId.trim() ? Number(activeFilters.actorId.trim()) : null;
      const parsedActorId = actorIdNumber !== null && !Number.isNaN(actorIdNumber) ? actorIdNumber : null;

      const response = await listAuditLogs({
        limit: 100,
        eventType: activeFilters.eventType.trim() || null,
        actorId: parsedActorId,
      });

      const startBoundary = parseDateFilter(activeFilters.startDate);
      const endBoundary = parseDateFilter(activeFilters.endDate, true);

      const filteredEntries = response.logs.filter((entry) => {
        const timestamp = entry.createdAt.getTime();
        if (startBoundary && timestamp < startBoundary.getTime()) {
          return false;
        }
        if (endBoundary && timestamp > endBoundary.getTime()) {
          return false;
        }
        return true;
      });

      setEntries(filteredEntries);
      setTotalEntries(response.total);
    } catch (loadError) {
      const message = loadError instanceof Error ? loadError.message : "Failed to load audit logs.";
      setError(message);
      setEntries([]);
      setTotalEntries(0);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadLogs(appliedFilters);
  }, [loadLogs, appliedFilters]);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setAppliedFilters(filters);
  };

  const resetFilters = () => {
    setFilters(DEFAULT_FILTERS);
    setAppliedFilters(DEFAULT_FILTERS);
  };

  const activeFilterChips = useMemo(() => {
    const chips: string[] = [];
    if (appliedFilters.eventType.trim()) {
      chips.push(`Action: ${appliedFilters.eventType.trim()}`);
    }
    if (appliedFilters.actorId.trim()) {
      chips.push(`User ID: ${appliedFilters.actorId.trim()}`);
    }
    if (appliedFilters.startDate || appliedFilters.endDate) {
      const start = appliedFilters.startDate || "any";
      const end = appliedFilters.endDate || "any";
      chips.push(`Date range: ${start} → ${end}`);
    }
    return chips;
  }, [appliedFilters]);

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <header style={{ display: "grid", gap: theme.spacing.xs }}>
        <h2 style={{ margin: 0 }}>Audit log</h2>
        <p style={{ margin: 0, color: theme.colors.muted }}>
          Review security-relevant actions recorded across the platform. Filter by action type, user, and date to
          focus on specific events.
        </p>
      </header>

      <Card title="Filters">
        <form
          onSubmit={handleSubmit}
          style={{
            display: "grid",
            gap: theme.spacing.md,
          }}
        >
          <div
            style={{
              display: "grid",
              gap: theme.spacing.md,
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            }}
          >
            <Input
              label="Action type"
              placeholder="e.g. pdf.signature.applied"
              value={filters.eventType}
              onChange={(event) => setFilters((previous) => ({ ...previous, eventType: event.target.value }))}
            />
            <Input
              label="User ID"
              type="number"
              min="0"
              value={filters.actorId}
              onChange={(event) => setFilters((previous) => ({ ...previous, actorId: event.target.value }))}
            />
            <Input
              label="Start date"
              type="date"
              value={filters.startDate}
              onChange={(event) => setFilters((previous) => ({ ...previous, startDate: event.target.value }))}
            />
            <Input
              label="End date"
              type="date"
              value={filters.endDate}
              onChange={(event) => setFilters((previous) => ({ ...previous, endDate: event.target.value }))}
            />
          </div>

          <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap" }}>
            <Button type="submit" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Spinner size={18} /> Applying…
                </>
              ) : (
                "Apply filters"
              )}
            </Button>
            <Button type="button" variant="secondary" onClick={resetFilters} disabled={isLoading}>
              Reset
            </Button>
          </div>

          {activeFilterChips.length ? (
            <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap" }}>
              {activeFilterChips.map((chip) => (
                <span
                  key={chip}
                  style={{
                    padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                    borderRadius: theme.borderRadius,
                    background: "rgba(37, 99, 235, 0.08)",
                    fontSize: theme.font.size.xs,
                  }}
                >
                  {chip}
                </span>
              ))}
            </div>
          ) : null}
        </form>
      </Card>

      {error ? <span style={{ color: theme.colors.danger }}>{error}</span> : null}

      <Card
        title="Recent activity"
        action={
          <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
            Showing {entries.length} of {totalEntries} entries
          </span>
        }
      >
        {isLoading ? (
          <div style={{ display: "grid", placeItems: "center", padding: theme.spacing.xl }}>
            <Spinner />
          </div>
        ) : entries.length === 0 ? (
          <span style={{ color: theme.colors.muted }}>No audit entries match the selected filters.</span>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table
              style={{
                width: "100%",
                borderCollapse: "collapse",
                fontSize: theme.font.size.sm,
              }}
            >
              <thead>
                <tr style={{ textAlign: "left", borderBottom: `1px solid rgba(148, 163, 184, 0.4)` }}>
                  <th style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>Timestamp</th>
                  <th style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>Action</th>
                  <th style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>Resource</th>
                  <th style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>User</th>
                  <th style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>IP address</th>
                  <th style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>Details</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((entry) => (
                  <tr key={entry.id} style={{ borderBottom: `1px solid rgba(148, 163, 184, 0.2)` }}>
                    <td style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>{formatDateTime(entry.createdAt)}</td>
                    <td style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>{entry.eventType}</td>
                    <td style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>{entry.resource}</td>
                    <td style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>{entry.actorId ?? "system"}</td>
                    <td style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>{entry.ipAddress ?? "n/a"}</td>
                    <td style={{ padding: `${theme.spacing.sm} ${theme.spacing.md}` }}>
                      <Button type="button" variant="ghost" onClick={() => setSelectedEntry(entry)}>
                        View details
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Modal
        open={selectedEntry !== null}
        title={selectedEntry ? `Audit event: ${selectedEntry.eventType}` : "Audit event"}
        onClose={() => setSelectedEntry(null)}
        footer={
          <Button type="button" variant="secondary" onClick={() => setSelectedEntry(null)}>
            Close
          </Button>
        }
      >
        {selectedEntry ? (
          <div style={{ display: "grid", gap: theme.spacing.md }}>
            <div style={{ display: "grid", gap: theme.spacing.xs }}>
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Timestamp</span>
              <strong>{formatDateTime(selectedEntry.createdAt)}</strong>
            </div>
            <div style={{ display: "grid", gap: theme.spacing.xs }}>
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Actor</span>
              <strong>{selectedEntry.actorId ?? "System"}</strong>
            </div>
            <div style={{ display: "grid", gap: theme.spacing.xs }}>
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Resource</span>
              <strong>{selectedEntry.resource}</strong>
            </div>
            {selectedEntry.ipAddress ? (
              <div style={{ display: "grid", gap: theme.spacing.xs }}>
                <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>IP address</span>
                <strong>{selectedEntry.ipAddress}</strong>
              </div>
            ) : null}
            {selectedEntry.userAgent ? (
              <div style={{ display: "grid", gap: theme.spacing.xs }}>
                <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>User agent</span>
                <span style={{ wordBreak: "break-word" }}>{selectedEntry.userAgent}</span>
              </div>
            ) : null}
            {selectedEntry.message ? (
              <div style={{ display: "grid", gap: theme.spacing.xs }}>
                <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Message</span>
                <span>{selectedEntry.message}</span>
              </div>
            ) : null}
            <div style={{ display: "grid", gap: theme.spacing.xs }}>
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Metadata</span>
              <pre
                style={{
                  backgroundColor: "rgba(15, 23, 42, 0.05)",
                  padding: theme.spacing.md,
                  borderRadius: theme.borderRadius,
                  margin: 0,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  fontSize: theme.font.size.xs,
                }}
              >
                {JSON.stringify(selectedEntry.metadata ?? {}, null, 2)}
              </pre>
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
};
