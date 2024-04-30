import { fireEvent, waitFor, screen } from "@testing-library/react-native";

export const verifyLoggedOutHomepage = () => {
  expect(screen.getByText("This is a placeholder homepage")).toBeTruthy();
  expect(screen.getByText("Login")).toBeTruthy();
};

export const verifyUpcomingInterviews = async () => {
  // Wait for interviews to be fetched and rendered
  await screen.findByText("John Doe");
};

export const verifyTabSwitch = async (
  tabName: "Upcoming" | "Completed" | "Both"
) => {
  if (tabName === "Both") {
    await verifyTabSwitch("Completed");
    await verifyTabSwitch("Upcoming");
  } else {
    // Click on the specified tab
    if (tabName === "Completed") {
      await waitFor(() => {
        fireEvent.press(screen.getByTestId("completed-tab"));
      });
      // await waitFor(async () => {
      //   fireEvent.press(screen.getByTestId("completed-tab"));
      //   await screen.findByText("This is a placeholder for the Completed tab");
      //   expect(
      //     await screen.queryAllByTestId("interview-list")[0].props.data.length
      //   ).toBeLessThan(5);
      //   expect(screen.queryByText("John Doe")).toBeNull();
      // });
    } else if (tabName === "Upcoming") {
      await waitFor(() => {
        fireEvent.press(screen.getByTestId("upcoming-tab"));
      });
    }
  }
  // Assert visibility of interviews based on the selected tab
  if (tabName === "Completed") {
    await screen.findByText("This is a placeholder for the Completed tab");
    //expect(screen.queryAllByTestId("interview-list")[0].props.data.length).toBe(0);
  } else if (tabName === "Upcoming") {
    await verifyUpcomingInterviews();
  }
};

export const verifyHomeElements = async () => {
  // Will check other home elements when they are added
  await verifyTabSwitch("Both");
};
