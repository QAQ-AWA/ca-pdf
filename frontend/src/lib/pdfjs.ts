import { GlobalWorkerOptions, getDocument } from "pdfjs-dist";
import type { PDFDocumentProxy, PDFPageProxy, PageViewport, RenderTask } from "pdfjs-dist/types/src/display/api";
import workerSrc from "pdfjs-dist/build/pdf.worker.min.js?url";

if (typeof window !== "undefined") {
  GlobalWorkerOptions.workerSrc = workerSrc;
}

export { getDocument };
export type { PDFDocumentProxy, PDFPageProxy, PageViewport, RenderTask };
