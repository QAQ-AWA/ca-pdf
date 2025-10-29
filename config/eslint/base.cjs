const path = require("node:path");
const Module = require("node:module");

const frontendNodeModules = path.resolve(__dirname, "../../frontend/node_modules");

if (!module.paths.includes(frontendNodeModules)) {
  module.paths.push(frontendNodeModules);
}

if (!Module.globalPaths.includes(frontendNodeModules)) {
  Module.globalPaths.push(frontendNodeModules);
}

const resolveFromFrontend = (moduleName) =>
  require.resolve(moduleName, { paths: [frontendNodeModules, __dirname] });

module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  parser: resolveFromFrontend("@typescript-eslint/parser"),
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
  },
  settings: {
    react: {
      version: "detect",
    },
  },
  rules: {
    "react/react-in-jsx-scope": "off",
  },
};
