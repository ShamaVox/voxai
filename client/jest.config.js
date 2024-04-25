module.exports = {
  preset: "jest-expo",
  transform: {
    "\\.[jt]sx?$": "babel-jest",
  },
  setupFiles: ["<rootDir>/tests/jest-setup.js"],
};
