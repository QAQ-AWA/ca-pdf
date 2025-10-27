import { FormEvent, useMemo, useState } from "react";

import { importCertificate } from "../../lib/caApi";
import type { CertificateImportResult } from "../../types/ca";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { Spinner } from "../ui/Spinner";
import { useTheme } from "../ThemeProvider";

type ImportCertificateFormProps = {
  onImported?: (result: CertificateImportResult) => void;
};

type ValidationErrors = {
  file?: string;
  passphrase?: string;
  form?: string;
};

type SelectedFile = {
  file: File;
  name: string;
  sizeLabel: string;
};

const MAX_P12_BYTES = 5 * 1024 * 1024; // 5 MiB
const ALLOWED_MIME_TYPES = new Set([
  "application/x-pkcs12",
  "application/pkcs12",
  "application/octet-stream",
]);

const formatSize = (bytes: number): string => {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  }
  return `${bytes} bytes`;
};

const bufferToBase64 = (buffer: ArrayBuffer): string => {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let offset = 0; offset < bytes.length; offset += chunkSize) {
    const chunk = bytes.subarray(offset, offset + chunkSize);
    binary += String.fromCharCode(...chunk);
  }
  return btoa(binary);
};

export const ImportCertificateForm = ({ onImported }: ImportCertificateFormProps) => {
  const theme = useTheme();
  const [selectedFile, setSelectedFile] = useState<SelectedFile | null>(null);
  const [passphrase, setPassphrase] = useState("");
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<CertificateImportResult | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const helperTextStyle = useMemo<React.CSSProperties>(
    () => ({
      fontSize: theme.font.size.xs,
      color: theme.colors.muted,
    }),
    [theme]
  );

  const errorTextStyle = useMemo<React.CSSProperties>(
    () => ({
      fontSize: theme.font.size.xs,
      color: theme.colors.danger,
    }),
    [theme]
  );

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      setSelectedFile(null);
      setErrors({ file: "Choose a PKCS#12 file to import." });
      return;
    }

    if (!ALLOWED_MIME_TYPES.has(file.type)) {
      setSelectedFile(null);
      setErrors({ file: "Unsupported file type. Please select a PKCS#12 bundle (.p12/.pfx)." });
      return;
    }

    if (file.size > MAX_P12_BYTES) {
      setSelectedFile(null);
      setErrors({ file: `File exceeds the ${formatSize(MAX_P12_BYTES)} limit.` });
      return;
    }

    setErrors({});
    setSelectedFile({ file, name: file.name, sizeLabel: formatSize(file.size) });
    setSubmitError(null);
  };

  const validate = (file: SelectedFile | null): ValidationErrors => {
    if (!file) {
      return { file: "Choose a PKCS#12 bundle to import." };
    }

    return {};
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setSubmitError(null);
    const validationErrors = validate(selectedFile);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    if (!selectedFile) {
      setErrors({ file: "Choose a PKCS#12 bundle to import." });
      return;
    }

    setIsSubmitting(true);
    try {
      const buffer = await selectedFile.file.arrayBuffer();
      const encoded = bufferToBase64(buffer);
      const imported = await importCertificate(encoded, passphrase.trim() || null);
      setResult(imported);
      setPassphrase("");
      setSelectedFile(null);
      setErrors({});
      onImported?.(imported);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to import the certificate.";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card title="Import PKCS#12 bundle">
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.lg }}>
        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <label style={{ display: "grid", gap: theme.spacing.xs }}>
            <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>
              PKCS#12 file
            </span>
            <input
              type="file"
              accept=".p12,.pfx,application/x-pkcs12"
              onChange={handleFileChange}
            />
            <span style={helperTextStyle}>
              Upload a PKCS#12 bundle issued by the managed root CA. Maximum size {formatSize(MAX_P12_BYTES)}.
            </span>
            {selectedFile ? (
              <span style={{ fontSize: theme.font.size.xs }}>
                Selected {selectedFile.name} ({selectedFile.sizeLabel})
              </span>
            ) : null}
            {errors.file ? <span style={errorTextStyle}>{errors.file}</span> : null}
          </label>
        </div>

        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Bundle passphrase (optional)"
            type="password"
            value={passphrase}
            onChange={(event) => setPassphrase(event.target.value)}
            placeholder="Passphrase used to encrypt the bundle"
          />
          <span style={helperTextStyle}>
            Provide the passphrase if the PKCS#12 bundle is protected. Leave blank if it is unencrypted.
          </span>
          {errors.passphrase ? <span style={errorTextStyle}>{errors.passphrase}</span> : null}
        </div>

        {submitError ? <span style={errorTextStyle}>{submitError}</span> : null}

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Spinner size={18} /> Importing bundle...
            </>
          ) : (
            "Import certificate"
          )}
        </Button>
      </form>

      {result ? (
        <div
          style={{
            border: `1px solid ${theme.colors.muted}`,
            borderRadius: theme.borderRadius,
            padding: theme.spacing.lg,
            display: "grid",
            gap: theme.spacing.sm,
          }}
        >
          <strong>Certificate imported successfully.</strong>
          <span>
            Serial number <code>{result.serialNumber}</code>
          </span>
          <span>
            Valid until {result.expiresAt.toLocaleString()}
          </span>
        </div>
      ) : null}
    </Card>
  );
};
