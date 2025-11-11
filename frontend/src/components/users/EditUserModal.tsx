import { useState } from "react";

import { Modal } from "../ui/Modal";
import { UserForm, UserFormData } from "./UserForm";
import { usersApi, User } from "../../lib/usersApi";

interface EditUserModalProps {
  user: User;
  onClose: () => void;
  onSuccess: () => void;
}

export const EditUserModal = ({ user, onClose, onSuccess }: EditUserModalProps) => {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: UserFormData) => {
    setError(null);
    try {
      await usersApi.updateUser(user.id, {
        email: data.email,
        role: data.role,
        is_active: data.is_active,
      });
      onSuccess();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : "更新用户失败";
      setError(message);
      throw err;
    }
  };

  return (
    <Modal open={true} title="编辑用户" onClose={onClose}>
      {error && (
        <div
          style={{
            padding: "12px",
            backgroundColor: "#fee2e2",
            color: "#991b1b",
            borderRadius: "4px",
            marginBottom: "16px",
          }}
        >
          {error}
        </div>
      )}
      <UserForm user={user} onSubmit={handleSubmit} onCancel={onClose} />
    </Modal>
  );
};
