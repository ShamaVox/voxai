import React from "react";
import { render, fireEvent, waitFor } from "@testing-library/react-native";
import App from "../src/App";
import { SERVER_ENDPOINT } from "../src/utils/Constants";
import { loginAndNavigateAll } from "./actions/AppIntegrationActions";

test("Login with existing account and navigate to Dashboard and Home", async () => {
  const {
    getByText,
    getByTestId,
    queryByTestId,
    queryByText,
    findByText,
    findByPlaceholderText,
    queryAllByTestId,
  } = render(<App />);
  await loginAndNavigateAll(
    getByText,
    getByTestId,
    queryByTestId,
    queryByText,
    findByText,
    findByPlaceholderText,
    queryAllByTestId
  );
});

test("Create new account and navigate to Dashboard and Home", async () => {
  const {
    getByText,
    getByTestId,
    queryByTestId,
    queryByText,
    findByText,
    findByPlaceholderText,
    queryAllByTestId,
  } = render(<App />);
  await loginAndNavigateAll(
    getByText,
    getByTestId,
    queryByTestId,
    queryByText,
    findByText,
    findByPlaceholderText,
    queryAllByTestId,
    Math.random() * 9999999999999999
  );
});
