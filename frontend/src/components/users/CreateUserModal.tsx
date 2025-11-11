import { useState } from "react";

import { Modal } from "../ui/Modal";
import { UserForm, UserFormData } from "./UserForm";
import { usersApi } from "../../lib/usersApi";

interface CreateUserModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export const CreateUserModal = ({ onClose, onSuccess }: CreateUserModalProps) => {
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: UserFormData) => {
    setError(null);
    try {
      await usersApi.createUser({
        username: data.username,
        email: data.email,
        password: data.password || "",
        role: data.role,
        is_active: data.is_active,
      });
      onSuccess();
      onClose();
    } catch (err) {
      const message = err instanceof Error ? err.message : "创建用户失败";
      setError(message);
      throw err;
    }
  };

  return (
    <Modal open={true} title="创建新用户" onClose={onClose}>
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
      <UserForm onSubmit={handleSubmit} onCancel={onClose} />
    </Modal>
  );
};
