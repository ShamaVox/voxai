import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import Dashboard from "../src/Dashboard";
import { SERVER_ENDPOINT } from "../src/Constants";
import { mockInsights } from "./utils/MockRequests";

test("fetches insights data", async () => {
  mockInsights();
  const { findByText } = render(<Dashboard />);

  // Assert that insights data is displayed
  await findByText("Interviewing");
  await findByText("85%");
  await findByText("6 days");
  await findByText("-10%");
  await findByText("20K - 130K");
});
