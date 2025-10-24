import type { CrlMetadata } from "../../types/ca";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Spinner } from "../ui/Spinner";
import { useTheme } from "../ThemeProvider";

type CrlStatusCardProps = {
  crls: CrlMetadata[];
  loading?: boolean;
  error?: string | null;
  onRefresh?: () => void;
  onGenerate?: () => Promise<void> | void;
  onDownload?: (crl: CrlMetadata) => Promise<void> | void;
  isAdmin?: boolean;
  isGenerating?: boolean;
};

export const CrlStatusCard = ({
  crls,
  loading = false,
  error,
  onRefresh,
  onGenerate,
  onDownload,
  isAdmin = false,
  isGenerating = false,
}: CrlStatusCardProps) => {
  const theme = useTheme();

  return (
    <Card
      title="Certificate revocation lists"
      action={
        onRefresh ? (
          <Button type="button" variant="ghost" onClick={onRefresh}>
            Refresh
          </Button>
        ) : undefined
      }
    >
      {loading ? (
        <div style={{ display: "flex", gap: theme.spacing.sm, alignItems: "center" }}>
          <Spinner size={20} />
          <span>Loading CRL metadata...</span>
        </div>
      ) : null}

      {error ? <span style={{ color: theme.colors.danger }}>{error}</span> : null}

      {!loading && !error && crls.length === 0 ? (
        <p style={{ margin: 0, color: theme.colors.muted }}>
          No certificate revocation lists published yet.
        </p>
      ) : null}

      <div style={{ display: "grid", gap: theme.spacing.sm }}>
        {crls.map((crl) => (
          <div
            key={crl.artifactId}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              borderRadius: theme.borderRadius,
              border: `1px solid ${theme.colors.muted}`,
            }}
          >
            <div style={{ display: "grid", gap: theme.spacing.xs }}>
              <strong>{crl.name}</strong>
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
                Published at {crl.createdAt.toLocaleString()}
              </span>
            </div>
            {onDownload ? (
              <Button type="button" variant="secondary" onClick={() => void onDownload(crl)}>
                Download
              </Button>
            ) : null}
          </div>
        ))}
      </div>

      {isAdmin && onGenerate ? (
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button type="button" onClick={() => void onGenerate()} disabled={isGenerating}>
            {isGenerating ? (
              <>
                <Spinner size={18} /> Generating...
              </>
            ) : (
              "Generate new CRL"
            )}
          </Button>
        </div>
      ) : null}
    </Card>
  );
};
