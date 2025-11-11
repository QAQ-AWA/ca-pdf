import AxiosMockAdapter from "axios-mock-adapter";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ThemeProvider } from "../../../components/ThemeProvider";
import { httpClient } from "../../../lib/httpClient";
import { UsersManagementPage } from "../UsersManagementPage";

describe("UsersManagementPage", () => {
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
        <UsersManagementPage />
      </ThemeProvider>
    );

  it("loads and displays users list", async () => {
    mock.onGet("/api/v1/users").reply(200, {
      items: [
        {
          id: "1",
          username: "testuser",
          email: "test@example.com",
          role: "user",
          is_active: true,
          created_at: "2024-01-01T00:00:00Z",
        },
        {
          id: "2",
          username: "adminuser",
          email: "admin@example.com",
          role: "admin",
          is_active: true,
          created_at: "2024-01-02T00:00:00Z",
        },
      ],
      total_count: 2,
      skip: 0,
      limit: 10,
    });

    renderPage();

    expect(await screen.findByText("testuser")).toBeInTheDocument();
    expect(screen.getByText("adminuser")).toBeInTheDocument();
    expect(screen.getByText("test@example.com")).toBeInTheDocument();
    expect(screen.getByText("admin@example.com")).toBeInTheDocument();
  });

  it("opens create user modal when create button is clicked", async () => {
    mock.onGet("/api/v1/users").reply(200, {
      items: [],
      total_count: 0,
      skip: 0,
      limit: 10,
    });

    renderPage();

    await waitFor(() => expect(mock.history.get.length).toBe(1));

    const createButton = screen.getByRole("button", { name: /创建用户/i });
    await user.click(createButton);

    expect(await screen.findByText("创建新用户")).toBeInTheDocument();
  });

  it("displays search input", async () => {
    mock.onGet("/api/v1/users").reply(200, {
      items: [],
      total_count: 0,
      skip: 0,
      limit: 10,
    });

    renderPage();

    await waitFor(() => expect(mock.history.get.length).toBe(1));

    expect(screen.getByPlaceholderText(/搜索用户名或邮箱/i)).toBeInTheDocument();
  });

  it("displays filter controls", async () => {
    mock.onGet("/api/v1/users").reply(200, {
      items: [],
      total_count: 0,
      skip: 0,
      limit: 10,
    });

    renderPage();

    await waitFor(() => expect(mock.history.get.length).toBe(1));

    const roleSelects = screen.getAllByRole("combobox");
    expect(roleSelects.length).toBeGreaterThan(0);
  });

  it("displays user active status button", async () => {
    mock.onGet("/api/v1/users").reply(200, {
      items: [
        {
          id: "1",
          username: "testuser",
          email: "test@example.com",
          role: "user",
          is_active: true,
          created_at: "2024-01-01T00:00:00Z",
        },
      ],
      total_count: 1,
      skip: 0,
      limit: 10,
    });

    renderPage();

    expect(await screen.findByText("活跃")).toBeInTheDocument();
  });
});
