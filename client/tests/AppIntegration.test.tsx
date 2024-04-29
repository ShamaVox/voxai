import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import App from "../src/App";
import { SERVER_ENDPOINT } from "../src/utils/Constants";
import { randomAccountNumber } from "./utils/Random";
import { loginAndNavigateAll } from "./actions/AppIntegrationActions";

test("Login with existing account and navigate to Dashboard and Home", async () => {
  render(<App />);
  await loginAndNavigateAll();
});

test("Create new account and navigate to Dashboard and Home", async () => {
  render(<App />);
  await loginAndNavigateAll(randomAccountNumber());
});
