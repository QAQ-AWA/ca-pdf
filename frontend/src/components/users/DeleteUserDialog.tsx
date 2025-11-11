import { useState } from "react";

import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { useTheme } from "../ThemeProvider";
import type { User } from "../../lib/usersApi";

interface DeleteUserDialogProps {
  user: User;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}

export const DeleteUserDialog = ({ user, onClose, onConfirm }: DeleteUserDialogProps) => {
  const theme = useTheme();
  const [deleting, setDeleting] = useState(false);

  const handleConfirm = async () => {
    setDeleting(true);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      console.error("Failed to delete user:", error);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <Modal open={true} title="确认删除用户" onClose={onClose}>
      <div style={{ display: "grid", gap: theme.spacing.md }}>
        <div
          style={{
            padding: theme.spacing.md,
            backgroundColor: "#fef3c7",
            borderRadius: theme.borderRadius,
            border: "1px solid #fbbf24",
          }}
        >
          <strong style={{ color: "#92400e" }}>⚠️ 警告</strong>
          <p style={{ margin: `${theme.spacing.sm} 0 0`, color: "#92400e" }}>
            此操作不可撤销。删除用户将永久移除该用户及其关联的所有数据。
          </p>
        </div>

        <div style={{ padding: theme.spacing.md, backgroundColor: theme.colors.surface, borderRadius: theme.borderRadius }}>
          <p style={{ margin: 0 }}>
            <strong>用户名：</strong> {user.username}
          </p>
          <p style={{ margin: `${theme.spacing.xs} 0 0` }}>
            <strong>邮箱：</strong> {user.email}
          </p>
          <p style={{ margin: `${theme.spacing.xs} 0 0` }}>
            <strong>角色：</strong> {user.role === "admin" ? "管理员" : "用户"}
          </p>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: theme.spacing.md }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={deleting}>
            取消
          </Button>
          <Button
            type="button"
            onClick={handleConfirm}
            disabled={deleting}
            style={{ backgroundColor: "#dc2626" }}
          >
            {deleting ? "删除中..." : "确认删除"}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
