import { httpClient } from "./httpClient";
import type {
  CertificateImportResult,
  CertificateIssuePayload,
  CertificateIssueResult,
  CertificateRevokeResult,
  CertificateStatus,
  CertificateSummary,
  CrlGenerateResult,
  CrlMetadata,
} from "../types/ca";

type RawCertificateSummary = {
  certificate_id: string;
  serial_number: string;
  subject_common_name: string;
  status: CertificateStatus;
  issued_at: string;
  expires_at: string;
};

type CertificateListResponse = {
  certificates: RawCertificateSummary[];
};

type RawCertificateIssueResponse = {
  certificate_id: string;
  serial_number: string;
  status: CertificateStatus;
  issued_at: string;
  expires_at: string;
  certificate_pem: string;
  p12_bundle?: string | null;
};

type RawCertificateImportResponse = {
  certificate_id: string;
  serial_number: string;
  status: CertificateStatus;
  issued_at: string;
  expires_at: string;
  certificate_pem: string;
  p12_bundle?: string | null;
};

type RawCertificateRevokeResponse = {
  certificate_id: string;
  status: CertificateStatus;
  revoked_at: string;
};

type RawCrlMetadata = {
  artifact_id: string;
  name: string;
  created_at: string;
};

type CrlListResponse = {
  crls: RawCrlMetadata[];
};

type RawCrlGenerateResponse = {
  artifact_id: string;
  name: string;
  created_at: string;
  revoked_serials: string[];
  crl_pem: string;
};

const toDate = (value: string): Date => new Date(value);

const mapCertificateSummary = (certificate: RawCertificateSummary): CertificateSummary => ({
  id: certificate.certificate_id,
  serialNumber: certificate.serial_number,
  subjectCommonName: certificate.subject_common_name,
  status: certificate.status,
  issuedAt: toDate(certificate.issued_at),
  expiresAt: toDate(certificate.expires_at),
});

const mapCertificateIssueResult = (payload: RawCertificateIssueResponse): CertificateIssueResult => ({
  certificateId: payload.certificate_id,
  serialNumber: payload.serial_number,
  status: payload.status,
  issuedAt: toDate(payload.issued_at),
  expiresAt: toDate(payload.expires_at),
  certificatePem: payload.certificate_pem,
  p12Bundle: payload.p12_bundle ?? null,
});

const mapCertificateImportResult = (payload: RawCertificateImportResponse): CertificateImportResult => ({
  certificateId: payload.certificate_id,
  serialNumber: payload.serial_number,
  status: payload.status,
  issuedAt: toDate(payload.issued_at),
  expiresAt: toDate(payload.expires_at),
  certificatePem: payload.certificate_pem,
});

const mapCertificateRevokeResult = (payload: RawCertificateRevokeResponse): CertificateRevokeResult => ({
  certificateId: payload.certificate_id,
  status: payload.status,
  revokedAt: toDate(payload.revoked_at),
});

const mapCrlMetadata = (payload: RawCrlMetadata): CrlMetadata => ({
  artifactId: payload.artifact_id,
  name: payload.name,
  createdAt: toDate(payload.created_at),
});

const mapCrlGenerateResult = (payload: RawCrlGenerateResponse): CrlGenerateResult => ({
  artifactId: payload.artifact_id,
  name: payload.name,
  createdAt: toDate(payload.created_at),
  revokedSerials: payload.revoked_serials,
  crlPem: payload.crl_pem,
});

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

export const fetchCertificates = async (): Promise<CertificateSummary[]> => {
  const response = await httpClient.get<CertificateListResponse>("/api/v1/ca/certificates");
  return response.data.certificates.map(mapCertificateSummary);
};

export const issueCertificate = async (
  payload: CertificateIssuePayload
): Promise<CertificateIssueResult> => {
  const response = await httpClient.post<RawCertificateIssueResponse>("/api/v1/ca/certificates/issue", {
    common_name: payload.commonName,
    organization: payload.organization ?? null,
    algorithm: payload.algorithm,
    validity_days: payload.validityDays,
    p12_passphrase: payload.passphrase ?? null,
  });

  return mapCertificateIssueResult(response.data);
};

export const importCertificate = async (
  p12Bundle: string,
  passphrase: string | null
): Promise<CertificateImportResult> => {
  const response = await httpClient.post<RawCertificateImportResponse>("/api/v1/ca/certificates/import", {
    p12_bundle: p12Bundle,
    passphrase,
  });

  return mapCertificateImportResult(response.data);
};

export const revokeCertificate = async (certificateId: string): Promise<CertificateRevokeResult> => {
  const response = await httpClient.post<RawCertificateRevokeResponse>(
    `/api/v1/ca/certificates/${certificateId}/revoke`
  );

  return mapCertificateRevokeResult(response.data);
};

export const downloadCertificateBundle = async (
  certificateId: string
): Promise<{ blob: Blob; filename: string; contentType: string }> => {
  const response = await httpClient.get<ArrayBuffer>(
    `/api/v1/ca/certificates/${certificateId}/bundle`,
    {
      responseType: "arraybuffer",
    }
  );

  const contentType = response.headers["content-type"] ?? "application/x-pkcs12";
  const disposition = response.headers["content-disposition"];
  const filename = filenameFromDisposition(disposition) ?? `certificate-${certificateId}.p12`;
  const blob = new Blob([response.data], { type: contentType });

  return { blob, filename, contentType };
};

export const listCrls = async (): Promise<CrlMetadata[]> => {
  const response = await httpClient.get<CrlListResponse>("/api/v1/ca/crl");
  return response.data.crls.map(mapCrlMetadata);
};

export const generateCrl = async (): Promise<CrlGenerateResult> => {
  const response = await httpClient.post<RawCrlGenerateResponse>("/api/v1/ca/crl");
  return mapCrlGenerateResult(response.data);
};

export const downloadCrl = async (
  artifactId: string
): Promise<{ blob: Blob; filename: string; contentType: string }> => {
  const response = await httpClient.get<ArrayBuffer>(`/api/v1/ca/crl/${artifactId}`, {
    responseType: "arraybuffer",
  });

  const contentType = response.headers["content-type"] ?? "application/pkix-crl";
  const disposition = response.headers["content-disposition"];
  const filename =
    filenameFromDisposition(disposition) ?? `certificate-revocation-list-${artifactId}.crl`;
  const blob = new Blob([response.data], { type: contentType });

  return { blob, filename, contentType };
};
