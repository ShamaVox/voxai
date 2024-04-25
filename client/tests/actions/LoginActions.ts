import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
  mockUpcomingInterviews,
} from "../utils/MockRequests";
import { fireEvent, waitFor } from "@testing-library/react-native";

export const sendCodeSuccess = async (
  getByTestId,
  getByText,
  newAccount: number = 0
) => {
  let email;
  if (newAccount) {
    mockNewAccount();
    email = "new" + newAccount.toString() + "@email.com";
  } else {
    mockAccountExists();
    email = "existing@email.com";
  }

  await waitFor(() => {
    fireEvent.changeText(getByTestId("email-input"), email);
    fireEvent.press(getByText("Send code"));
  });
};

export const validateCodeSuccess = async (
  findByPlaceholderText,
  getByTestId,
  getByText,
  newAccount: number = 0
) => {
  mockValidCode();
  if (newAccount) {
    await findByPlaceholderText("Name");
    await waitFor(() => {
      fireEvent.changeText(getByTestId("name-input"), "New User");
    });
    await waitFor(() => {
      fireEvent.changeText(getByTestId("organization-input"), "Test Org");
    });
  }
  await findByPlaceholderText("Verification code");
  await waitFor(() => {
    fireEvent.changeText(getByTestId("code-input"), "123123"); // Valid code
  });
  await waitFor(() => {
    fireEvent.press(getByText("Validate code"));
  });

  // Wait for login to complete
  await new Promise(process.nextTick);
};

export const loginSuccess = async (
  findByPlaceholderText,
  getByTestId,
  getByText,
  newAccount: number = 0
) => {
  await sendCodeSuccess(getByTestId, getByText, (newAccount = newAccount));

  mockUpcomingInterviews();

  await validateCodeSuccess(
    findByPlaceholderText,
    getByTestId,
    getByText,
    (newAccount = newAccount)
  );
};
