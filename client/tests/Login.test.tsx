import React from "react";
import {
  render,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react-native";
import { AuthContext } from "../src/AuthContext";
import {
  mockAccountExists,
  mockNewAccount,
  mockInvalidCode,
} from "./utils/MockRequests";
import { randomAccountNumber } from "./utils/Random";
import {
  loginFormEntry,
  sendCodeSuccess,
  validateCodeSuccess,
  loginSuccess,
} from "./actions/LoginActions";
import { clearCookies } from "./utils/Cookies";
import { renderLoginFromMock } from "./utils/Render";

const mockNavigate = jest.fn();
const mockHandleLogin = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    addListener: () => jest.fn(),
  }),
}));

beforeEach(() => {
  jest.restoreAllMocks();
  jest.clearAllMocks();
  clearCookies();
});

const renderLogin: () => Object = () => {
  return renderLoginFromMock(mockHandleLogin);
};

test("shows error message for invalid email", async () => {
  renderLogin();

  // Enter an invalid email
  await loginFormEntry(
    { "email-input": "invalid_email" },
    "Send code",
    "Invalid email"
  );
});

test("shows no error message for valid email", async () => {
  renderLogin();

  mockAccountExists();

  await loginFormEntry(
    { "email-input": "valid@email.com" },
    "Send code",
    "Invalid email",
    false
  );
});

test("shows code input field after sending code", async () => {
  renderLogin();

  sendCodeSuccess(0);

  // Wait for code field to appear
  await screen.findByPlaceholderText("Verification code");

  // Assert that the code field is now present
  expect(screen.getByTestId("code-input")).toBeTruthy();
});

test("shows error message for invalid code", async () => {
  renderLogin();

  sendCodeSuccess(0);
  await loginFormEntry(
    { "code-input": "123" },
    "Validate code",
    "Verification code should be 6 digits"
  );

  // Try different invalid code
  mockInvalidCode();
  await loginFormEntry(
    { "code-input": "123292" },
    "Validate code",
    "Invalid code"
  );
});

test("shows new account fields when required", async () => {
  renderLogin();

  sendCodeSuccess(randomAccountNumber());

  // Assert new account fields are present
  await screen.findByPlaceholderText("Verification code");
  await screen.findByPlaceholderText("Name");
  await screen.findByPlaceholderText("Organization");

  expect(screen.getByTestId("name-input")).toBeTruthy();
  expect(screen.getByTestId("organization-input")).toBeTruthy();
});

test("handles successful login", async () => {
  renderLogin();

  await loginSuccess(0);

  // Assert that handleLogin was called with the correct arguments
  expect(mockHandleLogin).toHaveBeenCalledWith(
    "existing@email.com",
    "Test Name",
    "AUTHTOKEN"
  );
  expect(mockNavigate).toHaveBeenCalledWith("Home");
});

test("handles successful account creation and login", async () => {
  renderLogin();

  let accountNumber: number = randomAccountNumber();

  await loginSuccess(accountNumber);

  // Assert handleLogin was called and navigation occurred
  expect(mockHandleLogin).toHaveBeenCalledWith(
    "new" + accountNumber + "@email.com",
    "New User",
    "AUTHTOKEN"
  );
  expect(mockNavigate).toHaveBeenCalledWith("Home");
});
