// DashboardActions.ts

export const verifyInsightsData = async (findByText) => {
  // Assert that insights data is displayed
  await findByText("3");
  await findByText("85%");
  await findByText("6 days");
  await findByText("-10%");
  await findByText("20K - 129K");
};
