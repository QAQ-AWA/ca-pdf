export type SealSummary = {
  id: string;
  name: string;
  description?: string | null;
  contentType: string;
  sizeBytes: number;
  createdAt: Date;
  updatedAt: Date;
  downloadUrl?: string | null;
};

export type SealUploadPayload = {
  file: File;
  name: string;
  description?: string;
};
