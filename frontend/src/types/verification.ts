export type SignatureVerificationResult = {
  fieldName: string;
  valid: boolean;
  trusted: boolean;
  docmdpOk: boolean | null;
  modificationLevel: string | null;
  signingTime: Date | null;
  signerCommonName: string | null;
  signerSerialNumber: string | null;
  summary: string;
  timestampTrusted: boolean | null;
  timestampTime: Date | null;
  timestampSummary: string | null;
  error: string | null;
};

export type PdfVerificationReport = {
  totalSignatures: number;
  validSignatures: number;
  trustedSignatures: number;
  allSignaturesValid: boolean;
  allSignaturesTrusted: boolean;
  signatures: SignatureVerificationResult[];
};
