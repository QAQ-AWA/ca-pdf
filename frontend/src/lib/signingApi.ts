import axios, { type AxiosError } from "axios";

import { triggerFileDownload } from "./download";
import { httpClient } from "./httpClient";
import type { SignatureMetadata, SignatureVisibility } from "../types/signing";

const filenameFromDisposition = (headerValue: string | null | undefined): string | null => {
  if (!headerValue) {
    return null;
  }

  const utf8Match = headerValue.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match?.[1]) {
    return decodeURIComponent(utf8Match[1]);
  }

  const asciiMatch = headerValue.match(/filename="?([^";]+)"?/i);
  if (asciiMatch?.[1]) {
    return asciiMatch[1];
  }

  return null;
};

const sanitizeFilename = (name: string): string => {
  if (!name) {
    return "document.pdf";
  }
  const base = name.trim().split(/[/\\]/).pop() ?? name;
  const cleaned = base.replace(/[^\w.\- ]+/g, "_");
  return cleaned || "document.pdf";
};

const toSignedFilename = (name: string): string => {
  const sanitized = sanitizeFilename(name);
  const withoutExtension = sanitized.replace(/\.pdf$/i, "");
  const base = withoutExtension.trim() || "document";
  return `${base}-signed.pdf`;
};

const toBooleanOrNull = (value: string | undefined): boolean | null => {
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  return null;
};

const extractDetailString = (value: unknown): string | null => {
  if (!value || typeof value !== "object") {
    return null;
  }
  const maybeDetail = (value as Record<string, unknown>).detail;
  if (typeof maybeDetail === "string" && maybeDetail.trim()) {
    return maybeDetail.trim();
  }
  return null;
};

const parseTextPayload = (payload: string): string | null => {
  const trimmed = payload.trim();
  if (!trimmed) {
    return null;
  }
  try {
    const parsed = JSON.parse(trimmed);
    const detail = extractDetailString(parsed);
    if (detail) {
      return detail;
    }
  } catch {
    // ignore JSON parse errors
  }
  return trimmed;
};

const arrayBufferToString = (buffer: ArrayBuffer): string => {
  if (typeof TextDecoder !== "undefined") {
    return new TextDecoder().decode(new Uint8Array(buffer));
  }

  let result = "";
  const view = new Uint8Array(buffer);
  for (let index = 0; index < view.length; index += 1) {
    result += String.fromCharCode(view[index]);
  }
  return result;
};

const parseAxiosErrorMessage = async (error: AxiosError<unknown>): Promise<string> => {
  const defaultMessage = error.response?.statusText?.trim() || error.message || "Failed to sign document.";
  const data = error.response?.data;

  if (data instanceof Blob) {
    try {
      const text = await data.text();
      return parseTextPayload(text) ?? defaultMessage;
    } catch {
      return defaultMessage;
    }
  }

  if (data instanceof ArrayBuffer) {
    try {
      const text = arrayBufferToString(data);
      return parseTextPayload(text) ?? defaultMessage;
    } catch {
      return defaultMessage;
    }
  }

  if (typeof data === "string") {
    return parseTextPayload(data) ?? defaultMessage;
  }

  const detail = extractDetailString(data);
  if (detail) {
    return detail;
  }

  return defaultMessage || "Failed to sign document.";
};

type CoordinatesPayload = {
  page: number;
  x: number;
  y: number;
  width: number;
  height: number;
};

type CommonSignOptions = {
  certificateId: string;
  sealId?: string | null;
  visibility: SignatureVisibility;
  coordinates?: CoordinatesPayload | null;
  metadata?: SignatureMetadata | null;
  useTsa?: boolean;
  embedLtv?: boolean;
};

export type SignPdfOptions = CommonSignOptions & {
  file: Blob | File;
  filename?: string;
};

export type SignPdfResult = {
  blob: Blob;
  filename: string;
  contentType: string;
  documentId: string | null;
  signedAt: string | null;
  certificateId: string | null;
  sealId: string | null;
  visibility: SignatureVisibility | null;
  tsaUsed: boolean | null;
  ltvEmbedded: boolean | null;
};

