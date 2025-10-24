import { useCallback, useEffect, useState } from "react";

import { CertificateList } from "../../components/certificates/CertificateList";
import { CrlStatusCard } from "../../components/certificates/CrlStatusCard";
import { ImportCertificateForm } from "../../components/certificates/ImportCertificateForm";
import { IssueCertificateForm } from "../../components/certificates/IssueCertificateForm";
import { useAuth } from "../../contexts/AuthContext";
import {
  downloadCertificateBundle,
  downloadCrl,
  fetchCertificates,
  generateCrl,
  listCrls,
  revokeCertificate,
} from "../../lib/caApi";
import { triggerFileDownload } from "../../lib/download";
import type { CertificateSummary, CrlMetadata } from "../../types/ca";
import { useTheme } from "../../components/ThemeProvider";

export const CertificatesPage = () => {
  const theme = useTheme();
  const { hasRole } = useAuth();
  const isAdmin = hasRole("admin");

  const [certificates, setCertificates] = useState<CertificateSummary[]>([]);
  const [certificatesLoading, setCertificatesLoading] = useState(false);
  const [certificatesError, setCertificatesError] = useState<string | null>(null);
  const [certificateMessage, setCertificateMessage] = useState<string | null>(null);

  const [crls, setCrls] = useState<CrlMetadata[]>([]);
  const [crlLoading, setCrlLoading] = useState(false);
  const [crlError, setCrlError] = useState<string | null>(null);
  const [crlMessage, setCrlMessage] = useState<string | null>(null);
  const [isGeneratingCrl, setIsGeneratingCrl] = useState(false);

  const loadCertificates = useCallback(async () => {
    setCertificatesLoading(true);
    setCertificatesError(null);
    try {
      const data = await fetchCertificates();
      setCertificates(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load certificates.";
      setCertificatesError(message);
    } finally {
      setCertificatesLoading(false);
    }
  }, []);

  const loadCrls = useCallback(async () => {
    setCrlLoading(true);
    setCrlError(null);
    try {
      const data = await listCrls();
      setCrls(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to load CRLs.";
      setCrlError(message);
    } finally {
      setCrlLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadCertificates();
  }, [loadCertificates]);

  useEffect(() => {
    void loadCrls();
  }, [loadCrls]);

  const handleDownloadBundle = useCallback(async (certificate: CertificateSummary) => {
    try {
      const { blob, filename } = await downloadCertificateBundle(certificate.id);
      triggerFileDownload(blob, filename);
      setCertificateMessage(`PKCS#12 bundle downloaded for ${certificate.serialNumber}.`);
      setCertificatesError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to download bundle.";
      setCertificatesError(message);
    }
  }, []);

  const handleCertificateIssued = useCallback(
    async () => {
      setCertificateMessage("Certificate issued successfully.");
      await loadCertificates();
    },
    [loadCertificates]
  );

  const handleCertificateImported = useCallback(
    async () => {
      setCertificateMessage("Certificate imported successfully.");
      await loadCertificates();
    },
    [loadCertificates]
  );

  const handleRevokeCertificate = useCallback(
    async (certificate: CertificateSummary) => {
      try {
        const result = await revokeCertificate(certificate.id);
        setCertificates((previous) =>
          previous.map((entry) =>
            entry.id === certificate.id
              ? {
                  ...entry,
                  status: result.status,
                }
              : entry
          )
        );
        setCertificateMessage(`Certificate ${certificate.serialNumber} revoked.`);
        setCertificatesError(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to revoke certificate.";
        setCertificatesError(message);
      }
    },
    []
  );

  const handleGenerateCrl = useCallback(async () => {
    setCrlError(null);
    setCrlMessage(null);
    setIsGeneratingCrl(true);
    try {
      const result = await generateCrl();
      setCrlMessage(`CRL ${result.name} generated.`);
      const blob = new Blob([result.crlPem], { type: "application/pkix-crl" });
      triggerFileDownload(blob, `${result.name}.crl`);
      await loadCrls();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate CRL.";
      setCrlError(message);
    } finally {
      setIsGeneratingCrl(false);
    }
  }, [loadCrls]);

  const handleDownloadCrl = useCallback(async (crl: CrlMetadata) => {
    try {
      const { blob, filename } = await downloadCrl(crl.artifactId);
      triggerFileDownload(blob, filename);
      setCrlError(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to download CRL.";
      setCrlError(message);
    }
  }, []);

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <header style={{ display: "grid", gap: theme.spacing.xs }}>
        <h2 style={{ margin: 0 }}>Certificate management</h2>
        <p style={{ margin: 0, color: theme.colors.muted }}>
          Issue, import, and manage end-entity certificates for your organization. Admins can revoke
          certificates and publish certificate revocation lists.
        </p>
      </header>

      {certificateMessage ? (
        <span style={{ color: theme.colors.success }}>{certificateMessage}</span>
      ) : null}
      {certificatesError ? <span style={{ color: theme.colors.danger }}>{certificatesError}</span> : null}

      <CertificateList
        certificates={certificates}
        loading={certificatesLoading}
        error={null}
        onRefresh={() => void loadCertificates()}
        onDownloadBundle={handleDownloadBundle}
        onRevoke={isAdmin ? handleRevokeCertificate : undefined}
        isAdmin={isAdmin}
      />

      <IssueCertificateForm onIssued={handleCertificateIssued} />
      <ImportCertificateForm onImported={handleCertificateImported} />

      {crlMessage ? <span style={{ color: theme.colors.success }}>{crlMessage}</span> : null}
      {crlError ? <span style={{ color: theme.colors.danger }}>{crlError}</span> : null}

      <CrlStatusCard
        crls={crls}
        loading={crlLoading}
        onRefresh={() => void loadCrls()}
        onGenerate={isAdmin ? handleGenerateCrl : undefined}
        onDownload={handleDownloadCrl}
        isAdmin={isAdmin}
        isGenerating={isGeneratingCrl}
      />
    </div>
  );
};
