type EnvKey = `VITE_${string}`;

type ClientEnv = {
  appName: string;
  apiBaseUrl: string;
  mode: string;
  isDev: boolean;
  isProd: boolean;
};

const readEnv = (key: EnvKey, fallback?: string): string => {
  const value = import.meta.env[key];

  if (typeof value === "string" && value.length > 0) {
    return value;
  }

  if (fallback !== undefined) {
    return fallback;
  }

  console.warn(`Missing environment variable: ${key}`);
  return "";
};

export const clientEnv: ClientEnv = Object.freeze({
  appName: readEnv("VITE_APP_NAME", "Monorepo UI"),
  apiBaseUrl: readEnv("VITE_API_BASE_URL", "http://localhost:8000"),
  mode: import.meta.env.MODE,
  isDev: import.meta.env.DEV,
  isProd: import.meta.env.PROD,
});
