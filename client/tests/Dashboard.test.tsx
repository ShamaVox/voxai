import React from "react";
import { waitFor } from "@testing-library/react-native";
import Dashboard from "../src/Dashboard";
import { SERVER_ENDPOINT } from "../src/utils/Axios";
import { mockInsights, mockTokenValidation } from "./utils/MockRequests";
import { renderComponent } from "./utils/Render";
import { verifyInsightsData } from "./actions/DashboardActions";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

test("fetches insights data", async () => {
  mockInsights();
  renderComponent(Dashboard, true);

  // Assert that insights data is displayed
  await verifyInsightsData();
});

test("calls logout and navigates to login if token is invalid", async () => {
  mockTokenValidation("insights", false);
  renderComponent(Dashboard, true);
  await waitFor(() => {
    expect(mockNavigate).toHaveBeenCalledWith("Login");
  });
});
