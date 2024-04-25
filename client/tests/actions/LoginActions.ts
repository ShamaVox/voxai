import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
} from "../utils/MockRequests";
import { render, fireEvent } from "@testing-library/react-native";

export const sendCodeSuccess = (
  getByTestId,
  getByText,
  newAccount: boolean = false,
  mock: boolean = true
) => {
  if (mock) {
    if (newAccount) {
      mockNewAccount();
    } else {
      mockAccountExists();
    }
  }

  fireEvent.changeText(getByTestId("email-input"), "valid@email.com");
  fireEvent.press(getByText("Send code"));
};

export const validateCodeSuccess = async (
  findByPlaceholderText,
  getByTestId,
  getByText,
  newAccount: boolean = false,
  mock: boolean = true
) => {
  if (mock) {
    mockValidCode();
  }
  if (newAccount) {
    await findByPlaceholderText("Name");
    fireEvent.changeText(getByTestId("name-input"), "New User");
    fireEvent.changeText(getByTestId("organization-input"), "Test Org");
  }
  await findByPlaceholderText("Verification code");
  fireEvent.changeText(getByTestId("code-input"), "123123"); // Valid code
  fireEvent.press(getByText("Validate code"));

  // Wait for login to complete
  await new Promise(process.nextTick);
};

export const loginSuccess = async (
  findByPlaceholderText,
  getByTestId,
  getByText,
  newAccount: boolean = false,
  mock: boolean = true
) => {
  sendCodeSuccess(
    getByTestId,
    getByText,
    (newAccount = newAccount),
    (mock = mock)
  );

  await validateCodeSuccess(
    findByPlaceholderText,
    getByTestId,
    getByText,
    (newAccount = newAccount),
    (mock = mock)
  );
};
