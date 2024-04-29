import React from "react";
import { render, fireEvent, screen } from "@testing-library/react-native";
import Login from "../src/Login";
import { AuthContext } from "../src/AuthContext";
import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
  mockInvalidCode,
} from "./utils/MockRequests";
import { randomAccountNumber } from "./utils/Random";
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
      value={{
        isLoggedIn: false,
        handleLogin: mockHandleLogin,
        username: "",
        email: "",
        authToken: "",
        handleLogout: async () => {},
      }}
    >
      <Login />
    </AuthContext.Provider>
  );
}

beforeEach(() => {
  jest.clearAllMocks();
});

test("shows error message for invalid email", () => {
  renderLogin();

  // Enter an invalid email
  fireEvent.changeText(screen.getByTestId("email-input"), "invalid_email");
  fireEvent.press(screen.getByText("Send code"));

  // Check for error message
  expect(screen.getByText("Invalid email")).toBeTruthy();
});

test("shows no error message for valid email", () => {
  renderLogin();

  mockAccountExists();

  fireEvent.changeText(screen.getByTestId("email-input"), "valid@email.com");
  fireEvent.press(screen.getByText("Send code"));

  expect(screen.queryByText("Invalid email")).toBeNull();
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
  await screen.findByPlaceholderText("Verification code");
  fireEvent.changeText(screen.getByTestId("code-input"), "123");
  fireEvent.press(screen.getByText("Validate code"));

  // Assert error message
  await screen.findByText("Verification code should be 6 digits");
  expect(screen.getByText("Verification code should be 6 digits")).toBeTruthy();

  // Try different invalid code
  mockInvalidCode();
  fireEvent.changeText(screen.getByTestId("code-input"), "123292");
  fireEvent.press(screen.getByText("Validate code"));

  await screen.findByText("Invalid code");
  expect(screen.getByText("Invalid code")).toBeTruthy();
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
    "Test Name",
    "AUTHTOKEN"
  );
  expect(mockNavigate).toHaveBeenCalledWith("Home");
});
