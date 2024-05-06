import {
  mockAccountExists,
  mockNewAccount,
  mockValidCode,
  mockUpcomingInterviews,
} from "../utils/MockRequests";
import { fireEvent, waitFor, screen, act } from "@testing-library/react-native";

/**
 * Simulates user input in the login form and triggers the specified button press.
 *
 * @param formData An object with test IDs as keys and input values as values.
 * @param buttonText The text of the button to press.
 * @param expectedError (Optional) The expected error message to appear.
 * @param errorDisplays (Optional) Whether the error message should be displayed. Defaults to true.
 */
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

/**
 * Simulates successful sending of verification code for existing or new account.
 *
 * @param newAccount - Optional account number for creating a new account. Defaults to 0 (existing account).
 */
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

/**
 * Simulates successful validation of verification code for existing or new account.
 *
 * @param newAccount - Optional account number for creating a new account. Defaults to 0 (existing account).
 */
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
};

/**
 * Simulates a successful login process, including sending and validating code.
 *
 * @param newAccount - Optional account number for creating a new account. Defaults to 0 (existing account).
 */
export const loginSuccess = async (
  newAccount: number = 0,
  validateNavigation: boolean = false
) => {
  await sendCodeSuccess(newAccount);

  mockUpcomingInterviews();

  await validateCodeSuccess(newAccount, validateNavigation);
};
