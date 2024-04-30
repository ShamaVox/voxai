// DashboardActions.ts

import { screen } from "@testing-library/react-native";

export const verifyInsightsData = async () => {
  // Assert that insights data is displayed
  await screen.findByText("3");
  await screen.findByText("85%");
  await screen.findByText("6 days");
  await screen.findByText("-10%");
  await screen.findByText("20K - 129K");
};
