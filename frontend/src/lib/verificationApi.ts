import { httpClient } from "./httpClient";
import type { PdfVerificationReport, SignatureVerificationResult } from "../types/verification";

type RawSignatureResult = {
  field_name: string;
  valid: boolean;
  trusted: boolean;
  docmdp_ok: boolean | null;
  modification_level: string | null;
  signing_time: string | null;
  signer_common_name: string | null;
  signer_serial_number: string | null;
  summary: string;
  timestamp_trusted: boolean | null;
  timestamp_time: string | null;
  timestamp_summary: string | null;
  error: string | null;
};

type RawVerificationResponse = {
  total_signatures: number;
  valid_signatures: number;
  trusted_signatures: number;
  all_signatures_valid: boolean;
  all_signatures_trusted: boolean;
  signatures: RawSignatureResult[];
};

const parseDate = (value: string | null): Date | null => {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
};

const mapSignature = (payload: RawSignatureResult): SignatureVerificationResult => ({
  fieldName: payload.field_name,
  valid: payload.valid,
  trusted: payload.trusted,
  docmdpOk: payload.docmdp_ok,
  modificationLevel: payload.modification_level,
  signingTime: parseDate(payload.signing_time),
  signerCommonName: payload.signer_common_name,
  signerSerialNumber: payload.signer_serial_number,
  summary: payload.summary,
  timestampTrusted: payload.timestamp_trusted,
  timestampTime: parseDate(payload.timestamp_time),
  timestampSummary: payload.timestamp_summary,
  error: payload.error,
});

export const verifyPdf = async (file: Blob | File): Promise<PdfVerificationReport> => {
  const formData = new FormData();
  const filename =
    "name" in file && typeof (file as File).name === "string" && (file as File).name
      ? (file as File).name
      : "document.pdf";

  formData.append("pdf_file", file, filename);

  const response = await httpClient.post<RawVerificationResponse>("/api/v1/pdf/verify", formData);

  return {
    totalSignatures: response.data.total_signatures,
    validSignatures: response.data.valid_signatures,
    trustedSignatures: response.data.trusted_signatures,
    allSignaturesValid: response.data.all_signatures_valid,
    allSignaturesTrusted: response.data.all_signatures_trusted,
    signatures: response.data.signatures.map(mapSignature),
  };
};
