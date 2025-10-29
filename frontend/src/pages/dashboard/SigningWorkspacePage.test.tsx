import { vi } from "vitest";
import type { SpyInstance } from "vitest";
import AxiosMockAdapter from "axios-mock-adapter";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeProvider } from "../../components/ThemeProvider";
import { httpClient } from "../../lib/httpClient";
import { SigningWorkspacePage } from "./SigningWorkspacePage";

vi.mock("../../lib/pdfjs", () => {
  const createPage = () => ({
    getViewport: ({ scale }: { scale: number }) => ({
      width: 600 * scale,
      height: 800 * scale,
    }),
    render: () => ({
      promise: Promise.resolve(),
      cancel: vi.fn(),
    }),
  });

  return {
    getDocument: () => ({
      promise: Promise.resolve({
        numPages: 1,
        getPage: async () => createPage(),
      }),
    }),
  };
});

describe("SigningWorkspacePage", () => {
  let mock: AxiosMockAdapter;
  let user: ReturnType<typeof userEvent.setup>;
  let createObjectUrlSpy: SpyInstance;
  let revokeObjectUrlSpy: SpyInstance;

  beforeAll(() => {
    createObjectUrlSpy = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:preview");
    revokeObjectUrlSpy = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
  });

  beforeEach(() => {
    user = userEvent.setup();
    mock = new AxiosMockAdapter(httpClient);
    mock.onGet("/api/v1/pdf/seals").reply(200, { seals: [] });
  });

  afterEach(() => {
    mock.restore();
  });

  afterAll(() => {
    createObjectUrlSpy.mockRestore();
    revokeObjectUrlSpy.mockRestore();
  });

  const renderPage = () =>
    render(
      <ThemeProvider>
        <SigningWorkspacePage />
      </ThemeProvider>
    );

  const uploadSamplePdf = async () => {
    const file = new File([new Uint8Array([37, 80, 68, 70])], "contract.pdf", {
      type: "application/pdf",
    });

    const fileInput = screen.getByLabelText(/select pdf files/i);
    await user.upload(fileInput, file);
    expect(await screen.findByText(/contract\.pdf/i)).toBeInTheDocument();
    return file;
  };

  it("signs a queued document with a visible overlay", async () => {
    renderPage();
    await uploadSamplePdf();

    await user.click(screen.getByRole("button", { name: /add overlay/i }));
    expect(await screen.findByText(/signature 1/i)).toBeInTheDocument();

    const certificateField = screen.getByLabelText(/certificate id/i);
    await user.clear(certificateField);
    await user.type(certificateField, "cert-123");

    const responseBuffer = new ArrayBuffer(8);
    mock.onPost("/api/v1/pdf/sign").reply(200, responseBuffer, {
      "content-type": "application/pdf",
      "content-disposition": 'attachment; filename="contract-signed.pdf"',
    });

    await user.click(screen.getByRole("button", { name: /sign queued documents/i }));

    await waitFor(() => expect(mock.history.post.length).toBe(1));
    expect(await screen.findByText(/signed/i)).toBeInTheDocument();

    expect(screen.getByRole("button", { name: /download/i })).toBeInTheDocument();

    const requestData = mock.history.post[0].data as FormData;
    expect(requestData.get("certificate_id")).toBe("cert-123");
    expect(requestData.get("visibility")).toBe("visible");
    expect(Number(requestData.get("page"))).toBe(1);
    expect(Number(requestData.get("x"))).toBeCloseTo(120, 0);
    expect(Number(requestData.get("y"))).toBeCloseTo(496, 0);
    expect(Number(requestData.get("width"))).toBeCloseTo(180, 0);
    expect(Number(requestData.get("height"))).toBeCloseTo(144, 0);
  });

  it("shows a validation message when certificate ID is missing", async () => {
    renderPage();
    await uploadSamplePdf();

    await user.click(screen.getByRole("button", { name: /add overlay/i }));
    expect(await screen.findByText(/signature 1/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /sign queued documents/i }));

    expect(await screen.findByText(/provide a certificate id/i)).toBeInTheDocument();
    expect(mock.history.post.length).toBe(0);
  });

  it("surfaces API errors when signing fails", async () => {
    renderPage();
    await uploadSamplePdf();

    await user.click(screen.getByRole("button", { name: /add overlay/i }));
    expect(await screen.findByText(/signature 1/i)).toBeInTheDocument();

    const certificateField = screen.getByLabelText(/certificate id/i);
    await user.type(certificateField, "error-cert");

    mock.onPost("/api/v1/pdf/sign").reply(500);

    await user.click(screen.getByRole("button", { name: /sign queued documents/i }));

    expect(await screen.findByText(/error/i)).toBeInTheDocument();
    expect(screen.getByText(/failed to sign document/i)).toBeInTheDocument();
  });
});
