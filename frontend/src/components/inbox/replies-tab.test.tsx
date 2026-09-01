import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { RepliesTab as ConversationsPage } from "./replies-tab";
import * as conversationsApi from "@/lib/api/conversations";

vi.mock("@/lib/workspace-context", () => ({
  useWorkspace: () => ({
    activeWorkspace: { id: "ws-123", name: "Test Workspace", slug: "test-workspace" },
    workspaces: [{ id: "ws-123", name: "Test Workspace", slug: "test-workspace" }],
    setActiveWorkspaceId: vi.fn(),
    createWorkspace: vi.fn(),
  }),
}));

describe("ConversationsPage - Add Test Reply", () => {
  const mockConversations: conversationsApi.Conversation[] = [
    {
      id: "conv-1",
      workspace_id: "ws-123",
      contact_id: "contact-1",
      contact_name: "Alex Buyer",
      contact_email: "alex.buyer@targetcompany.com",
      account_name: "Target Co",
      campaign_id: "camp-1",
      delivery_id: "del-1",
      status: "active",
      current_reply_state: "interested",
      last_message_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      messages: [],
    },
  ];

  beforeEach(() => {
    vi.spyOn(conversationsApi, "fetchConversations").mockResolvedValue(mockConversations);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("opens add test reply modal when button is clicked", async () => {
    render(<ConversationsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Alex Buyer").length).toBeGreaterThan(0);
    });

    const simulateBtn = screen.getByRole("button", { name: /add test reply/i, hidden: true });
    fireEvent.click(simulateBtn);

    expect(screen.getByText("Add Test Reply")).toBeInTheDocument();
    expect(screen.getByDisplayValue("alex.buyer@targetcompany.com")).toBeInTheDocument();
  });

  it("disables submit button and shows loading state while processing", async () => {
    let resolveIngest: (val: conversationsApi.Conversation) => void = () => {};
    const ingestPromise = new Promise<conversationsApi.Conversation>((resolve) => {
      resolveIngest = resolve;
    });

    vi.spyOn(conversationsApi, "ingestInboundReply").mockReturnValue(ingestPromise);

    render(<ConversationsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Alex Buyer").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByRole("button", { name: /add test reply/i, hidden: true }));

    const submitBtn = screen.getByRole("button", { name: /ingest & classify reply/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText("Processing...")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /processing/i })).toBeDisabled();
    });

    resolveIngest(mockConversations[0]);

    await waitFor(() => {
      // modal closed
      expect(screen.getByText(/Inbound prospect reply was successfully ingested and classified/i)).toBeInTheDocument();
    });
  });

  it("displays error message inside the modal when ingestion fails and keeps modal open", async () => {
    vi.spyOn(conversationsApi, "ingestInboundReply").mockRejectedValue(
      new Error("Contact or workspace could not be resolved for inbound message")
    );

    render(<ConversationsPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Alex Buyer").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getByRole("button", { name: /add test reply/i, hidden: true }));

    const submitBtn = screen.getByRole("button", { name: /ingest & classify reply/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(
        screen.getByText("Contact or workspace could not be resolved for inbound message")
      ).toBeInTheDocument();
      expect(screen.getByText("Add Test Reply")).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /ingest & classify reply/i })).not.toBeDisabled();
    });
  });
});
