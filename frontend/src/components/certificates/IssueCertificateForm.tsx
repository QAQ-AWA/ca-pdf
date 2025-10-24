import { FormEvent, useMemo, useState } from "react";

import { issueCertificate } from "../../lib/caApi";
import { triggerFileDownload } from "../../lib/download";
import type { CertificateIssuePayload, CertificateIssueResult } from "../../types/ca";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { Spinner } from "../ui/Spinner";
import { useTheme } from "../ThemeProvider";

type FormState = {
  commonName: string;
  organization: string;
  validityDays: string;
  algorithm: CertificateIssuePayload["algorithm"];
  passphrase: string;
  confirmPassphrase: string;
};

type ValidationErrors = Partial<Record<keyof FormState | "form", string>>;

type IssueCertificateFormProps = {
  onIssued?: (result: CertificateIssueResult) => void;
};

const DEFAULT_STATE: FormState = {
  commonName: "",
  organization: "",
  validityDays: "365",
  algorithm: "rsa-2048",
  passphrase: "",
  confirmPassphrase: "",
};

const MIN_COMMON_NAME = 3;
const MAX_COMMON_NAME = 255;
const MAX_ORGANIZATION = 255;
const MIN_VALIDITY = 1;
const MAX_VALIDITY = 1825;
const MIN_PASSPHRASE_LENGTH = 8;

const toBase64Blob = (base64: string, contentType: string): Blob => {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i += 1) {
    bytes[i] = binary.charCodeAt(i);
  }
  return new Blob([bytes], { type: contentType });
};

const formatDate = (value: Date): string => value.toLocaleString();

