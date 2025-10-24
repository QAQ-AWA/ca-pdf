import { FormEvent, useState } from "react";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { useTheme } from "../../components/ThemeProvider";

export const SettingsPage = () => {
  const theme = useTheme();
  const [workspaceName, setWorkspaceName] = useState("Product Team");
  const [timezone, setTimezone] = useState("UTC");
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setMessage("Settings saved");
  };

  return (
    <div style={{ display: "grid", gap: theme.spacing.xl }}>
      <h2 style={{ margin: 0 }}>Settings</h2>
      <Card title="Workspace details">
        <form onSubmit={handleSubmit} style={{ display: "grid", gap: theme.spacing.lg }}>
          <Input
            label="Workspace name"
            value={workspaceName}
            onChange={(event) => setWorkspaceName(event.target.value)}
            required
          />
          <Input
            label="Timezone"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
            required
          />
          {message ? (
            <span style={{ color: theme.colors.success }}>{message}</span>
          ) : null}
          <Button type="submit">Save changes</Button>
        </form>
      </Card>
    </div>
  );
};
