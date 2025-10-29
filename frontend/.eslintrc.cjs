const path = require("node:path");

module.exports = {
  root: true,
  extends: [
    path.resolve(__dirname, "../config/eslint/base.cjs"),
    "plugin:testing-library/react",
  ],
  ignorePatterns: ["dist", "node_modules"],
  settings: {
    react: {
      version: "detect",
    },
  },
  rules: {
    "react/prop-types": "off",
  },
  overrides: [
    {
      files: ["**/*.{ts,tsx}"],
      rules: {
        "testing-library/prefer-find-by": "warn",
        "testing-library/render-result-naming-convention": "warn",
        "no-useless-escape": "warn",
      },
    },
  ],
};
