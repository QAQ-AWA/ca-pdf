import { ChangeEvent, FormEvent, useMemo, useRef, useState } from "react";
import type { CSSProperties } from "react";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Spinner } from "../../components/ui/Spinner";
import { useTheme } from "../../components/ThemeProvider";
import { verifyPdf } from "../../lib/verificationApi";
import type { PdfVerificationReport, SignatureVerificationResult } from "../../types/verification";

type StatusPillProps = {
  label: string;
  status: boolean | null;
};

const StatusPill = ({ label, status }: StatusPillProps) => {
  const theme = useTheme();

  const styles = useMemo<CSSProperties>(() => {
    if (status === null) {
      return {
        backgroundColor: "rgba(148, 163, 184, 0.15)",
        color: theme.colors.muted,
        border: `1px solid rgba(148, 163, 184, 0.2)`,
      };
    }

    if (status) {
      return {
        backgroundColor: "rgba(22, 163, 74, 0.12)",
        color: theme.colors.success,
        border: `1px solid rgba(22, 163, 74, 0.24)`,
      };
    }

    return {
      backgroundColor: "rgba(220, 38, 38, 0.12)",
      color: theme.colors.danger,
      border: `1px solid rgba(220, 38, 38, 0.24)`
    };
  }, [status, theme.colors.danger, theme.colors.muted, theme.colors.success]);

  return (
    <span
      style={{
        padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
        borderRadius: theme.borderRadius,
        fontSize: theme.font.size.sm,
        fontWeight: theme.font.weight.medium,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        whiteSpace: "nowrap",
        ...styles,
      }}
    >
      {label}
    </span>
  );
};

