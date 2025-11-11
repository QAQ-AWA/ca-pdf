import { FormEvent, useState } from "react";

import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import { Input } from "../ui/Input";
import { useTheme } from "../ThemeProvider";
import { usersApi, User } from "../../lib/usersApi";

interface ResetPasswordDialogProps {
  user: User;
  onClose: () => void;
  onSuccess: () => void;
}

export const ResetPasswordDialog = ({ user, onClose, onSuccess }: ResetPasswordDialogProps) => {
  const theme = useTheme();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resetting, setResetting] = useState(false);

  const getPasswordStrength = (pwd: string): { text: string; color: string } => {
    if (pwd.length === 0) return { text: "", color: "" };
    if (pwd.length < 8) return { text: "弱", color: "#dc2626" };
    
    let strength = 0;
    if (pwd.length >= 12) strength++;
    if (/[a-z]/.test(pwd)) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/[0-9]/.test(pwd)) strength++;
    if (/[^a-zA-Z0-9]/.test(pwd)) strength++;

    if (strength <= 2) return { text: "中", color: "#f59e0b" };
    if (strength <= 4) return { text: "强", color: "#10b981" };
    return { text: "非常强", color: "#059669" };
  };

  const passwordStrength = getPasswordStrength(password);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);

    if (password.length < 8) {
      setError("密码至少需要8个字符");
      return;
    }

    if (password !== confirmPassword) {
      setError("两次输入的密码不一致");
      return;
    }

    setResetting(true);
    try {
      await usersApi.resetPassword(user.id, password);
      onSuccess();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : "重置密码失败";
      setError(message);
    } finally {
      setResetting(false);
    }
  };

  return (
    <Modal open={true} title="重置密码" onClose={onClose}>
      <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.md }}>
        <div style={{ padding: theme.spacing.md, backgroundColor: theme.colors.surface, borderRadius: theme.borderRadius }}>
          <p style={{ margin: 0 }}>
            <strong>用户名：</strong> {user.username}
          </p>
          <p style={{ margin: `${theme.spacing.xs} 0 0` }}>
            <strong>邮箱：</strong> {user.email}
          </p>
        </div>

        {error && (
          <div
            style={{
              padding: theme.spacing.md,
              backgroundColor: "#fee2e2",
              color: "#991b1b",
              borderRadius: theme.borderRadius,
            }}
          >
            {error}
          </div>
        )}

        <div>
          <Input
            label="新密码"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {passwordStrength.text && (
            <div style={{ marginTop: theme.spacing.xs, fontSize: theme.font.size.sm }}>
              密码强度: <span style={{ color: passwordStrength.color, fontWeight: theme.font.weight.medium }}>
                {passwordStrength.text}
              </span>
            </div>
          )}
        </div>

        <Input
          label="确认密码"
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
        />

        <div style={{ display: "flex", justifyContent: "flex-end", gap: theme.spacing.md }}>
          <Button type="button" variant="secondary" onClick={onClose} disabled={resetting}>
            取消
          </Button>
          <Button type="submit" disabled={resetting}>
            {resetting ? "重置中..." : "确认重置"}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
