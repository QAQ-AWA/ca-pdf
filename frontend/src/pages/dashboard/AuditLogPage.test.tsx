import AxiosMockAdapter from "axios-mock-adapter";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeProvider } from "../../components/ThemeProvider";
import { httpClient } from "../../lib/httpClient";
import { AuditLogPage } from "./AuditLogPage";

describe("AuditLogPage", () => {
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
        <AuditLogPage />
      </ThemeProvider>
    );

  it("renders audit entries and shows detail modal", async () => {
    mock.onGet("/api/v1/audit/logs").reply(200, {
      total: 2,
      limit: 100,
      offset: 0,
      logs: [
        {
          id: "1",
          actor_id: 42,
          event_type: "pdf.signature.applied",
          resource: "pdf",
          ip_address: "192.168.1.5",
          user_agent: "Mozilla/5.0",
          metadata: { document_id: "abc" },
          message: "Signature created",
          created_at: "2024-05-01T12:00:00Z",
        },
        {
          id: "2",
          actor_id: null,
          event_type: "auth.login",
          resource: "auth",
          ip_address: null,
          user_agent: null,
          metadata: null,
          message: null,
          created_at: "2024-05-01T10:00:00Z",
        },
      ],
    });

    renderPage();

    expect(await screen.findByText(/pdf.signature.applied/)).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: /view details/i })[0]);

    expect(await screen.findByText(/Signature created/)).toBeInTheDocument();
    expect(screen.getByText(/document_id/)).toBeInTheDocument();
  });

  it("applies filters and forwards them to the backend", async () => {
    mock.onGet("/api/v1/audit/logs").replyOnce(200, {
      total: 1,
      limit: 100,
      offset: 0,
      logs: [
        {
          id: "3",
          actor_id: 7,
          event_type: "pdf.signature.applied",
          resource: "pdf",
          ip_address: "10.0.0.8",
          user_agent: "Mozilla/5.0",
          metadata: {},
          message: "Signature complete",
          created_at: "2024-05-01T09:00:00Z",
        },
      ],
    });

    mock.onGet("/api/v1/audit/logs").replyOnce(200, {
      total: 1,
      limit: 100,
      offset: 0,
      logs: [
        {
          id: "4",
          actor_id: 123,
          event_type: "pdf.signature.applied",
          resource: "pdf",
          ip_address: "10.0.0.9",
          user_agent: "Mozilla/5.0",
          metadata: {},
          message: "Filtered",
          created_at: "2024-05-02T09:00:00Z",
        },
      ],
    });

    renderPage();

    expect(await screen.findByText(/Signature complete/)).toBeInTheDocument();

    await user.clear(screen.getByLabelText(/Action type/i));
    await user.type(screen.getByLabelText(/Action type/i), "pdf.signature.applied");

    await user.clear(screen.getByLabelText(/User ID/i));
    await user.type(screen.getByLabelText(/User ID/i), "123");

    await user.type(screen.getByLabelText(/Start date/i), "2024-05-01");
    await user.type(screen.getByLabelText(/End date/i), "2024-05-02");

    await user.click(screen.getByRole("button", { name: /apply filters/i }));

    await waitFor(() => expect(mock.history.get.length).toBe(2));

    const secondRequest = mock.history.get[1];
    expect(secondRequest.params?.event_type).toBe("pdf.signature.applied");
    expect(secondRequest.params?.actor_id === 123 || secondRequest.params?.actor_id === "123").toBe(true);

    expect(await screen.findByText(/Filtered/)).toBeInTheDocument();
    expect(screen.getByText(/Date range: 2024-05-01 → 2024-05-02/)).toBeInTheDocument();
  });
});
