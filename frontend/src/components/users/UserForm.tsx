import { FormEvent, useState } from "react";

import { useTheme } from "../ThemeProvider";
import { Input } from "../ui/Input";
import { Button } from "../ui/Button";
import type { User } from "../../lib/usersApi";

interface UserFormProps {
  user?: User | null;
  onSubmit: (data: UserFormData) => Promise<void>;
  onCancel: () => void;
}

export interface UserFormData {
  username: string;
  email: string;
  password?: string;
  role: string;
  is_active: boolean;
}

export const UserForm = ({ user, onSubmit, onCancel }: UserFormProps) => {
  const theme = useTheme();
  const isEditing = Boolean(user);

  const [formData, setFormData] = useState<UserFormData>({
    username: user?.username || "",
    email: user?.email || "",
    password: "",
    role: user?.role || "user",
    is_active: user?.is_active ?? true,
  });

  const [errors, setErrors] = useState<Partial<Record<keyof UserFormData, string>>>({});
  const [submitting, setSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof UserFormData, string>> = {};

    if (!formData.username.trim()) {
      newErrors.username = "用户名不能为空";
    } else if (!/^[a-zA-Z0-9_-]{3,50}$/.test(formData.username)) {
      newErrors.username = "用户名必须是3-50个字符，只能包含字母、数字、下划线和连字符";
    }

    if (!formData.email.trim()) {
      newErrors.email = "邮箱不能为空";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = "请输入有效的邮箱地址";
    }

    if (!isEditing && !formData.password) {
      newErrors.password = "密码不能为空";
    } else if (formData.password && formData.password.length < 8) {
      newErrors.password = "密码至少需要8个字符";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    try {
      await onSubmit(formData);
    } catch (error) {
      console.error("Form submission error:", error);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.md }}>
      <Input
        label="用户名"
        value={formData.username}
        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
        disabled={isEditing}
        required
      />
      {errors.username && (
        <span style={{ color: "#dc2626", fontSize: theme.font.size.sm, marginTop: `-${theme.spacing.sm}` }}>
          {errors.username}
        </span>
      )}

      <Input
        label="邮箱"
        type="email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        required
      />
      {errors.email && (
        <span style={{ color: "#dc2626", fontSize: theme.font.size.sm, marginTop: `-${theme.spacing.sm}` }}>
          {errors.email}
        </span>
      )}

      <Input
        label={isEditing ? "密码（留空表示不修改）" : "密码"}
        type="password"
        value={formData.password}
        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
        required={!isEditing}
      />
      {errors.password && (
        <span style={{ color: "#dc2626", fontSize: theme.font.size.sm, marginTop: `-${theme.spacing.sm}` }}>
          {errors.password}
        </span>
      )}

      <label style={{ display: "grid", gap: theme.spacing.xs }}>
        <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>角色</span>
        <select
          value={formData.role}
          onChange={(e) => setFormData({ ...formData, role: e.target.value })}
          style={{
            padding: `${theme.spacing.sm} ${theme.spacing.md}`,
            borderRadius: theme.borderRadius,
            border: `1px solid ${theme.colors.muted}`,
            fontSize: theme.font.size.base,
            backgroundColor: "#fff",
          }}
        >
          <option value="user">用户</option>
          <option value="admin">管理员</option>
        </select>
      </label>

      <label style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
        <input
          type="checkbox"
          checked={formData.is_active}
          onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
          style={{ width: "18px", height: "18px" }}
        />
        <span style={{ fontSize: theme.font.size.sm }}>账户已激活</span>
      </label>

      <div style={{ display: "flex", justifyContent: "flex-end", gap: theme.spacing.md, marginTop: theme.spacing.md }}>
        <Button type="button" variant="secondary" onClick={onCancel} disabled={submitting}>
          取消
        </Button>
        <Button type="submit" disabled={submitting}>
          {submitting ? "提交中..." : isEditing ? "保存" : "创建"}
        </Button>
      </div>
    </form>
  );
};
