export type SignatureVisibility = "visible" | "invisible";

export type SignatureMetadata = {
  reason?: string;
  location?: string;
  contactInfo?: string;
};

export type SignaturePlacement = {
  page: number;
  left: number;
  top: number;
  width: number;
  height: number;
};

export type SignatureOverlay = {
  id: string;
  label: string;
  visibility: SignatureVisibility;
  sealId: string | null;
  metadata: SignatureMetadata;
  placement: SignaturePlacement | null;
};

export type SigningDocumentStatus = "draft" | "signing" | "signed" | "error";

export type PageDimension = {
  pageNumber: number;
  width: number;
  height: number;
  widthPoints: number;
  heightPoints: number;
};

export type SigningDocument = {
  id: string;
  name: string;
  file: File;
  objectUrl: string;
  overlays: SignatureOverlay[];
  status: SigningDocumentStatus;
  error?: string | null;
  signedBlob?: Blob | null;
  signedFilename?: string | null;
  pageDimensions: PageDimension[];
};
