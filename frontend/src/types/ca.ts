export type CertificateStatus = "active" | "revoked" | "expired" | "pending";

export type CertificateSummary = {
  id: string;
  serialNumber: string;
  subjectCommonName: string;
  status: CertificateStatus;
  issuedAt: Date;
  expiresAt: Date;
};

export type CertificateIssuePayload = {
  commonName: string;
  organization?: string | null;
  algorithm: "rsa-2048" | "ec-p256";
  validityDays: number;
  passphrase?: string | null;
};

export type CertificateIssueResult = {
  certificateId: string;
  serialNumber: string;
  status: CertificateStatus;
  issuedAt: Date;
  expiresAt: Date;
  certificatePem: string;
  p12Bundle?: string | null;
};

export type CertificateImportResult = {
  certificateId: string;
  serialNumber: string;
  status: CertificateStatus;
  issuedAt: Date;
  expiresAt: Date;
  certificatePem: string;
};

export type CertificateRevokeResult = {
  certificateId: string;
  status: CertificateStatus;
  revokedAt: Date;
};

export type CrlMetadata = {
  artifactId: string;
  name: string;
  createdAt: Date;
};

export type CrlGenerateResult = {
  artifactId: string;
  name: string;
  createdAt: Date;
  revokedSerials: string[];
  crlPem: string;
};
