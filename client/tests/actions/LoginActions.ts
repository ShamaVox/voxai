import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
  mockUpcomingInterviews,
} from "../utils/MockRequests";
import { fireEvent, waitFor, screen } from "@testing-library/react-native";

export const loginFormEntry = async (
  formData: Record<string, string>,
  buttonText: string,
  expectedError: string = "",
  errorDisplays: boolean = true
) => {
  await waitFor(() => {
    for (var testId in formData) {
      fireEvent.changeText(screen.getByTestId(testId), formData[testId]);
    }
  });
  await waitFor(() => {
    fireEvent.press(screen.getByText(buttonText));
  });
  if (expectedError) {
    if (errorDisplays) {
      await screen.findByText(expectedError);
    } else {
      await waitFor(() => {
        expect(screen.queryByText("Invalid email")).toBeNull();
      });
    }
  }
};

export const sendCodeSuccess = async (newAccount: number = 0) => {
  let email;
  if (newAccount) {
    mockNewAccount();
    email = "new" + newAccount.toString() + "@email.com";
  } else {
    mockAccountExists();
    email = "existing@email.com";
  }
  await loginFormEntry({ "email-input": email }, "Send code");
};

export const validateCodeSuccess = async (
  newAccount: number = 0,
  validateNavigation: boolean = false
) => {
  mockValidCode(newAccount ? "New User" : "Test Name");
  var formData: Record<string, string> = { "code-input": "123123" };
  if (newAccount) {
    formData["name-input"] = "New User";
    formData["organization-input"] = "Test Org";
  }
  await loginFormEntry(
    formData,
    "Validate code",
    validateNavigation ? "My Interviews" : ""
  );
  await waitFor(() => {});
};

export const loginSuccess = async (
  newAccount: number = 0,
  validateNavigation: boolean = false
) => {
  await sendCodeSuccess(newAccount);

  mockUpcomingInterviews();

  await validateCodeSuccess(newAccount, validateNavigation);
};
