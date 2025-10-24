import { FormEvent, useEffect, useMemo, useState } from "react";

import { uploadSeal } from "../../lib/sealApi";
import type { SealSummary } from "../../types/seal";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { Input } from "../ui/Input";
import { Spinner } from "../ui/Spinner";
import { useTheme } from "../ThemeProvider";

type SealUploadManagerProps = {
  onUploaded?: (seal: SealSummary) => void;
  maxBytes?: number;
};

type ValidationErrors = {
  name?: string;
  file?: string;
  form?: string;
};

const DEFAULT_MAX_BYTES = 1024 * 1024; // 1 MiB
const ALLOWED_TYPES = new Set(["image/png", "image/svg+xml"]);

const formatSize = (bytes: number): string => {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  }
  if (bytes >= 1024) {
    return `${(bytes / 1024).toFixed(2)} KB`;
  }
  return `${bytes} bytes`;
};

const isSvg = (file: File | null) => file?.type === "image/svg+xml";

export const SealUploadManager = ({ onUploaded, maxBytes = DEFAULT_MAX_BYTES }: SealUploadManagerProps) => {
  const theme = useTheme();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(null);
      return;
    }
    const objectUrl = URL.createObjectURL(file);
    setPreviewUrl(objectUrl);
    return () => {
      URL.revokeObjectURL(objectUrl);
    };
  }, [file]);

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
    const selected = event.target.files?.[0] ?? null;
    if (!selected) {
      setFile(null);
      setErrors((previous) => ({ ...previous, file: "Choose an image to upload." }));
      return;
    }

    if (!ALLOWED_TYPES.has(selected.type)) {
      setFile(null);
      setErrors({ file: "Unsupported image type. Only PNG and SVG files are allowed." });
      return;
    }

    if (selected.size > maxBytes) {
      setFile(null);
      setErrors({ file: `Image exceeds the ${formatSize(maxBytes)} limit.` });
      return;
    }

    setErrors((previous) => ({ ...previous, file: undefined }));
    setFile(selected);
    setSuccessMessage(null);
  };

  const validate = (): ValidationErrors => {
    const nextErrors: ValidationErrors = {};

    if (!name.trim()) {
      nextErrors.name = "Provide a display name for the seal.";
    }

    if (!file) {
      nextErrors.file = "Select an image to upload.";
    }

    return nextErrors;
  };

  const resetForm = () => {
    setName("");
    setDescription("");
    setFile(null);
    setPreviewUrl(null);
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSuccessMessage(null);

    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    if (!file) {
      return;
    }

    setIsSubmitting(true);
    try {
      const seal = await uploadSeal({
        file,
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setSuccessMessage(`Seal \"${seal.name}\" uploaded successfully.`);
      setErrors({});
      resetForm();
      onUploaded?.(seal);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to upload seal image.";
      setErrors({ form: message });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card title="Upload seal image">
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.lg }}>
        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Seal name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Company approvals"
            required
          />
          {errors.name ? <span style={errorTextStyle}>{errors.name}</span> : null}
        </div>

        <div style={{ display: "grid", gap: theme.spacing.sm }}>
          <Input
            label="Description (optional)"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Used when signing purchase orders"
          />
        </div>

        <div style={{ display: "grid", gap: theme.spacing.xs }}>
          <label style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }} htmlFor="seal-upload">
            Seal image
          </label>
          <input
            id="seal-upload"
            type="file"
            accept="image/png,image/svg+xml"
            onChange={handleFileChange}
          />
          <span style={helperTextStyle}>
            Upload a high-resolution PNG or SVG image up to {formatSize(maxBytes)} in size.
          </span>
          {errors.file ? <span style={errorTextStyle}>{errors.file}</span> : null}
        </div>

        {previewUrl ? (
          <div
            style={{
              display: "grid",
              gap: theme.spacing.xs,
              border: `1px dashed ${theme.colors.muted}`,
              borderRadius: theme.borderRadius,
              padding: theme.spacing.md,
            }}
          >
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>Preview</span>
            {isSvg(file) ? (
              <object data={previewUrl} type="image/svg+xml" style={{ width: "180px", height: "180px" }}>
                SVG preview unavailable
              </object>
            ) : (
              <img
                src={previewUrl}
                alt={name || "Seal preview"}
                style={{ width: "180px", height: "180px", objectFit: "contain" }}
              />
            )}
          </div>
        ) : null}

        {errors.form ? <span style={errorTextStyle}>{errors.form}</span> : null}
        {successMessage ? <span style={{ color: theme.colors.success }}>{successMessage}</span> : null}

        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? (
            <>
              <Spinner size={18} /> Uploading seal...
            </>
          ) : (
            "Upload seal"
          )}
        </Button>
      </form>
    </Card>
  );
};
