import "@testing-library/jest-dom/vitest";
import { vi } from "vitest";

const url = globalThis.URL;

if (url && !url.createObjectURL) {
  Object.defineProperty(url, "createObjectURL", {
    configurable: true,
    writable: true,
    value: vi.fn(() => "blob:mock-url"),
  });
}

if (url && !url.revokeObjectURL) {
  Object.defineProperty(url, "revokeObjectURL", {
    configurable: true,
    writable: true,
    value: vi.fn(),
  });
}

if (typeof File !== "undefined" && !(File.prototype as { arrayBuffer?: () => Promise<ArrayBuffer> }).arrayBuffer) {
  Object.defineProperty(File.prototype, "arrayBuffer", {
    configurable: true,
    writable: true,
    value: async function arrayBuffer(): Promise<ArrayBuffer> {
      return new ArrayBuffer(0);
    },
  });
}
