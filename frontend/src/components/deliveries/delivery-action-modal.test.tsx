import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { DeliveryActionModal } from "./delivery-action-modal";

describe("DeliveryActionModal", () => {
  const defaultProps = {
    isOpen: true,
    draftSubject: "Test Subject",
    realProspectEmail: "prospect@example.com",
    onClose: vi.fn(),
    onConfirm: vi.fn(),
  };

  afterEach(() => {
    cleanup();
    vi.clearAllMocks();
  });

  it("renders when isOpen is true", () => {
    render(<DeliveryActionModal {...defaultProps} />);
    expect(screen.getByText("Send Outbound Email")).toBeInTheDocument();
    expect(screen.getByText(/Target prospect:/)).toBeInTheDocument();
    expect(screen.getByText("prospect@example.com")).toBeInTheDocument();
  });

  it("does not render when isOpen is false", () => {
    render(<DeliveryActionModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByText("Send Outbound Email")).not.toBeInTheDocument();
  });

  it("calls onConfirm with null if no test email is provided (live send)", async () => {
    const onConfirmMock = vi.fn().mockResolvedValue(undefined);
    render(<DeliveryActionModal {...defaultProps} onConfirm={onConfirmMock} />);
    
    // Default is empty test email, so the warning should be shown
    expect(screen.getByText("Attention: Live Dispatch")).toBeInTheDocument();
    
    const confirmButton = screen.getByRole("button", { name: /Confirm Live Send/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(onConfirmMock).toHaveBeenCalledWith(null);
    });
  });

  it("calls onConfirm with the test email if provided (test send)", async () => {
    const onConfirmMock = vi.fn().mockResolvedValue(undefined);
    render(<DeliveryActionModal {...defaultProps} onConfirm={onConfirmMock} />);
    
    const input = screen.getByLabelText(/Test Recipient Email/i);
    fireEvent.change(input, { target: { value: "test@example.com" } });
    
    // Warning should disappear
    expect(screen.queryByText("Attention: Live Dispatch")).not.toBeInTheDocument();
    
    const confirmButton = screen.getByRole("button", { name: /Confirm Test Send/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(onConfirmMock).toHaveBeenCalledWith("test@example.com");
    });
  });

  it("disables buttons and shows loading state during submission", async () => {
    let resolveConfirm: (value: void | PromiseLike<void>) => void = () => {};
    const promise = new Promise<void>((resolve) => {
      resolveConfirm = resolve;
    });
    
    const onConfirmMock = vi.fn().mockReturnValue(promise);
    render(<DeliveryActionModal {...defaultProps} onConfirm={onConfirmMock} />);
    
    const confirmButton = screen.getByRole("button", { name: /Confirm Live Send/i });
    const cancelButton = screen.getByRole("button", { name: /Cancel/i });
    
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(screen.getByText("Sending...")).toBeInTheDocument();
      expect(confirmButton).toBeDisabled();
      expect(cancelButton).toBeDisabled();
    });
    
    resolveConfirm();
    
    await waitFor(() => {
      expect(defaultProps.onClose).toHaveBeenCalled();
    });
  });

  it("displays error message if submission fails", async () => {
    const onConfirmMock = vi.fn().mockRejectedValue(new Error("Delivery failed permanently"));
    render(<DeliveryActionModal {...defaultProps} onConfirm={onConfirmMock} />);
    
    const confirmButton = screen.getByRole("button", { name: /Confirm Live Send/i });
    fireEvent.click(confirmButton);
    
    await waitFor(() => {
      expect(screen.getByText("Delivery failed permanently")).toBeInTheDocument();
      expect(confirmButton).not.toBeDisabled();
    });
  });
});
