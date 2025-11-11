import { ChangeEvent, useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

import { PdfPreview } from "../../components/signing/PdfPreview";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { Spinner } from "../../components/ui/Spinner";
import { useTheme } from "../../components/ThemeProvider";
import { fileValidators } from "../../lib/fileValidators";
import { triggerFileDownload } from "../../lib/download";
import { listSeals } from "../../lib/sealApi";
import { signPdf } from "../../lib/signingApi";
import type { SealSummary } from "../../types/seal";
import type {
  PageDimension,
  SignatureMetadata,
  SignatureOverlay,
  SignaturePlacement,
  SignatureVisibility,
  SigningDocument,
} from "../../types/signing";

const MIN_SIZE_RATIO = 0.05;

const generateId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `id-${Math.random().toString(36).slice(2)}`;

const createDocument = (file: File): SigningDocument => ({
  id: generateId(),
  name: file.name,
  file,
  objectUrl: URL.createObjectURL(file),
  overlays: [],
  status: "draft",
  error: null,
  signedBlob: null,
  signedFilename: null,
  pageDimensions: [],
});

const createDefaultPlacement = (page: number): SignaturePlacement => ({
  page,
  left: 0.2,
  top: 0.2,
  width: 0.3,
  height: 0.18,
});

const sanitizeMetadataField = (value: string) => (value.trim() === "" ? undefined : value);

const visibilityOptions: Array<{ value: SignatureVisibility; label: string }> = [
  { value: "visible", label: "Visible" },
  { value: "invisible", label: "Invisible" },
];

const statusLabel: Record<SigningDocument["status"], string> = {
  draft: "Draft",
  signing: "Signing…",
  signed: "Signed",
  error: "Error",
};

const convertPlacementToCoordinates = (
  placement: SignaturePlacement,
  pages: PageDimension[]
): { page: number; x: number; y: number; width: number; height: number } => {
  const pageInfo = pages.find((page) => page.pageNumber === placement.page);
  if (!pageInfo) {
    throw new Error("Page metrics unavailable for selected page.");
  }

  const x = placement.left * pageInfo.widthPoints;
  const width = placement.width * pageInfo.widthPoints;
  const height = placement.height * pageInfo.heightPoints;
  const y = (1 - (placement.top + placement.height)) * pageInfo.heightPoints;

  return {
    page: placement.page,
    x,
    y,
    width,
    height,
  };
};

export const SigningWorkspacePage = () => {
  const theme = useTheme();
  const [documents, setDocuments] = useState<SigningDocument[]>([]);
  const [activeDocumentId, setActiveDocumentId] = useState<string | null>(null);
  const [activeOverlayId, setActiveOverlayId] = useState<string | null>(null);
  const [certificateId, setCertificateId] = useState("");
  const [useTsa, setUseTsa] = useState(false);
  const [embedLtv, setEmbedLtv] = useState(false);
  const [availableSeals, setAvailableSeals] = useState<SealSummary[]>([]);
  const [isLoadingSeals, setIsLoadingSeals] = useState(false);
  const [sealError, setSealError] = useState<string | null>(null);
  const [isSigning, setIsSigning] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string | null>(null);

  const documentsRef = useRef<SigningDocument[]>([]);

  useEffect(() => {
    documentsRef.current = documents;
  }, [documents]);

  useEffect(() => {
    let isMounted = true;
    const fetchSeals = async () => {
      setIsLoadingSeals(true);
      setSealError(null);
      try {
        const seals = await listSeals();
        if (isMounted) {
          setAvailableSeals(seals);
        }
      } catch (error) {
        if (!isMounted) {
          return;
        }
        const message = error instanceof Error ? error.message : "Failed to load seal images.";
        setSealError(message);
      } finally {
        if (isMounted) {
          setIsLoadingSeals(false);
        }
      }
    };

    void fetchSeals();

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    return () => {
      documentsRef.current.forEach((doc) => URL.revokeObjectURL(doc.objectUrl));
    };
  }, []);

  const activeDocument = useMemo(
    () => documents.find((document) => document.id === activeDocumentId) ?? null,
    [documents, activeDocumentId]
  );

  const activeOverlay = useMemo(() => {
    if (!activeDocument || !activeOverlayId) {
      return null;
    }
    return activeDocument.overlays.find((overlay) => overlay.id === activeOverlayId) ?? null;
  }, [activeDocument, activeOverlayId]);

  useEffect(() => {
    if (!activeDocument) {
      setActiveOverlayId(null);
      return;
    }

    if (!activeDocument.overlays.length) {
      setActiveOverlayId(null);
      return;
    }

    if (!activeOverlayId || !activeDocument.overlays.some((overlay) => overlay.id === activeOverlayId)) {
      setActiveOverlayId(activeDocument.overlays[0].id);
    }
  }, [activeDocument, activeOverlayId]);

  const updateDocument = (documentId: string, updater: (document: SigningDocument) => SigningDocument) => {
    setDocuments((prevDocuments) =>
      prevDocuments.map((document) => (document.id === documentId ? updater(document) : document))
    );
  };

  const updateOverlay = (
    documentId: string,
    overlayId: string,
    updater: (overlay: SignatureOverlay) => SignatureOverlay
  ) => {
    updateDocument(documentId, (document) => ({
      ...document,
      overlays: document.overlays.map((overlay) => (overlay.id === overlayId ? updater(overlay) : overlay)),
    }));
  };

  const handleFilesSelected = (event: ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files?.length) {
      return;
    }

    const nextDocuments: SigningDocument[] = [];
    let firstError: string | null = null;

    Array.from(files).forEach((file) => {
      const validationError = fileValidators.validatePDF(file);
      if (validationError) {
        if (!firstError) {
          firstError = validationError;
        }
        return;
      }
      nextDocuments.push(createDocument(file));
    });

    if (!nextDocuments.length) {
      setGlobalError(firstError ?? "Select PDF files to add them to the workspace queue.");
      event.target.value = "";
      return;
    }

    setDocuments((previous) => [...previous, ...nextDocuments]);
    setGlobalError(firstError);
    setActiveDocumentId((previousActive) => previousActive ?? nextDocuments[0]?.id ?? null);
    setActiveOverlayId(null);
    event.target.value = "";
  };

  const handleRemoveDocument = (documentId: string) => {
    setDocuments((prev) => {
      const toRemove = prev.find((document) => document.id === documentId);
      if (toRemove) {
        URL.revokeObjectURL(toRemove.objectUrl);
      }
      const remaining = prev.filter((document) => document.id !== documentId);
      if (!remaining.length) {
        setActiveDocumentId(null);
        setActiveOverlayId(null);
      } else if (documentId === activeDocumentId) {
        setActiveDocumentId(remaining[0].id);
      }
      return remaining;
    });
  };

  const handleAddOverlay = () => {
    if (!activeDocument) {
      return;
    }

    let createdOverlayId: string | null = null;
    updateDocument(activeDocument.id, (document) => {
      const overlayId = generateId();
      createdOverlayId = overlayId;
      const defaultPage = document.pageDimensions[0]?.pageNumber ?? 1;
      const newOverlay: SignatureOverlay = {
        id: overlayId,
        label: `Signature ${document.overlays.length + 1}`,
        visibility: "visible",
        sealId: null,
        metadata: {},
        placement: createDefaultPlacement(defaultPage),
      };

      return {
        ...document,
        overlays: [...document.overlays, newOverlay],
      };
    });

    if (createdOverlayId) {
      setActiveOverlayId(createdOverlayId);
    }
  };

  const handleRemoveOverlay = (overlayId: string) => {
    if (!activeDocument) {
      return;
    }

    let nextActiveOverlay: string | null = null;
    updateDocument(activeDocument.id, (document) => {
      const remaining = document.overlays.filter((overlay) => overlay.id !== overlayId);
      nextActiveOverlay = remaining[0]?.id ?? null;
      return {
        ...document,
        overlays: remaining,
      };
    });

    setActiveOverlayId((current) => (current === overlayId ? nextActiveOverlay : current));
  };

  const handleOverlayLabelChange = (overlayId: string, value: string) => {
    if (!activeDocument) {
      return;
    }
    updateOverlay(activeDocument.id, overlayId, (overlay) => ({
      ...overlay,
      label: value,
    }));
  };

  const handleOverlayVisibilityChange = (overlayId: string, value: SignatureVisibility) => {
    if (!activeDocument) {
      return;
    }

    updateOverlay(activeDocument.id, overlayId, (overlay) => ({
      ...overlay,
      visibility: value,
    }));
  };

  const handleOverlaySealChange = (overlayId: string, sealId: string) => {
    if (!activeDocument) {
      return;
    }
    updateOverlay(activeDocument.id, overlayId, (overlay) => ({
      ...overlay,
      sealId: sealId || null,
    }));
  };

  const handleOverlayPageChange = (overlayId: string, pageNumber: number) => {
    if (!activeDocument) {
      return;
    }

    updateOverlay(activeDocument.id, overlayId, (overlay) => ({
      ...overlay,
      placement: overlay.placement ? { ...overlay.placement, page: pageNumber } : createDefaultPlacement(pageNumber),
    }));
  };

  const handleOverlayMetadataChange = (overlayId: string, field: keyof SignatureMetadata, value: string) => {
    if (!activeDocument) {
      return;
    }

    updateOverlay(activeDocument.id, overlayId, (overlay) => ({
      ...overlay,
      metadata: {
        ...overlay.metadata,
        [field]: sanitizeMetadataField(value),
      },
    }));
  };

  const handleOverlayPlacementChange = (overlayId: string, placement: SignaturePlacement) => {
    if (!activeDocument) {
      return;
    }

    updateOverlay(activeDocument.id, overlayId, (overlay) => ({
      ...overlay,
      placement,
    }));
  };

  const handleOverlayPlacementFieldChange = (
    overlayId: string,
    field: "x" | "y" | "width" | "height",
    value: number
  ) => {
    if (!activeDocument) {
      return;
    }

    const overlay = activeDocument.overlays.find((item) => item.id === overlayId);
    if (!overlay?.placement) {
      return;
    }

    if (Number.isNaN(value)) {
      return;
    }

    const pageInfo = activeDocument.pageDimensions.find((page) => page.pageNumber === overlay.placement?.page);
    if (!pageInfo) {
      return;
    }

    const placement = overlay.placement;

    let nextPlacement: SignaturePlacement = placement;

    if (field === "x") {
      const normalized = Math.min(Math.max(value / pageInfo.widthPoints, 0), 1 - placement.width);
      nextPlacement = { ...placement, left: normalized };
    } else if (field === "width") {
      const normalized = Math.min(Math.max(value / pageInfo.widthPoints, MIN_SIZE_RATIO), 1 - placement.left);
      nextPlacement = { ...placement, width: normalized };
    } else if (field === "height") {
      const normalized = Math.min(Math.max(value / pageInfo.heightPoints, MIN_SIZE_RATIO), 1 - placement.top);
      nextPlacement = { ...placement, height: normalized };
    } else if (field === "y") {
      const bottomNormalized = Math.min(Math.max(value / pageInfo.heightPoints, 0), 1);
      const topNormalized = Math.min(Math.max(1 - bottomNormalized - placement.height, 0), 1 - placement.height);
      nextPlacement = { ...placement, top: topNormalized };
    }

    handleOverlayPlacementChange(overlayId, nextPlacement);
  };

  const handlePageMetricsUpdate = (documentId: string, metrics: PageDimension[]) => {
    updateDocument(documentId, (document) => ({
      ...document,
      pageDimensions: metrics,
    }));
  };

  const handleSignQueue = async () => {
    const trimmedCertificateId = certificateId.trim();
    if (!trimmedCertificateId) {
      setGlobalError("Provide a certificate ID before submitting signing requests.");
      return;
    }
    if (!documents.length) {
      setGlobalError("Add at least one PDF document to the queue before signing.");
      return;
    }

    setGlobalError(null);
    setIsSigning(true);
    try {
      for (const document of documents) {
        if (!document.overlays.length) {
          setDocuments((prev) =>
            prev.map((item) =>
              item.id === document.id
                ? {
                    ...item,
                    status: "error",
                    error: "Add at least one signature overlay before signing this document.",
                  }
                : item
            )
          );
          continue;
        }

        setDocuments((prev) =>
          prev.map((item) => (item.id === document.id ? { ...item, status: "signing", error: null } : item))
        );

        try {
          let currentBlob: Blob | File = document.file;
          let currentFilename = document.file.name;

          for (let index = 0; index < document.overlays.length; index += 1) {
            const overlay = document.overlays[index];
            setProgressMessage(`Signing ${document.name} (${index + 1}/${document.overlays.length})…`);

            if (overlay.visibility === "visible" && !overlay.placement) {
              throw new Error("Visible signatures require placement coordinates.");
            }

            const coordinates =
              overlay.visibility === "visible" && overlay.placement
                ? convertPlacementToCoordinates(overlay.placement, document.pageDimensions)
                : null;

            const result = await signPdf({
              file: currentBlob,
              filename: currentFilename,
              certificateId: trimmedCertificateId,
              sealId: overlay.sealId ?? undefined,
              visibility: overlay.visibility,
              coordinates: coordinates ?? undefined,
              metadata: overlay.metadata,
              useTsa,
              embedLtv,
            });

            currentBlob = result.blob;
            currentFilename = result.filename;
          }

          const finalBlob = currentBlob instanceof Blob ? currentBlob : new Blob([currentBlob]);

          try {
            triggerFileDownload(finalBlob, currentFilename);
          } catch (downloadError) {
            const message =
              downloadError instanceof Error
                ? downloadError.message
                : "Failed to trigger signed document download.";
            setGlobalError(message);
          }

          setDocuments((prev) =>
            prev.map((item) =>
              item.id === document.id
                ? {
                    ...item,
                    status: "signed",
                    signedBlob: finalBlob,
                    signedFilename: currentFilename,
                  }
                : item
            )
          );
        } catch (error) {
          let message = "Failed to sign document.";

          if (axios.isAxiosError(error)) {
            const data = error.response?.data as { code?: string; message?: string } | undefined;
            if (data?.code === "INVALID_FILE" && data.message) {
              message = data.message;
            } else if (data?.message) {
              message = data.message;
            }
          } else if (error instanceof Error) {
            message = error.message;
          }

          setDocuments((prev) =>
            prev.map((item) =>
              item.id === document.id ? { ...item, status: "error", error: message, signedBlob: null } : item
            )
          );
        }
      }
    } finally {
      setIsSigning(false);
      setProgressMessage(null);
    }
  };

  const renderOverlayList = () => {
    if (!activeDocument) {
      return <p style={{ margin: 0, color: theme.colors.muted }}>Select a document to configure signatures.</p>;
    }

    if (!activeDocument.overlays.length) {
      return <p style={{ margin: 0, color: theme.colors.muted }}>Add signature overlays to this document.</p>;
    }

    return (
      <div style={{ display: "grid", gap: theme.spacing.xs }}>
        {activeDocument.overlays.map((overlay) => (
          <button
            key={overlay.id}
            type="button"
            onClick={() => setActiveOverlayId(overlay.id)}
            style={
              overlay.id === activeOverlayId
                ? {
                    padding: theme.spacing.sm,
                    borderRadius: theme.borderRadius,
                    background: theme.colors.primary,
                    color: "#fff",
                    border: "none",
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    textAlign: "left",
                  }
                : {
                    padding: theme.spacing.sm,
                    borderRadius: theme.borderRadius,
                    background: theme.colors.surface,
                    border: `1px solid ${theme.colors.muted}`,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    textAlign: "left",
                  }
            }
          >
            <span>{overlay.label}</span>
            <span style={{ fontSize: theme.font.size.xs, opacity: 0.8 }}>{overlay.visibility}</span>
          </button>
        ))}
      </div>
    );
  };

  const renderOverlayEditor = () => {
    if (!activeDocument || !activeOverlay) {
      return null;
    }

    const pageDimensions = activeDocument.pageDimensions;
    const placement = activeOverlay.placement ?? createDefaultPlacement(pageDimensions[0]?.pageNumber ?? 1);
    const currentPageInfo = pageDimensions.find((page) => page.pageNumber === placement.page) ?? pageDimensions[0];

    const coordinateInputsDisabled = activeOverlay.visibility !== "visible" || !currentPageInfo;

    const xPoints = currentPageInfo ? placement.left * currentPageInfo.widthPoints : 0;
    const widthPoints = currentPageInfo ? placement.width * currentPageInfo.widthPoints : 0;
    const heightPoints = currentPageInfo ? placement.height * currentPageInfo.heightPoints : 0;
    const yPoints = currentPageInfo ? (1 - (placement.top + placement.height)) * currentPageInfo.heightPoints : 0;

    return (
      <div style={{ display: "grid", gap: theme.spacing.md }}>
        <Input
          label="Overlay label"
          value={activeOverlay.label}
          onChange={(event) => handleOverlayLabelChange(activeOverlay.id, event.target.value)}
        />

        <label style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>Visibility</span>
          <select
            value={activeOverlay.visibility}
            onChange={(event) => handleOverlayVisibilityChange(activeOverlay.id, event.target.value as SignatureVisibility)}
            style={{
              padding: theme.spacing.sm,
              borderRadius: theme.borderRadius,
              border: `1px solid ${theme.colors.muted}`,
            }}
          >
            {visibilityOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>Seal (optional)</span>
          <select
            value={activeOverlay.sealId ?? ""}
            onChange={(event) => handleOverlaySealChange(activeOverlay.id, event.target.value)}
            style={{
              padding: theme.spacing.sm,
              borderRadius: theme.borderRadius,
              border: `1px solid ${theme.colors.muted}`,
            }}
          >
            <option value="">No seal</option>
            {availableSeals.map((seal) => (
              <option key={seal.id} value={seal.id}>
                {seal.name}
              </option>
            ))}
          </select>
          {sealError ? <span style={{ color: theme.colors.danger, fontSize: theme.font.size.xs }}>{sealError}</span> : null}
          {isLoadingSeals ? (
            <span style={{ color: theme.colors.muted, fontSize: theme.font.size.xs }}>Loading seals…</span>
          ) : null}
        </label>

        <label style={{ display: "grid", gap: theme.spacing.xs }}>
          <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>Page</span>
          <select
            value={placement.page}
            onChange={(event) => handleOverlayPageChange(activeOverlay.id, Number.parseInt(event.target.value, 10))}
            style={{
              padding: theme.spacing.sm,
              borderRadius: theme.borderRadius,
              border: `1px solid ${theme.colors.muted}`,
            }}
          >
            {pageDimensions.map((page) => (
              <option key={page.pageNumber} value={page.pageNumber}>
                Page {page.pageNumber}
              </option>
            ))}
          </select>
        </label>

        <div style={{ display: "grid", gap: theme.spacing.sm, gridTemplateColumns: "repeat(2, minmax(0, 1fr))" }}>
          <Input
            label="X position"
            type="number"
            value={Number.isFinite(xPoints) ? Math.round(xPoints) : ""}
            onChange={(event) => handleOverlayPlacementFieldChange(activeOverlay.id, "x", Number(event.target.value))}
            disabled={coordinateInputsDisabled}
          />
          <Input
            label="Y position"
            type="number"
            value={Number.isFinite(yPoints) ? Math.round(yPoints) : ""}
            onChange={(event) => handleOverlayPlacementFieldChange(activeOverlay.id, "y", Number(event.target.value))}
            disabled={coordinateInputsDisabled}
          />
          <Input
            label="Width"
            type="number"
            value={Number.isFinite(widthPoints) ? Math.round(widthPoints) : ""}
            onChange={(event) => handleOverlayPlacementFieldChange(activeOverlay.id, "width", Number(event.target.value))}
            disabled={coordinateInputsDisabled}
          />
          <Input
            label="Height"
            type="number"
            value={Number.isFinite(heightPoints) ? Math.round(heightPoints) : ""}
            onChange={(event) => handleOverlayPlacementFieldChange(activeOverlay.id, "height", Number(event.target.value))}
            disabled={coordinateInputsDisabled}
          />
        </div>

        <Input
          label="Reason"
          value={activeOverlay.metadata.reason ?? ""}
          onChange={(event) => handleOverlayMetadataChange(activeOverlay.id, "reason", event.target.value)}
        />
        <Input
          label="Location"
          value={activeOverlay.metadata.location ?? ""}
          onChange={(event) => handleOverlayMetadataChange(activeOverlay.id, "location", event.target.value)}
        />
        <Input
          label="Contact info"
          value={activeOverlay.metadata.contactInfo ?? ""}
          onChange={(event) => handleOverlayMetadataChange(activeOverlay.id, "contactInfo", event.target.value)}
        />

        <Button variant="secondary" onClick={() => handleRemoveOverlay(activeOverlay.id)}>
          Remove overlay
        </Button>
      </div>
    );
  };

  const renderQueue = () => {
    if (!documents.length) {
      return <p style={{ margin: 0, color: theme.colors.muted }}>Upload PDF documents to build the signing queue.</p>;
    }

    return (
      <div style={{ display: "grid", gap: theme.spacing.sm }}>
        {documents.map((document) => (
          <div
            key={document.id}
            style={{
              border: `1px solid ${document.id === activeDocumentId ? theme.colors.primary : theme.colors.muted}`,
              borderRadius: theme.borderRadius,
              padding: theme.spacing.md,
              display: "grid",
              gap: theme.spacing.xs,
              background: document.id === activeDocumentId ? "rgba(37, 99, 235, 0.08)" : theme.colors.surface,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong>{document.name}</strong>
              <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>{statusLabel[document.status]}</span>
            </div>
            <div style={{ display: "flex", gap: theme.spacing.sm }}>
              <Button variant="ghost" onClick={() => setActiveDocumentId(document.id)}>
                View
              </Button>
              <Button variant="ghost" onClick={() => handleRemoveDocument(document.id)}>
                Remove
              </Button>
              {document.status === "signed" && document.signedBlob ? (
                <Button
                  onClick={() =>
                    triggerFileDownload(
                      document.signedBlob,
                      document.signedFilename ?? document.name.replace(/\.pdf$/i, "-signed.pdf")
                    )
                  }
                >
                  Download
                </Button>
              ) : null}
            </div>
            {document.status === "error" && document.error ? (
              <span style={{ color: theme.colors.danger, fontSize: theme.font.size.xs }}>{document.error}</span>
            ) : null}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <header style={{ display: "flex", flexDirection: "column", gap: theme.spacing.xs }}>
        <h2 style={{ margin: 0 }}>Signing workspace</h2>
        <p style={{ margin: 0, color: theme.colors.muted }}>
          Upload PDF documents, place signature overlays, and process signing requests with full visibility into
          progress and results.
        </p>
      </header>

      <div style={{ display: "grid", gap: theme.spacing.xl, gridTemplateColumns: "minmax(0, 2fr) minmax(0, 1fr)" }}>
        <div style={{ display: "grid", gap: theme.spacing.lg }}>
          <Card title="Upload documents">
            <label style={{ display: "grid", gap: theme.spacing.xs }}>
              <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>
                Select PDF files
              </span>
              <input type="file" accept="application/pdf" multiple onChange={handleFilesSelected} />
            </label>
            <span style={{ fontSize: theme.font.size.xs, color: theme.colors.muted }}>
              Upload one or more PDF files to queue them for signing. Each document can contain multiple signature overlays.
            </span>
          </Card>

          {activeDocument ? (
            <PdfPreview
              documentId={activeDocument.id}
              file={activeDocument.file}
              overlays={activeDocument.overlays}
              activeOverlayId={activeOverlayId}
              onOverlayPlacementChange={(overlayId, placement) => handleOverlayPlacementChange(overlayId, placement)}
              onOverlayActivate={(overlayId) => setActiveOverlayId(overlayId)}
              onPageMetrics={(metrics) => handlePageMetricsUpdate(activeDocument.id, metrics)}
            />
          ) : (
            <Card>
              <p style={{ margin: 0, color: theme.colors.muted }}>
                Upload a PDF document to start configuring signature overlays.
              </p>
            </Card>
          )}
        </div>

        <aside style={{ display: "grid", gap: theme.spacing.lg }}>
          <Card title="Batch queue">{renderQueue()}</Card>

          <Card
            title="Signature overlays"
            action={
              <Button variant="ghost" onClick={handleAddOverlay} disabled={!activeDocument}>
                Add overlay
              </Button>
            }
          >
            {renderOverlayList()}
            {renderOverlayEditor()}
          </Card>

          <Card title="Signing settings">
            <Input
              label="Certificate ID"
              value={certificateId}
              onChange={(event) => setCertificateId(event.target.value)}
              placeholder="e.g. 92d5c0d8-5598-4c8b-91bd-80a7ba14a818"
            />

            <label style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
              <input type="checkbox" checked={useTsa} onChange={(event) => setUseTsa(event.target.checked)} />
              <span>Include RFC3161 timestamp</span>
            </label>

            <label style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
              <input type="checkbox" checked={embedLtv} onChange={(event) => setEmbedLtv(event.target.checked)} />
              <span>Embed LTV validation material</span>
            </label>

            {globalError ? <span style={{ color: theme.colors.danger }}>{globalError}</span> : null}
            {progressMessage ? <span style={{ color: theme.colors.muted }}>{progressMessage}</span> : null}

            <Button onClick={handleSignQueue} disabled={isSigning}>
              {isSigning ? (
                <>
                  <Spinner size={18} /> Signing…
                </>
              ) : (
                "Sign queued documents"
              )}
            </Button>
          </Card>
        </aside>
      </div>
    </div>
  );
};
