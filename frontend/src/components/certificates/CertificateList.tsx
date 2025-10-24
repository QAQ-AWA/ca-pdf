import { useMemo, useState } from "react";

import type { CertificateSummary } from "../../types/ca";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Spinner } from "../ui/Spinner";
import { useTheme } from "../ThemeProvider";

type CertificateListProps = {
  certificates: CertificateSummary[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onDownloadBundle: (certificate: CertificateSummary) => Promise<void> | void;
  onRevoke?: (certificate: CertificateSummary) => Promise<void> | void;
  isAdmin?: boolean;
};

const statusLabel: Record<CertificateSummary["status"], string> = {
  active: "Active",
  revoked: "Revoked",
  expired: "Expired",
  pending: "Pending",
};

export const CertificateList = ({
  certificates,
  loading = false,
  error,
  onRefresh,
  onDownloadBundle,
  onRevoke,
  isAdmin = false,
}: CertificateListProps) => {
  const theme = useTheme();
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const statusColors = useMemo<Record<CertificateSummary["status"], string>>(
    () => ({
      active: theme.colors.success,
      revoked: theme.colors.danger,
      expired: theme.colors.warning,
      pending: theme.colors.secondary,
    }),
    [theme]
  );

  const handleDownload = async (certificate: CertificateSummary) => {
    try {
      setDownloadingId(certificate.id);
      await onDownloadBundle(certificate);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleRevoke = async (certificate: CertificateSummary) => {
    if (!onRevoke) {
      return;
    }

    const confirmed = window.confirm(
      `Revoke certificate ${certificate.serialNumber}? This action cannot be undone.`
    );
    if (!confirmed) {
      return;
    }

    try {
      setRevokingId(certificate.id);
      await onRevoke(certificate);
    } finally {
      setRevokingId(null);
    }
  };

  return (
    <Card
      title="Your certificates"
      action={
        onRefresh ? (
          <Button onClick={onRefresh} variant="ghost" type="button">
            Refresh
          </Button>
        ) : undefined
      }
    >
      {loading ? (
        <div style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
          <Spinner size={20} />
          <span>Loading certificates...</span>
        </div>
      ) : null}

      {error ? <span style={{ color: theme.colors.danger }}>{error}</span> : null}

      {!loading && !error && certificates.length === 0 ? (
        <p style={{ margin: 0, color: theme.colors.muted }}>
          No certificates issued yet. Issue a new certificate to get started.
        </p>
      ) : null}

      <div style={{ display: "grid", gap: theme.spacing.md }}>
        {certificates.map((certificate) => (
          <article
            key={certificate.id}
            style={{
              border: `1px solid ${theme.colors.muted}`,
              borderRadius: theme.borderRadius,
              padding: theme.spacing.lg,
              display: "grid",
              gap: theme.spacing.sm,
            }}
          >
            <header
              style={{
                display: "flex",
                flexDirection: "row",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: theme.spacing.md,
              }}
            >
              <div style={{ display: "grid", gap: theme.spacing.xs }}>
                <strong style={{ fontSize: theme.font.size.base }}>{certificate.subjectCommonName}</strong>
                <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
                  Serial {certificate.serialNumber}
                </span>
              </div>
              <span
                style={{
                  padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                  borderRadius: "999px",
                  backgroundColor: `${statusColors[certificate.status]}20`,
                  color: statusColors[certificate.status],
                  fontSize: theme.font.size.xs,
                  fontWeight: theme.font.weight.medium,
                  textTransform: "uppercase",
                  letterSpacing: 0.6,
                }}
              >
                {statusLabel[certificate.status]}
              </span>
            </header>

            <dl
              style={{
                display: "grid",
                gridTemplateColumns: "auto 1fr",
                gap: theme.spacing.xs,
                fontSize: theme.font.size.sm,
                margin: 0,
              }}
            >
              <dt>Issued</dt>
              <dd style={{ margin: 0 }}>{certificate.issuedAt.toLocaleString()}</dd>
              <dt>Expires</dt>
              <dd style={{ margin: 0 }}>{certificate.expiresAt.toLocaleString()}</dd>
            </dl>

            <footer
              style={{
                display: "flex",
                flexWrap: "wrap",
                gap: theme.spacing.sm,
              }}
            >
              <Button
                variant="secondary"
                type="button"
                onClick={() => void handleDownload(certificate)}
                disabled={downloadingId === certificate.id}
              >
                {downloadingId === certificate.id ? (
                  <>
                    <Spinner size={18} /> Downloading...
                  </>
                ) : (
                  "Download bundle"
                )}
              </Button>

              {isAdmin ? (
                <Button
                  variant="ghost"
                  type="button"
                  onClick={() => void handleRevoke(certificate)}
                  disabled={revokingId === certificate.id || certificate.status !== "active"}
                >
                  {revokingId === certificate.id ? (
                    <>
                      <Spinner size={18} /> Revoking...
                    </>
                  ) : (
                    "Revoke"
                  )}
                </Button>
              ) : null}
            </footer>
          </article>
        ))}
      </div>
    </Card>
  );
};
