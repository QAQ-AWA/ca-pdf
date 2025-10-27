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
  const inferredFilename =
    options.filename ?? ("name" in options.file ? (options.file as File).name : undefined) ?? "document.pdf";

  formData.append("pdf_file", options.file, inferredFilename);
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

  const response = await httpClient.post<ArrayBuffer>("/api/v1/pdf/sign", formData, {
    responseType: "arraybuffer",
  });

  const contentType = response.headers["content-type"] ?? "application/pdf";
  const disposition = response.headers["content-disposition"];
  const filename = filenameFromDisposition(disposition) ?? `signed-${inferredFilename}`;

  const blob = new Blob([response.data], { type: contentType });

  return {
    blob,
    filename,
    contentType,
    documentId: (response.headers["x-document-id"] as string | undefined) ?? null,
    signedAt: (response.headers["x-signed-at"] as string | undefined) ?? null,
    certificateId: (response.headers["x-certificate-id"] as string | undefined) ?? null,
    sealId: (response.headers["x-seal-id"] as string | undefined) ?? null,
    visibility: (response.headers["x-visibility"] as SignatureVisibility | undefined) ?? null,
    tsaUsed: response.headers["x-tsa-used"] === "true",
    ltvEmbedded: response.headers["x-ltv-embedded"] === "true",
  };
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
    const filename = entry.filename ?? ("name" in entry.file ? (entry.file as File).name : undefined) ?? `document-${index + 1}.pdf`;
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
