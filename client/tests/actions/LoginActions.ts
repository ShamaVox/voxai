import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
  mockUpcomingInterviews,
} from "../utils/MockRequests";
import { fireEvent, waitFor, screen } from "@testing-library/react-native";

export const sendCodeSuccess = async (newAccount: number = 0) => {
  let email;
  if (newAccount) {
    mockNewAccount();
    email = "new" + newAccount.toString() + "@email.com";
  } else {
    mockAccountExists();
    email = "existing@email.com";
  }

  await waitFor(() => {
    fireEvent.changeText(screen.getByTestId("email-input"), email);
    fireEvent.press(screen.getByText("Send code"));
  });
};

export const validateCodeSuccess = async (newAccount: number = 0) => {
  mockValidCode();
  if (newAccount) {
    await screen.findByPlaceholderText("Name");
    await waitFor(() => {
      fireEvent.changeText(screen.getByTestId("name-input"), "New User");
    });
    await waitFor(() => {
      fireEvent.changeText(
        screen.getByTestId("organization-input"),
        "Test Org"
      );
    });
  }
  await screen.findByPlaceholderText("Verification code");
  await waitFor(() => {
    fireEvent.changeText(screen.getByTestId("code-input"), "123123"); // Valid code
  });
  await waitFor(() => {
    fireEvent.press(screen.getByText("Validate code"));
  });
};

export const loginSuccess = async (newAccount: number = 0) => {
  await sendCodeSuccess(newAccount);

  mockUpcomingInterviews();

  await validateCodeSuccess(newAccount);
};
