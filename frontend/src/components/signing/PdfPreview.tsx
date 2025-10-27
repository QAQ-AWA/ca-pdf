import { memo, useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { CSSProperties, PointerEvent as ReactPointerEvent } from "react";

import { getDocument } from "../../lib/pdfjs";
import type { PageViewport, PDFPageProxy, RenderTask } from "../../lib/pdfjs";
import type { PageDimension, SignatureOverlay, SignaturePlacement } from "../../types/signing";
import { useTheme } from "../ThemeProvider";

const DISPLAY_SCALE = 1.5;
const MIN_SIZE_RATIO = 0.05;

const clamp = (value: number, min: number, max: number) => Math.min(Math.max(value, min), max);

type PdfPreviewProps = {
  documentId: string;
  file: File;
  overlays: SignatureOverlay[];
  activeOverlayId: string | null;
  onOverlayPlacementChange: (overlayId: string, placement: SignaturePlacement) => void;
  onOverlayActivate: (overlayId: string) => void;
  onPageMetrics: (pages: PageDimension[]) => void;
};

type PageRenderRecord = {
  pageNumber: number;
  width: number;
  height: number;
  widthPoints: number;
  heightPoints: number;
};

type Interaction = {
  overlayId: string;
  pageNumber: number;
  startX: number;
  startY: number;
  initialPlacement: SignaturePlacement;
  mode: "move" | "resize";
};

type PdfPageResources = {
  page: PDFPageProxy;
  baseViewport: PageViewport;
  renderViewport: PageViewport;
  renderTask?: RenderTask;
};

const toPageDimension = (record: PageRenderRecord): PageDimension => ({
  pageNumber: record.pageNumber,
  width: record.width,
  height: record.height,
  widthPoints: record.widthPoints,
  heightPoints: record.heightPoints,
});

const PdfPreviewComponent = ({
  documentId,
  file,
  overlays,
  activeOverlayId,
  onOverlayPlacementChange,
  onOverlayActivate,
  onPageMetrics,
}: PdfPreviewProps) => {
  const theme = useTheme();
  const [pages, setPages] = useState<PageRenderRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canvasRefs = useRef<Map<number, HTMLCanvasElement>>(new Map());
  const pageContainerRefs = useRef<Map<number, HTMLDivElement>>(new Map());
  const pdfResources = useRef<Map<number, PdfPageResources>>(new Map());
  const interactionRef = useRef<Interaction | null>(null);

  const reset = useCallback(() => {
    pdfResources.current.forEach((resource) => resource.renderTask?.cancel());
    pdfResources.current.clear();
    canvasRefs.current.forEach((canvas) => {
      const context = canvas.getContext("2d");
      if (context) {
        context.clearRect(0, 0, canvas.width, canvas.height);
      }
    });
    setPages([]);
    onPageMetrics([]);
  }, [onPageMetrics]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      reset();

      try {
        const data = await file.arrayBuffer();
        const loadingTask = getDocument({ data });
        const pdf = await loadingTask.promise;
        if (cancelled) {
          return;
        }

        const nextPages: PageRenderRecord[] = [];
        for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
          const page = await pdf.getPage(pageNumber);
          if (cancelled) {
            return;
          }

          const baseViewport = page.getViewport({ scale: 1 });
          const renderViewport = page.getViewport({ scale: DISPLAY_SCALE });

          pdfResources.current.set(pageNumber, {
            page,
            baseViewport,
            renderViewport,
          });

          nextPages.push({
            pageNumber,
            width: renderViewport.width,
            height: renderViewport.height,
            widthPoints: baseViewport.width,
            heightPoints: baseViewport.height,
          });
        }

        if (cancelled) {
          return;
        }

        setPages(nextPages);
        onPageMetrics(nextPages.map(toPageDimension));
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        const message =
          loadError instanceof Error ? loadError.message : "Unable to render PDF preview. Please try another file.";
        setError(message);
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
      reset();
    };
  }, [documentId, file, onPageMetrics, reset]);

  useEffect(() => {
    const render = async () => {
      for (const pageRecord of pages) {
        const canvas = canvasRefs.current.get(pageRecord.pageNumber);
        const resources = pdfResources.current.get(pageRecord.pageNumber);
        if (!canvas || !resources) {
          continue;
        }

        const context = canvas.getContext("2d");
        if (!context) {
          continue;
        }

        canvas.width = resources.renderViewport.width;
        canvas.height = resources.renderViewport.height;

        try {
          const view = resources.page.render({
            canvasContext: context,
            viewport: resources.renderViewport,
          });
          resources.renderTask = view;
          await view.promise;
        } catch (renderError) {
          if (import.meta.env.DEV) {
            console.warn("Failed to render PDF page", renderError);
          }
        }
      }
    };

    void render();
  }, [pages]);

  const handleOverlayPointerDown = useCallback(
    (overlay: SignatureOverlay, mode: Interaction["mode"], event: ReactPointerEvent<HTMLDivElement>) => {
      if (!overlay.placement) {
        return;
      }
      const pageInfo = pages.find((page) => page.pageNumber === overlay.placement?.page);
      if (!pageInfo || !pageContainerRefs.current.has(overlay.placement.page)) {
        return;
      }

      event.preventDefault();
      event.stopPropagation();

      onOverlayActivate(overlay.id);

      const interaction: Interaction = {
        overlayId: overlay.id,
        pageNumber: overlay.placement.page,
        startX: event.clientX,
        startY: event.clientY,
        initialPlacement: overlay.placement,
        mode,
      };

      interactionRef.current = interaction;

      const handlePointerMove = (moveEvent: PointerEvent) => {
        const currentInteraction = interactionRef.current;
        if (!currentInteraction) {
          return;
        }

        const currentPage = pages.find((page) => page.pageNumber === currentInteraction.pageNumber);
        if (!currentPage) {
          return;
        }

        const deltaX = moveEvent.clientX - currentInteraction.startX;
        const deltaY = moveEvent.clientY - currentInteraction.startY;

        const width = currentPage.width;
        const height = currentPage.height;

        if (currentInteraction.mode === "move") {
          const nextLeft = clamp(
            currentInteraction.initialPlacement.left + deltaX / width,
            0,
            1 - currentInteraction.initialPlacement.width
          );
          const nextTop = clamp(
            currentInteraction.initialPlacement.top + deltaY / height,
            0,
            1 - currentInteraction.initialPlacement.height
          );

          onOverlayPlacementChange(currentInteraction.overlayId, {
            ...currentInteraction.initialPlacement,
            left: nextLeft,
            top: nextTop,
          });
        } else {
          const nextWidth = clamp(
            currentInteraction.initialPlacement.width + deltaX / width,
            MIN_SIZE_RATIO,
            1 - currentInteraction.initialPlacement.left
          );
          const nextHeight = clamp(
            currentInteraction.initialPlacement.height + deltaY / height,
            MIN_SIZE_RATIO,
            1 - currentInteraction.initialPlacement.top
          );

          onOverlayPlacementChange(currentInteraction.overlayId, {
            ...currentInteraction.initialPlacement,
            width: nextWidth,
            height: nextHeight,
          });
        }
      };

      const handlePointerUp = () => {
        interactionRef.current = null;
        window.removeEventListener("pointermove", handlePointerMove);
        window.removeEventListener("pointerup", handlePointerUp);
      };

      window.addEventListener("pointermove", handlePointerMove);
      window.addEventListener("pointerup", handlePointerUp);
    },
    [onOverlayActivate, onOverlayPlacementChange, pages]
  );

  useEffect(() => {
    return () => {
      interactionRef.current = null;
    };
  }, []);

  const pageElements = useMemo(() => {
    return pages.map((page) => {
      const overlaysForPage = overlays.filter(
        (overlay) => overlay.placement?.page === page.pageNumber && overlay.visibility === "visible"
      );

      return (
        <div
          key={page.pageNumber}
          ref={(element: HTMLDivElement | null) => {
            if (element) {
              pageContainerRefs.current.set(page.pageNumber, element);
            } else {
              pageContainerRefs.current.delete(page.pageNumber);
            }
          }}
          style={{
            position: "relative",
            width: page.width,
            height: page.height,
            border: `1px solid ${theme.colors.muted}`,
            borderRadius: theme.borderRadius,
            background: theme.colors.surface,
            overflow: "hidden",
          }}
        >
          <canvas
            ref={(element: HTMLCanvasElement | null) => {
              if (element) {
                canvasRefs.current.set(page.pageNumber, element);
              } else {
                canvasRefs.current.delete(page.pageNumber);
              }
            }}
            style={{ display: "block", width: "100%", height: "100%" }}
          />

          {overlaysForPage.map((overlay) => {
            if (!overlay.placement) {
              return null;
            }

            const isActive = overlay.id === activeOverlayId;
            const placement = overlay.placement;

            const style: CSSProperties = {
              position: "absolute",
              left: placement.left * page.width,
              top: placement.top * page.height,
              width: placement.width * page.width,
              height: placement.height * page.height,
              borderRadius: theme.borderRadius,
              border: `2px solid ${isActive ? theme.colors.primary : theme.colors.secondary}`,
              background: isActive ? "rgba(37, 99, 235, 0.12)" : "rgba(100, 116, 139, 0.1)",
              color: theme.colors.text,
              cursor: "move",
              userSelect: "none",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: theme.font.size.sm,
            };

            return (
              <div
                key={overlay.id}
                role="button"
                tabIndex={0}
                onClick={() => onOverlayActivate(overlay.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onOverlayActivate(overlay.id);
                  }
                }}
                onPointerDown={(event) => handleOverlayPointerDown(overlay, "move", event)}
                style={style}
              >
                <span>{overlay.label}</span>
                <div
                  aria-hidden
                  onPointerDown={(event) => handleOverlayPointerDown(overlay, "resize", event)}
                  style={{
                    position: "absolute",
                    width: 14,
                    height: 14,
                    right: -7,
                    bottom: -7,
                    borderRadius: "50%",
                    background: theme.colors.primary,
                    border: `2px solid ${theme.colors.surface}`,
                    cursor: "nwse-resize",
                  }}
                />
              </div>
            );
          })}
        </div>
      );
    });
  }, [activeOverlayId, overlays, pages, theme, handleOverlayPointerDown, onOverlayActivate]);

  return (
    <div
      style={{
        position: "relative",
        padding: theme.spacing.md,
        borderRadius: theme.borderRadius,
        background: theme.colors.surface,
        border: `1px solid ${theme.colors.muted}`,
        overflowY: "auto",
        maxHeight: "calc(100vh - 220px)",
      }}
    >
      {isLoading ? (
        <p style={{ margin: 0, color: theme.colors.muted }}>Rendering PDF preview…</p>
      ) : null}
      {error ? (
        <p style={{ margin: 0, color: theme.colors.danger }}>{error}</p>
      ) : (
        <div style={{ display: "grid", gap: theme.spacing.md }}>{pageElements}</div>
      )}
    </div>
  );
};

export const PdfPreview = memo(PdfPreviewComponent);
