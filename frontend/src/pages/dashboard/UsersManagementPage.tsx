import { useCallback, useEffect, useState } from "react";

import { useTheme } from "../../components/ThemeProvider";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { Card } from "../../components/ui/Card";
import { UsersTable } from "../../components/users/UsersTable";
import { CreateUserModal } from "../../components/users/CreateUserModal";
import { EditUserModal } from "../../components/users/EditUserModal";
import { DeleteUserDialog } from "../../components/users/DeleteUserDialog";
import { ResetPasswordDialog } from "../../components/users/ResetPasswordDialog";
import { usersApi, User } from "../../lib/usersApi";

export const UsersManagementPage = () => {
  const theme = useTheme();
  
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(0);
  const pageSize = 10;
  
  const [searchTerm, setSearchTerm] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("");
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [deletingUser, setDeletingUser] = useState<User | null>(null);
  const [resettingUser, setResettingUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await usersApi.listUsers({
        skip: currentPage * pageSize,
        limit: pageSize,
        search: searchTerm || undefined,
        role: roleFilter || undefined,
        is_active: statusFilter ? statusFilter === "active" : undefined,
      });
      setUsers(response.items);
      setTotal(response.total_count);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载用户列表失败";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, searchTerm, roleFilter, statusFilter]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  const handleDeleteUser = async (user: User) => {
    try {
      await usersApi.deleteUser(user.id);
      setSuccessMessage(`用户 ${user.username} 已成功删除`);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : "删除用户失败";
      setError(message);
    }
  };

  const handleToggleActive = async (user: User) => {
    try {
      await usersApi.toggleActive(user.id);
      setSuccessMessage(`用户 ${user.username} 状态已更新`);
      setTimeout(() => setSuccessMessage(null), 3000);
      loadUsers();
    } catch (err) {
      const message = err instanceof Error ? err.message : "更新用户状态失败";
      setError(message);
    }
  };

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setCurrentPage(0);
  };

  const handleRoleFilterChange = (value: string) => {
    setRoleFilter(value);
    setCurrentPage(0);
  };

  const handleStatusFilterChange = (value: string) => {
    setStatusFilter(value);
    setCurrentPage(0);
  };

  return (
    <div style={{ padding: theme.spacing.lg }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: theme.spacing.lg }}>
        <h1 style={{ fontSize: theme.font.size.xl, margin: 0 }}>用户管理</h1>
        <Button onClick={() => setShowCreateModal(true)}>+ 创建用户</Button>
      </div>

      {error && (
        <div
          style={{
            padding: theme.spacing.md,
            backgroundColor: "#fee2e2",
            color: "#991b1b",
            borderRadius: theme.borderRadius,
            marginBottom: theme.spacing.lg,
          }}
        >
          {error}
          <button
            onClick={() => setError(null)}
            style={{
              marginLeft: theme.spacing.md,
              background: "none",
              border: "none",
              color: "#991b1b",
              cursor: "pointer",
              textDecoration: "underline",
            }}
          >
            关闭
          </button>
        </div>
      )}

      {successMessage && (
        <div
          style={{
            padding: theme.spacing.md,
            backgroundColor: "#d1fae5",
            color: "#065f46",
            borderRadius: theme.borderRadius,
            marginBottom: theme.spacing.lg,
          }}
        >
          {successMessage}
        </div>
      )}

      <Card style={{ marginBottom: theme.spacing.lg }}>
        <div style={{ display: "grid", gap: theme.spacing.md, gridTemplateColumns: "1fr 1fr 1fr" }}>
          <Input
            label="搜索"
            placeholder="搜索用户名或邮箱..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
          />
          
          <label style={{ display: "grid", gap: theme.spacing.xs }}>
            <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>角色</span>
            <select
              value={roleFilter}
              onChange={(e) => handleRoleFilterChange(e.target.value)}
              style={{
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                borderRadius: theme.borderRadius,
                border: `1px solid ${theme.colors.muted}`,
                fontSize: theme.font.size.base,
                backgroundColor: "#fff",
              }}
            >
              <option value="">全部</option>
              <option value="user">用户</option>
              <option value="admin">管理员</option>
            </select>
          </label>

          <label style={{ display: "grid", gap: theme.spacing.xs }}>
            <span style={{ fontSize: theme.font.size.sm, fontWeight: theme.font.weight.medium }}>状态</span>
            <select
              value={statusFilter}
              onChange={(e) => handleStatusFilterChange(e.target.value)}
              style={{
                padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                borderRadius: theme.borderRadius,
                border: `1px solid ${theme.colors.muted}`,
                fontSize: theme.font.size.base,
                backgroundColor: "#fff",
              }}
            >
              <option value="">全部</option>
              <option value="active">活跃</option>
              <option value="inactive">停用</option>
            </select>
          </label>
        </div>
      </Card>

      <Card>
        <UsersTable
          users={users}
          loading={loading}
          total={total}
          currentPage={currentPage}
          pageSize={pageSize}
          onPageChange={setCurrentPage}
          onEdit={setEditingUser}
          onDelete={setDeletingUser}
          onResetPassword={setResettingUser}
          onToggleActive={handleToggleActive}
        />
      </Card>

      {showCreateModal && (
        <CreateUserModal
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setSuccessMessage("用户创建成功");
            setTimeout(() => setSuccessMessage(null), 3000);
            loadUsers();
          }}
        />
      )}

      {editingUser && (
        <EditUserModal
          user={editingUser}
          onClose={() => setEditingUser(null)}
          onSuccess={() => {
            setSuccessMessage("用户信息已更新");
            setTimeout(() => setSuccessMessage(null), 3000);
            loadUsers();
          }}
        />
      )}

      {deletingUser && (
        <DeleteUserDialog
          user={deletingUser}
          onClose={() => setDeletingUser(null)}
          onConfirm={() => handleDeleteUser(deletingUser)}
        />
      )}

      {resettingUser && (
        <ResetPasswordDialog
          user={resettingUser}
          onClose={() => setResettingUser(null)}
          onSuccess={() => {
            setSuccessMessage("密码重置成功");
            setTimeout(() => setSuccessMessage(null), 3000);
            loadUsers();
          }}
        />
      )}
    </div>
  );
};