const formatDateTime = (value: Date | null): string => {
  if (!value) {
    return "Not provided";
  }

  try {
    return new Intl.DateTimeFormat(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(value);
  } catch (error) {
    return value.toISOString();
  }
};

export const VerificationPage = () => {
  const theme = useTheme();
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [report, setReport] = useState<PdfVerificationReport | null>(null);
  const [verifiedFilename, setVerifiedFilename] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] ?? null;

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (file.type !== "application/pdf") {
      setError("Select a PDF document to verify.");
      setSelectedFile(null);
      event.target.value = "";
      return;
    }

    setSelectedFile(file);
    setError(null);
    setReport(null);
    setVerifiedFilename(null);
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setReport(null);
    setVerifiedFilename(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!selectedFile) {
      setError("Select a signed PDF to run verification.");
      return;
    }

    setIsVerifying(true);
    setError(null);

    try {
      const result = await verifyPdf(selectedFile);
      setReport(result);
      setVerifiedFilename(selectedFile.name);
    } catch (submissionError) {
      const message =
        submissionError instanceof Error
          ? submissionError.message
          : "Verification failed. Try again.";
      setReport(null);
      setVerifiedFilename(null);
      setError(message);
    } finally {
      setIsVerifying(false);
    }
  };

  const renderSignatureDetails = (signature: SignatureVerificationResult) => (
    <div
      key={`${signature.fieldName}-${signature.summary}`}
      style={{
        border: `1px solid rgba(148, 163, 184, 0.24)`,
        borderRadius: theme.borderRadius,
        padding: theme.spacing.lg,
        display: "grid",
        gap: theme.spacing.md,
        backgroundColor: "rgba(248, 250, 252, 0.6)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          flexWrap: "wrap",
          gap: theme.spacing.sm,
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: theme.font.size.base }}>{signature.fieldName}</h3>
          <p style={{ margin: 0, color: theme.colors.muted }}>{signature.summary}</p>
        </div>
        <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap" }}>
          <StatusPill label={signature.valid ? "Signature valid" : "Signature invalid"} status={signature.valid} />
          <StatusPill
            label={signature.trusted ? "Trusted chain" : "Untrusted chain"}
            status={signature.trusted}
          />
          <StatusPill
            label={
              signature.timestampTrusted === null
                ? "No timestamp"
                : signature.timestampTrusted
                  ? "Timestamp trusted"
                  : "Timestamp untrusted"
            }
            status={signature.timestampTrusted}
          />
        </div>
      </div>

      <div
        style={{
          display: "grid",
          gap: theme.spacing.sm,
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
        }}
      >
        <div style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Signer</span>
          <strong>{signature.signerCommonName ?? "Unknown"}</strong>
          <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
            Serial: {signature.signerSerialNumber ?? "n/a"}
          </span>
        </div>
        <div style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Signed at</span>
          <strong>{formatDateTime(signature.signingTime)}</strong>
          {signature.modificationLevel ? (
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
              Modification level: {signature.modificationLevel}
            </span>
          ) : null}
        </div>
        <div style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Timestamp</span>
          <strong>{formatDateTime(signature.timestampTime)}</strong>
          {signature.timestampSummary ? (
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
              {signature.timestampSummary}
            </span>
          ) : null}
        </div>
      </div>

      {signature.docmdpOk !== null || signature.error ? (
        <div
          style={{
            display: "grid",
            gap: theme.spacing.xs,
            borderTop: `1px solid rgba(148, 163, 184, 0.24)`,
            paddingTop: theme.spacing.sm,
          }}
        >
          {signature.docmdpOk !== null ? (
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
              Document modification permissions: {signature.docmdpOk ? "respected" : "violated"}
            </span>
          ) : null}
          {signature.error ? (
            <span style={{ color: theme.colors.danger }}>{signature.error}</span>
          ) : null}
        </div>
      ) : null}
    </div>
  );

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <header style={{ display: "grid", gap: theme.spacing.xs }}>
        <h2 style={{ margin: 0 }}>Verify signed PDF</h2>
        <p style={{ margin: 0, color: theme.colors.muted }}>
          Upload a signed PDF to confirm signature validity, certificate trust chains, and timestamp status.
        </p>
      </header>

      {error ? <span style={{ color: theme.colors.danger }}>{error}</span> : null}

      <Card title="Verification input">
        <form
          onSubmit={handleSubmit}
          style={{
            display: "grid",
            gap: theme.spacing.md,
          }}
        >
          <Input
            ref={fileInputRef}
            type="file"
            accept="application/pdf"
            label="Select signed PDF"
            onChange={handleFileChange}
          />

          {selectedFile ? (
            <span style={{ fontSize: theme.font.size.sm }}>
              Selected file: <strong>{selectedFile.name}</strong>
            </span>
          ) : (
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
              Only PDF files are supported.
            </span>
          )}

          <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap" }}>
            <Button type="submit" disabled={isVerifying}>
              {isVerifying ? (
                <>
                  <Spinner size={18} /> Verifying…
                </>
              ) : (
                "Verify signatures"
              )}
            </Button>
            {selectedFile ? (
              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  clearSelection();
                }}
              >
                Clear selection
              </Button>
            ) : null}
          </div>
        </form>
      </Card>

      {report ? (
        <Card
          title="Verification summary"
          style={{ display: "grid", gap: theme.spacing.lg }}
          action={
            verifiedFilename ? (
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
                Last verified file: {verifiedFilename}
              </span>
            ) : undefined
          }
        >
          <div
            style={{
              display: "grid",
              gap: theme.spacing.md,
              gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            }}
          >
            <div
              style={{
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius,
                background: "rgba(37, 99, 235, 0.08)",
                display: "grid",
                gap: theme.spacing.xs,
              }}
            >
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Detected signatures</span>
              <strong style={{ fontSize: theme.font.size.lg }}>{report.totalSignatures}</strong>
            </div>
            <div
              style={{
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius,
                background: "rgba(22, 163, 74, 0.08)",
                display: "grid",
                gap: theme.spacing.xs,
              }}
            >
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Valid signatures</span>
              <strong style={{ fontSize: theme.font.size.lg }}>{report.validSignatures}</strong>
            </div>
            <div
              style={{
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius,
                background: "rgba(14, 116, 144, 0.08)",
                display: "grid",
                gap: theme.spacing.xs,
              }}
            >
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Trusted signatures</span>
              <strong style={{ fontSize: theme.font.size.lg }}>{report.trustedSignatures}</strong>
            </div>
          </div>

          <div style={{ display: "flex", gap: theme.spacing.sm, flexWrap: "wrap" }}>
            <StatusPill
              label={report.allSignaturesValid ? "All signatures valid" : "Some signatures invalid"}
              status={report.allSignaturesValid}
            />
            <StatusPill
              label={report.allSignaturesTrusted ? "All signatures trusted" : "Untrusted signatures present"}
              status={report.allSignaturesTrusted}
            />
          </div>

          <div style={{ display: "grid", gap: theme.spacing.md }}>
            {report.signatures.length === 0 ? (
              <span style={{ color: theme.colors.muted }}>No signature fields detected in this document.</span>
            ) : (
              report.signatures.map((signature) => renderSignatureDetails(signature))
            )}
          </div>
        </Card>
      ) : null}
    </div>
  );
};
