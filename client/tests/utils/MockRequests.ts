import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import { SERVER_ENDPOINT } from "../../src/Constants";

const mockAdapter = new MockAdapter(axios);

beforeEach(() => {
  mockAdapter.reset();
});

export const mockUpcomingInterviews = () => {
  mockAdapter.onGet(SERVER_ENDPOINT("interviews")).reply(200, [
    {
      id: 1,
      date: "2023-12-15",
      time: "10:00 AM",
      candidateName: "John Doe",
    },
  ]);
};

export const mockAccountExists = () => {
  mockAdapter.onPost(SERVER_ENDPOINT("send_code")).reply(200, {
    account_exists: true,
    message: "Verification code sent successfully",
  });
};

export const mockNewAccount = () => {
  mockAdapter.onPost(SERVER_ENDPOINT("send_code")).reply(201, {
    account_exists: false,
    message: "Verification code sent successfully",
  });
};

export const mockInvalidCode = () => {
  mockAdapter.onPost(SERVER_ENDPOINT("validate_code")).reply(400, {
    message: "Invalid verification code",
  });
};

export const mockValidCode = () => {
  mockAdapter.onPost(SERVER_ENDPOINT("validate_code")).reply(200, {
    message: "Verification code is valid",
    name: "Test Name",
    account_type: "Recruiter",
    email: "test@email.com",
  });
};

export const mockInsights = () => {
  mockAdapter.onGet(SERVER_ENDPOINT("insights")).reply(200, {
    candidateStage: "Interviewing",
    fittingJobApplication: 85,
    fittingJobApplicationPercentage: 30,
    averageInterviewPace: 6,
    averageInterviewPacePercentage: -10,
    lowerCompensationRange: 20,
    upperCompensationRange: 130,
  });
};
