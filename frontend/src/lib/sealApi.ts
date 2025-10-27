import { httpClient } from "./httpClient";
import type { SealSummary, SealUploadPayload } from "../types/seal";

type RawSeal = {
  seal_id: string;
  name: string;
  description?: string | null;
  content_type: string;
  size_bytes: number;
  created_at: string;
  updated_at: string;
  download_url?: string | null;
};

type SealListResponse = {
  seals: RawSeal[];
};

type RawSealResponse = RawSeal;

const toDate = (value: string): Date => new Date(value);

const mapSeal = (raw: RawSeal): SealSummary => ({
  id: raw.seal_id,
  name: raw.name,
  description: raw.description ?? null,
  contentType: raw.content_type,
  sizeBytes: raw.size_bytes,
  createdAt: toDate(raw.created_at),
  updatedAt: toDate(raw.updated_at),
  downloadUrl: raw.download_url ?? null,
});

export const listSeals = async (): Promise<SealSummary[]> => {
  const response = await httpClient.get<SealListResponse>("/api/v1/pdf/seals");
  return response.data.seals.map(mapSeal);
};

export const uploadSeal = async (payload: SealUploadPayload): Promise<SealSummary> => {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("name", payload.name);
  if (payload.description) {
    formData.append("description", payload.description);
  }

  const response = await httpClient.post<RawSealResponse>("/api/v1/pdf/seals", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return mapSeal(response.data);
};

export const deleteSeal = async (sealId: string): Promise<void> => {
  await httpClient.delete(`/api/v1/pdf/seals/${sealId}`);
};

export const downloadSealImage = async (
  sealId: string
): Promise<{ blob: Blob; filename: string; contentType: string }> => {
  const response = await httpClient.get<ArrayBuffer>(`/api/v1/pdf/seals/${sealId}/image`, {
    responseType: "arraybuffer",
  });

  const contentType = response.headers["content-type"] ?? "application/octet-stream";
  const filename = `seal-${sealId}.${contentType === "image/svg+xml" ? "svg" : "png"}`;
  const blob = new Blob([response.data], { type: contentType });

  return { blob, filename, contentType };
};