export const signPdf = async (options: SignPdfOptions): Promise<SignPdfResult> => {
  const formData = new FormData();
  const rawFilename =
    options.filename ?? ("name" in options.file ? (options.file as File).name : undefined) ?? "document.pdf";
  const uploadFilename = sanitizeFilename(rawFilename);

  formData.append("pdf_file", options.file, uploadFilename);
  formData.append("certificate_id", options.certificateId);

  if (options.sealId) {
    formData.append("seal_id", options.sealId);
  }

  formData.append("visibility", options.visibility);

  if (options.visibility === "visible" && options.coordinates) {
    formData.append("page", String(options.coordinates.page));
    formData.append("x", String(options.coordinates.x));
    formData.append("y", String(options.coordinates.y));
    formData.append("width", String(options.coordinates.width));
    formData.append("height", String(options.coordinates.height));
  }

  if (options.metadata?.reason) {
    formData.append("reason", options.metadata.reason);
  }
  if (options.metadata?.location) {
    formData.append("location", options.metadata.location);
  }
  if (options.metadata?.contactInfo) {
    formData.append("contact_info", options.metadata.contactInfo);
  }

  if (options.useTsa) {
    formData.append("use_tsa", "true");
  }

  if (options.embedLtv) {
    formData.append("embed_ltv", "true");
  }

  try {
    const response = await httpClient.post<Blob | ArrayBuffer>("/api/v1/pdf/sign", formData, {
      responseType: "blob",
    });

    const contentType = response.headers["content-type"] ?? "application/pdf";
    const disposition = response.headers["content-disposition"] ?? null;
    const headerFilename = filenameFromDisposition(disposition);
    const sanitizedHeaderFilename = headerFilename ? sanitizeFilename(headerFilename) : null;
    const filename = sanitizedHeaderFilename ?? toSignedFilename(rawFilename);

    const data = response.data;
    let blob: Blob;
    if (data instanceof Blob) {
      blob = data.type ? data : new Blob([data], { type: contentType });
    } else {
      blob = new Blob([data], { type: contentType });
    }

    if (typeof window !== "undefined" && typeof document !== "undefined") {
      triggerFileDownload(blob, filename);
    }

    const visibilityHeader = response.headers["x-visibility"];
    const visibility: SignatureVisibility | null =
      visibilityHeader === "visible" || visibilityHeader === "invisible"
        ? (visibilityHeader as SignatureVisibility)
        : null;

    const documentIdHeader = response.headers["x-document-id"];
    const signedAtHeader = response.headers["x-signed-at"];
    const certificateIdHeader = response.headers["x-certificate-id"];
    const sealIdHeader = response.headers["x-seal-id"];
    const tsaUsedHeader = response.headers["x-tsa-used"];
    const ltvEmbeddedHeader = response.headers["x-ltv-embedded"];

    return {
      blob,
      filename,
      contentType: blob.type || contentType,
      documentId: typeof documentIdHeader === "string" && documentIdHeader ? documentIdHeader : null,
      signedAt: typeof signedAtHeader === "string" && signedAtHeader ? signedAtHeader : null,
      certificateId:
        typeof certificateIdHeader === "string" && certificateIdHeader ? certificateIdHeader : null,
      sealId: typeof sealIdHeader === "string" && sealIdHeader ? sealIdHeader : null,
      visibility,
      tsaUsed: toBooleanOrNull(tsaUsedHeader),
      ltvEmbedded: toBooleanOrNull(ltvEmbeddedHeader),
    };
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const message = await parseAxiosErrorMessage(error);
      throw new Error(message);
    }
    throw error;
  }
};

export type BatchSignOptions = CommonSignOptions & {
  files: Array<{ file: Blob | File; filename?: string }>;
};

export type BatchSignResultItem = {
  filename: string;
  success: boolean;
  documentId: string | null;
  signedAt: string | null;
  fileSize: number | null;
  error: string | null;
};

export type BatchSignResult = {
  total: number;
  successful: number;
  failed: number;
  results: BatchSignResultItem[];
  certificateId: string;
  sealId: string | null;
  visibility: SignatureVisibility;
  tsaUsed: boolean;
  ltvEmbedded: boolean;
};

export const batchSignPdfs = async (options: BatchSignOptions): Promise<BatchSignResult> => {
  const formData = new FormData();

  options.files.forEach((entry, index) => {
    const filename =
      entry.filename ?? ("name" in entry.file ? (entry.file as File).name : undefined) ?? `document-${index + 1}.pdf`;
    formData.append("pdf_files", entry.file, filename);
  });

  formData.append("certificate_id", options.certificateId);

  if (options.sealId) {
    formData.append("seal_id", options.sealId);
  }

  formData.append("visibility", options.visibility);

  if (options.visibility === "visible" && options.coordinates) {
    formData.append("page", String(options.coordinates.page));
    formData.append("x", String(options.coordinates.x));
    formData.append("y", String(options.coordinates.y));
    formData.append("width", String(options.coordinates.width));
    formData.append("height", String(options.coordinates.height));
  }

  if (options.metadata?.reason) {
    formData.append("reason", options.metadata.reason);
  }
  if (options.metadata?.location) {
    formData.append("location", options.metadata.location);
  }
  if (options.metadata?.contactInfo) {
    formData.append("contact_info", options.metadata.contactInfo);
  }

  if (options.useTsa) {
    formData.append("use_tsa", "true");
  }
  if (options.embedLtv) {
    formData.append("embed_ltv", "true");
  }

  const response = await httpClient.post<{
    total: number;
    successful: number;
    failed: number;
    results: Array<{
      filename: string;
      success: boolean;
      document_id: string | null;
      signed_at: string | null;
      file_size: number | null;
      error: string | null;
    }>;
    certificate_id: string;
    seal_id: string | null;
    visibility: SignatureVisibility;
    tsa_used: boolean;
    ltv_embedded: boolean;
  }>("/api/v1/pdf/sign/batch", formData);

  return {
    total: response.data.total,
    successful: response.data.successful,
    failed: response.data.failed,
    certificateId: response.data.certificate_id,
    sealId: response.data.seal_id,
    visibility: response.data.visibility,
    tsaUsed: response.data.tsa_used,
    ltvEmbedded: response.data.ltv_embedded,
    results: response.data.results.map((item) => ({
      filename: item.filename,
      success: item.success,
      documentId: item.document_id,
      signedAt: item.signed_at,
      fileSize: item.file_size,
      error: item.error,
    })),
  };
};