export const IssueCertificateForm = ({ onIssued }: IssueCertificateFormProps) => {
  const theme = useTheme();
  const [form, setForm] = useState<FormState>(DEFAULT_STATE);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<CertificateIssueResult | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const isPassphraseProvided = useMemo(() => form.passphrase.trim().length > 0, [form.passphrase]);

  const handleFieldChange = (field: keyof FormState) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setForm((previous) => ({
      ...previous,
      [field]: event.target.value,
    }));
    setErrors((previous) => ({ ...previous, [field]: undefined }));
    setSubmitError(null);
  };

  const validate = (state: FormState): ValidationErrors => {
    const nextErrors: ValidationErrors = {};

    const trimmedCommonName = state.commonName.trim();
    if (trimmedCommonName.length < MIN_COMMON_NAME) {
      nextErrors.commonName = `Common name must be at least ${MIN_COMMON_NAME} characters.`;
    } else if (trimmedCommonName.length > MAX_COMMON_NAME) {
      nextErrors.commonName = `Common name must be fewer than ${MAX_COMMON_NAME} characters.`;
    }

    const trimmedOrg = state.organization.trim();
    if (trimmedOrg.length > MAX_ORGANIZATION) {
      nextErrors.organization = `Organization must be fewer than ${MAX_ORGANIZATION} characters.`;
    }

    const validity = Number.parseInt(state.validityDays, 10);
    if (Number.isNaN(validity)) {
      nextErrors.validityDays = "Validity period must be a numeric value.";
    } else if (validity < MIN_VALIDITY || validity > MAX_VALIDITY) {
      nextErrors.validityDays = `Validity period must be between ${MIN_VALIDITY} and ${MAX_VALIDITY} days.`;
    }

    if (state.passphrase && state.passphrase.length < MIN_PASSPHRASE_LENGTH) {
      nextErrors.passphrase = `Passphrase must be at least ${MIN_PASSPHRASE_LENGTH} characters when provided.`;
    }

    if (state.passphrase !== state.confirmPassphrase) {
      nextErrors.confirmPassphrase = "Passphrases do not match.";
    }

    return nextErrors;
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitError(null);
    const validationErrors = validate(form);

    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    const validityDays = Number.parseInt(form.validityDays, 10);
    const payload: CertificateIssuePayload = {
      commonName: form.commonName.trim(),
      organization: form.organization.trim() || null,
      algorithm: form.algorithm,
      validityDays,
      passphrase: form.passphrase ? form.passphrase : null,
    };

    setIsSubmitting(true);
    try {
      const issued = await issueCertificate(payload);
      setResult(issued);
      setForm(DEFAULT_STATE);
      setErrors({});
      onIssued?.(issued);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unable to issue certificate";
      setSubmitError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadBundle = () => {
    if (!result?.p12Bundle) {
      return;
    }
    const blob = toBase64Blob(result.p12Bundle, "application/x-pkcs12");
    const filename = `certificate-${result.serialNumber}.p12`;
    triggerFileDownload(blob, filename);
  };

  const helperTextStyle: React.CSSProperties = useMemo(
    () => ({
      fontSize: theme.font.size.xs,
      color: theme.colors.muted,
    }),
    [theme]
  );

  const errorTextStyle: React.CSSProperties = useMemo(
    () => ({
      fontSize: theme.font.size.xs,
      color: theme.colors.danger,
    }),
    [theme]
  );

  return (
    <Card title="Issue new certificate">
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.lg }}>
        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Common name"
            value={form.commonName}
            onChange={handleFieldChange("commonName")}
            placeholder="e.g. Jane Doe"
            required
          />
          {errors.commonName ? <span style={errorTextStyle}>{errors.commonName}</span> : null}
        </div>

        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Organization (optional)"
            value={form.organization}
            onChange={handleFieldChange("organization")}
            placeholder="Company or department"
          />
          {errors.organization ? <span style={errorTextStyle}>{errors.organization}</span> : null}
        </div>

        <div style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>Key algorithm</span>
          <div style={{ display: "flex", gap: theme.spacing.lg }}>
            <label style={{ display: "flex", alignItems: "center", gap: theme.spacing.xs }}>
              <input
                type="radio"
                name="algorithm"
                value="rsa-2048"
                checked={form.algorithm === "rsa-2048"}
                onChange={handleFieldChange("algorithm")}
              />
              RSA 2048
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: theme.spacing.xs }}>
              <input
                type="radio"
                name="algorithm"
                value="ec-p256"
                checked={form.algorithm === "ec-p256"}
                onChange={handleFieldChange("algorithm")}
              />
              ECDSA P-256
            </label>
          </div>
          <span style={helperTextStyle}>Choose the asymmetric key algorithm for the issued certificate.</span>
        </div>

        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Validity period (days)"
            type="number"
            min={MIN_VALIDITY}
            max={MAX_VALIDITY}
            value={form.validityDays}
            onChange={handleFieldChange("validityDays")}
            required
          />
          {errors.validityDays ? <span style={errorTextStyle}>{errors.validityDays}</span> : null}
        </div>

        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="PKCS#12 passphrase (optional)"
            type="password"
            value={form.passphrase}
            onChange={handleFieldChange("passphrase")}
            placeholder="Leave blank for an unprotected bundle"
          />
          {isPassphraseProvided ? (
            <span style={helperTextStyle}>
              Passphrase must be at least {MIN_PASSPHRASE_LENGTH} characters. Store it securely.
            </span>
          ) : (
            <span style={helperTextStyle}>If omitted, the bundle will be generated without encryption.</span>
          )}
          {errors.passphrase ? <span style={errorTextStyle}>{errors.passphrase}</span> : null}
        </div>

        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Confirm passphrase"
            type="password"
            value={form.confirmPassphrase}
            onChange={handleFieldChange("confirmPassphrase")}
            placeholder="Re-enter the passphrase when set"
            disabled={!isPassphraseProvided}
          />
          {errors.confirmPassphrase ? <span style={errorTextStyle}>{errors.confirmPassphrase}</span> : null}
        </div>

        {submitError ? <span style={errorTextStyle}>{submitError}</span> : null}

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Spinner size={18} /> Issuing certificate...
            </>
          ) : (
            "Issue certificate"
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
          <strong>Certificate issued successfully.</strong>
          <span>
            Serial number <code>{result.serialNumber}</code>
          </span>
          <span>
            Valid from {formatDate(result.issuedAt)} until {formatDate(result.expiresAt)}
          </span>
          {result.p12Bundle ? (
            <Button type="button" onClick={handleDownloadBundle} variant="secondary">
              Download PKCS#12 bundle
            </Button>
          ) : (
            <span style={helperTextStyle}>
              Bundle download not available. Re-issue if you need a fresh export.
            </span>
          )}
        </div>
      ) : null}
    </Card>
  );
};
