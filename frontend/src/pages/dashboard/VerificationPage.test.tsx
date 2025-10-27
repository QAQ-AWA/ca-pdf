import AxiosMockAdapter from "axios-mock-adapter";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeProvider } from "../../components/ThemeProvider";
import { httpClient } from "../../lib/httpClient";
import { VerificationPage } from "./VerificationPage";

describe("VerificationPage", () => {
  let mock: AxiosMockAdapter;
  let user: ReturnType<typeof userEvent.setup>;

  beforeEach(() => {
    user = userEvent.setup();
    mock = new AxiosMockAdapter(httpClient);
  });

  afterEach(() => {
    mock.restore();
  });

  const renderPage = () =>
    render(
      <ThemeProvider>
        <VerificationPage />
      </ThemeProvider>
    );

  const uploadPdf = async () => {
    const file = new File([new Uint8Array([37, 80, 68, 70])], "signed.pdf", { type: "application/pdf" });
    const input = screen.getByLabelText(/select signed pdf/i) as HTMLInputElement;
    await user.upload(input, file);
    return file;
  };

  it("displays verification results from the backend", async () => {
    mock.onPost("/api/v1/pdf/verify").reply(200, {
      total_signatures: 2,
      valid_signatures: 1,
      trusted_signatures: 1,
      all_signatures_valid: false,
      all_signatures_trusted: false,
      signatures: [
        {
          field_name: "Signature 1",
          valid: true,
          trusted: true,
          docmdp_ok: true,
          modification_level: "No changes",
          signing_time: "2024-05-01T12:00:00Z",
          signer_common_name: "Alice Example",
          signer_serial_number: "1234",
          summary: "Signature is cryptographically valid.",
          timestamp_trusted: true,
          timestamp_time: "2024-05-01T12:05:00Z",
          timestamp_summary: "Timestamp validated successfully.",
          error: null,
        },
        {
          field_name: "Signature 2",
          valid: false,
          trusted: false,
          docmdp_ok: false,
          modification_level: "Document changed",
          signing_time: null,
          signer_common_name: null,
          signer_serial_number: null,
          summary: "Signature is invalid.",
          timestamp_trusted: null,
          timestamp_time: null,
          timestamp_summary: null,
          error: "Certificate revoked",
        },
      ],
    });

    renderPage();
    await uploadPdf();

    await user.click(screen.getByRole("button", { name: /verify signatures/i }));

    await waitFor(() => expect(mock.history.post.length).toBe(1));

    expect(await screen.findByText(/trusted signatures/i)).toBeInTheDocument();
    expect(screen.getByText(/Signature is cryptographically valid/i)).toBeInTheDocument();
    expect(screen.getByText(/Signature is invalid/i)).toBeInTheDocument();
    expect(screen.getByText(/Timestamp validated successfully/i)).toBeInTheDocument();
    expect(screen.getByText(/Certificate revoked/i)).toBeInTheDocument();
    expect(screen.getByText(/Last verified file: signed.pdf/i)).toBeInTheDocument();
  });

  it("surfaces backend errors", async () => {
    mock.onPost("/api/v1/pdf/verify").reply(500);

    renderPage();
    await uploadPdf();

    await user.click(screen.getByRole("button", { name: /verify signatures/i }));

    expect(await screen.findByText(/verification failed/i)).toBeInTheDocument();
  });
});
