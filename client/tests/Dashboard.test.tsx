import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import Dashboard from "../src/Dashboard";
import { SERVER_ENDPOINT } from "../src/utils/Axios";
import { mockInsights } from "./utils/MockRequests";
import { verifyInsightsData } from "./actions/DashboardActions";

test("fetches insights data", async () => {
  mockInsights();
  render(<Dashboard />);

  // Assert that insights data is displayed
  await verifyInsightsData();
});
