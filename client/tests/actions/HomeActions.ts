import { fireEvent, waitFor } from "@testing-library/react-native";

export const verifyLoggedOutHomepage = (getByText) => {
  expect(getByText("This is a placeholder homepage")).toBeTruthy();
  expect(getByText("Login")).toBeTruthy();
};

export const verifyUpcomingInterviews = async (findByText) => {
  // Wait for interviews to be fetched and rendered
  await findByText("John Doe");
};

export const verifyTabSwitch = async (
  getByText,
  queryByText,
  findByText,
  queryAllByTestId,
  getByTestId,
  tabName: "Upcoming" | "Completed" | "Both"
) => {
  if (tabName === "Both") {
    await verifyTabSwitch(
      getByText,
      queryByText,
      findByText,
      queryAllByTestId,
      getByTestId,
      "Completed"
    );
    await verifyTabSwitch(
      getByText,
      queryByText,
      findByText,
      queryAllByTestId,
      getByTestId,
      "Upcoming"
    );
  } else {
    // Click on the specified tab
    if (tabName === "Completed") {
      await waitFor(() => {
        fireEvent.press(getByTestId("completed-tab"));
        expect(
          queryAllByTestId("interview-list")[0].props.data.length
        ).toBeLessThan(5);
        expect(queryByText("John Doe")).toBeNull();
      });
    } else if (tabName === "Upcoming") {
      await waitFor(() => {
        fireEvent.press(getByTestId("upcoming-tab"));
      });
    }
  }
  // Assert visibility of interviews based on the selected tab
  if (tabName === "Completed") {
    await waitFor(() => {
      //expect(queryAllByTestId("interview-list")[0].props.data.length).toBe(0);
    });
  } else if (tabName === "Upcoming") {
    await verifyUpcomingInterviews(findByText);
  }
};

export const verifyHomeElements = async (
  getByText,
  queryByText,
  findByText,
  queryAllByTestId,
  getByTestId
) => {
  await verifyTabSwitch(
    getByText,
    queryByText,
    findByText,
    queryAllByTestId,
    getByTestId,
    "Both"
  );
};
