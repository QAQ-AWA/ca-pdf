import { useTheme } from "../ThemeProvider";
import { Button } from "../ui/Button";
import { Spinner } from "../ui/Spinner";
import type { User } from "../../lib/usersApi";

interface UsersTableProps {
  users: User[];
  loading: boolean;
  total: number;
  currentPage: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onEdit: (user: User) => void;
  onDelete: (user: User) => void;
  onResetPassword: (user: User) => void;
  onToggleActive: (user: User) => void;
}

export const UsersTable = ({
  users,
  loading,
  total,
  currentPage,
  pageSize,
  onPageChange,
  onEdit,
  onDelete,
  onResetPassword,
  onToggleActive,
}: UsersTableProps) => {
  const theme = useTheme();

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          padding: theme.spacing.xl,
        }}
      >
        <Spinner size={40} />
      </div>
    );
  }

  if (users.length === 0) {
    return (
      <div
        style={{
          textAlign: "center",
          padding: theme.spacing.xl,
          color: theme.colors.muted,
        }}
      >
        没有找到用户
      </div>
    );
  }

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div style={{ display: "grid", gap: theme.spacing.md }}>
      <div style={{ overflowX: "auto" }}>
        <table
          style={{
            width: "100%",
            borderCollapse: "collapse",
            backgroundColor: theme.colors.surface,
            borderRadius: theme.borderRadius,
          }}
        >
          <thead>
            <tr style={{ borderBottom: `2px solid ${theme.colors.muted}` }}>
              <th style={{ padding: theme.spacing.md, textAlign: "left" }}>ID</th>
              <th style={{ padding: theme.spacing.md, textAlign: "left" }}>用户名</th>
              <th style={{ padding: theme.spacing.md, textAlign: "left" }}>邮箱</th>
              <th style={{ padding: theme.spacing.md, textAlign: "left" }}>角色</th>
              <th style={{ padding: theme.spacing.md, textAlign: "center" }}>状态</th>
              <th style={{ padding: theme.spacing.md, textAlign: "left" }}>创建时间</th>
              <th style={{ padding: theme.spacing.md, textAlign: "center" }}>操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id} style={{ borderBottom: `1px solid ${theme.colors.muted}` }}>
                <td style={{ padding: theme.spacing.md, fontSize: theme.font.size.sm }}>{user.id}</td>
                <td style={{ padding: theme.spacing.md }}>{user.username}</td>
                <td style={{ padding: theme.spacing.md }}>{user.email}</td>
                <td style={{ padding: theme.spacing.md }}>
                  <span
                    style={{
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      borderRadius: theme.borderRadius,
                      backgroundColor: user.role === "admin" ? "#fef3c7" : "#dbeafe",
                      color: user.role === "admin" ? "#92400e" : "#1e40af",
                      fontSize: theme.font.size.sm,
                    }}
                  >
                    {user.role === "admin" ? "管理员" : "用户"}
                  </span>
                </td>
                <td style={{ padding: theme.spacing.md, textAlign: "center" }}>
                  <button
                    onClick={() => onToggleActive(user)}
                    style={{
                      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                      borderRadius: theme.borderRadius,
                      border: "none",
                      backgroundColor: user.is_active ? "#d1fae5" : "#fee2e2",
                      color: user.is_active ? "#065f46" : "#991b1b",
                      fontSize: theme.font.size.sm,
                      cursor: "pointer",
                    }}
                  >
                    {user.is_active ? "活跃" : "停用"}
                  </button>
                </td>
                <td style={{ padding: theme.spacing.md, fontSize: theme.font.size.sm }}>
                  {new Date(user.created_at).toLocaleDateString()}
                </td>
                <td style={{ padding: theme.spacing.md }}>
                  <div style={{ display: "flex", gap: theme.spacing.xs, justifyContent: "center" }}>
                    <Button variant="ghost" onClick={() => onEdit(user)} style={{ padding: theme.spacing.xs }}>
                      编辑
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => onResetPassword(user)}
                      style={{ padding: theme.spacing.xs }}
                    >
                      重置密码
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => onDelete(user)}
                      style={{ padding: theme.spacing.xs, color: "#dc2626" }}
                    >
                      删除
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div
          style={{
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            gap: theme.spacing.md,
          }}
        >
          <Button variant="secondary" onClick={() => onPageChange(currentPage - 1)} disabled={currentPage === 0}>
            上一页
          </Button>
          <span style={{ fontSize: theme.font.size.sm }}>
            第 {currentPage + 1} 页 / 共 {totalPages} 页
          </span>
          <Button
            variant="secondary"
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage >= totalPages - 1}
          >
            下一页
          </Button>
        </div>
      )}
    </div>
  );
};
