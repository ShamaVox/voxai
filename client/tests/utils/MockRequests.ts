import axios from "axios";
import { SERVER_ENDPOINT } from "../../src/utils/Axios";
import mock from "../config/Config";
import MockAdapter from "axios-mock-adapter";

let mockAdapter = null;
if (mock) {
  mockAdapter = new MockAdapter(axios);
}

beforeEach(() => {
  if (mock) {
    mockAdapter.reset();
  }
});

/**
 * Helper function to delay responses.
 * from https://github.com/ctimmerm/axios-mock-adapter/issues/232
 *
 * @param delay - Amount to delay the response.
 * @param response - The response to return.
 */
const withDelay = <T>(
  delay: number,
  response: T
): ((config: any) => Promise<T>) => {
  return (config: any): Promise<T> => {
    return new Promise<T>((resolve, reject) => {
      setTimeout(() => {
        resolve(response);
      }, delay);
    });
  };
};

/**
 * Mocks the API response for fetching upcoming interviews.
 */
export const mockUpcomingInterviews = () => {
  if (mock) {
    mockAdapter.onGet(SERVER_ENDPOINT("interviews")).reply(200, [
      {
        id: 1,
        date: "2023-12-15",
        time: "10:00 AM",
        candidateName: "John Doe",
      },
    ]);
  }
};

/**
 * Mocks the API response for checking if an account exists.
 */
export const mockAccountExists = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("send_code")).reply(200, {
      account_exists: true,
      message: "Verification code sent successfully",
    });
  }
};

/**
 * Mocks a response indicating a new account was created when sending a verification code.
 */
export const mockNewAccount = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("send_code")).reply(201, {
      account_exists: false,
      message: "Verification code sent successfully",
    });
  }
};

/**
 * Mocks a response for an invalid verification code during login.
 */
export const mockInvalidCode = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("validate_code")).reply(400, {
      message: "Invalid verification code",
    });
  }
};

/**
 * Mocks a successful verification code validation with provided user details.
 *
 * @param name The name associated with the validated account.
 */
export const mockValidCode: (name: string) => void = (name) => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("validate_code")).reply(200, {
      message: "Verification code is valid",
      name: name,
      account_type: "Recruiter",
      email: "test@email.com", // Don't check this value: it will be different in integration tests
      authToken: "AUTHTOKEN",
    });
  }
};

/**
 * Mocks a successful response for fetching insights data.
 */
export const mockInsights = () => {
  if (mock) {
    mockAdapter.onGet(SERVER_ENDPOINT("insights")).reply(200, {
      candidateStage: 3,
      fittingJobApplication: 85,
      fittingJobApplicationPercentage: 29,
      averageInterviewPace: 6,
      averageInterviewPacePercentage: -10,
      lowerCompensationRange: 20,
      upperCompensationRange: 129,
    });
  }
};

/**
 * Mocks a response for an authentication token check.
 *
 * @param api The API to mock the response from.
 * @param valid Whether to mock a successful or failed check.
 */
export const mockTokenValidation = (
  api: string = "check_token",
  valid: boolean = true
) => {
  if (mock) {
    mockAdapter.onAny(SERVER_ENDPOINT(api)).reply(valid ? 200 : 401, {
      validToken: valid,
    });
  }
};

/**
 * Mocks a response for a logout signal to server.
 *
 * @param delay - How much time to wait before responding.
 */
export const mockLogout = () => {
  if (mock) {
    mockAdapter.onAny(SERVER_ENDPOINT("logout")).reply(200, {});
  }
};
