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
 * Mocks a response for a valid authentication token.
 */
export const mockValidToken = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("check_token")).reply(200, {
      validToken: true,
    });
  }
};
