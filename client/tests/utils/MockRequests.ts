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

export const mockAccountExists = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("send_code")).reply(200, {
      account_exists: true,
      message: "Verification code sent successfully",
    });
  }
};

export const mockNewAccount = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("send_code")).reply(201, {
      account_exists: false,
      message: "Verification code sent successfully",
    });
  }
};

export const mockInvalidCode = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("validate_code")).reply(400, {
      message: "Invalid verification code",
    });
  }
};

export const mockValidCode = () => {
  if (mock) {
    mockAdapter.onPost(SERVER_ENDPOINT("validate_code")).reply(200, {
      message: "Verification code is valid",
      name: "Test Name",
      account_type: "Recruiter",
      email: "test@email.com", // Don't check this value: it will be different in integration tests
      authToken: "AUTHTOKEN",
    });
  }
};

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
