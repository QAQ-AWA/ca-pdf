import { PropsWithChildren, ReactNode, useEffect, useMemo } from "react";

import { useTheme } from "../ThemeProvider";
import { Button } from "./Button";

type ModalProps = PropsWithChildren<{
  open: boolean;
  title: string;
  onClose: () => void;
  footer?: ReactNode;
}>;

export const Modal = ({ open, title, onClose, footer, children }: ModalProps) => {
  const theme = useTheme();
  const titleId = useMemo(() => `modal-title-${Math.random().toString(36).slice(2)}`, []);

  useEffect(() => {
    if (!open) {
      return;
    }

    const handleKeydown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, [open, onClose]);

  if (!open) {
    return null;
  }

  return (
    <div
      role="presentation"
      onClick={(event) => {
        if (event.target === event.currentTarget) {
          onClose();
        }
      }}
      style={{
        position: "fixed",
        inset: 0,
        backgroundColor: "rgba(15, 23, 42, 0.55)",
        display: "grid",
        placeItems: "center",
        padding: theme.spacing.lg,
        zIndex: 1000,
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        style={{
          width: "min(640px, 100%)",
          maxHeight: "90vh",
          overflowY: "auto",
          background: theme.colors.surface,
          borderRadius: theme.borderRadius,
          boxShadow: theme.shadow,
          padding: theme.spacing.xl,
          display: "grid",
          gap: theme.spacing.md,
        }}
      >
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: theme.spacing.sm,
          }}
        >
          <h2 id={titleId} style={{ margin: 0, fontSize: theme.font.size.lg }}>
            {title}
          </h2>
          <Button variant="ghost" type="button" aria-label="Close modal" onClick={onClose}>
            Close
          </Button>
        </header>
        <div style={{ display: "grid", gap: theme.spacing.md }}>{children}</div>
        {footer ? <footer style={{ display: "flex", justifyContent: "flex-end" }}>{footer}</footer> : null}
      </div>
    </div>
  );
};
