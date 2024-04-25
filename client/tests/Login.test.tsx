import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import Login from "../src/Login";
import { AuthContext } from "../src/AuthContext";
import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
  mockInvalidCode,
} from "./utils/MockRequests";
import {
  sendCodeSuccess,
  validateCodeSuccess,
  loginSuccess,
} from "./actions/LoginActions";

const mockNavigate = jest.fn();
const mockHandleLogin = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    addListener: () => jest.fn(),
  }),
}));

function renderLogin() {
  return render(
    <AuthContext.Provider
      value={{ isLoggedIn: false, handleLogin: mockHandleLogin }}
    >
      <Login />
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

test("shows error message for invalid email", () => {
  const { getByTestId, getByText } = renderLogin();

  mockAccountExists();

  // Enter an invalid email
  fireEvent.changeText(getByTestId("email-input"), "invalid_email");

  // Check for error message
  expect(getByText("Invalid email")).toBeTruthy();
});

test("shows no error message for valid email", () => {
  const { getByTestId, queryByText } = renderLogin();

  mockAccountExists();

  fireEvent.changeText(getByTestId("email-input"), "valid@email.com");

  expect(queryByText("Invalid email")).toBeNull();
});

test("shows code input field after sending code", async () => {
  const { getByTestId, getByText, findByPlaceholderText } = renderLogin();

  sendCodeSuccess(getByTestId, getByText, (newAccount = false));

  // Wait for code field to appear
  await findByPlaceholderText("Verification code");

  // Assert that the code field is now present
  expect(getByTestId("code-input")).toBeTruthy();
});

test("shows error message for invalid code", async () => {
  const {
    getByTestId,
    getByText,
    findByPlaceholderText,
    findByText,
  } = renderLogin();

  sendCodeSuccess(getByTestId, getByText, (newAccount = false));
  await findByPlaceholderText("Verification code");
  fireEvent.changeText(getByTestId("code-input"), "123");
  fireEvent.press(getByText("Validate code"));

  // Assert error message
  await findByText("Verification code should be 6 digits");
  expect(getByText("Verification code should be 6 digits")).toBeTruthy();

  // Try different invalid code
  mockInvalidCode();
  fireEvent.changeText(getByTestId("code-input"), "123292");
  fireEvent.press(getByText("Validate code"));

  await findByText("Invalid code");
  expect(getByText("Invalid code")).toBeTruthy();
});

test("shows new account fields when required", async () => {
  const { getByTestId, getByText, findByPlaceholderText } = renderLogin();

  sendCodeSuccess(getByTestId, getByText, (newAccount = true));

  // Assert new account fields are present
  await findByPlaceholderText("Verification code");
  await findByPlaceholderText("Name");
  await findByPlaceholderText("Organization");

  expect(getByTestId("name-input")).toBeTruthy();
  expect(getByTestId("organization-input")).toBeTruthy();
});

test("handles successful login", async () => {
  const { getByTestId, getByText, findByPlaceholderText } = renderLogin();

  await loginSuccess(
    findByPlaceholderText,
    getByTestId,
    getByText,
    (newAccount = false)
  );

  // Assert that handleLogin was called with the correct arguments
  expect(mockHandleLogin).toHaveBeenCalledWith("valid@email.com", "Test Name");
  expect(mockNavigate).toHaveBeenCalledWith("Home");
});

test("handles successful account creation and login", async () => {
  const { getByTestId, getByText, findByPlaceholderText } = renderLogin();

  await loginSuccess(
    findByPlaceholderText,
    getByTestId,
    getByText,
    (newAccount = true)
  );

  // Assert handleLogin was called and navigation occurred
  expect(mockHandleLogin).toHaveBeenCalledWith("valid@email.com", "Test Name");
  expect(mockNavigate).toHaveBeenCalledWith("Home");
});
