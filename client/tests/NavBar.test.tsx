import React from "react";
import {
  render,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react-native";
import NavBar from "../src/NavBar";
import { renderComponent } from "./utils/Render";
import { clearCookies } from "./utils/Cookies";
// import "jest-styled-components";

const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    addListener: () => jest.fn(),
  }),
}));

beforeEach(() => {
  jest.clearAllMocks();
  clearCookies();
});

test("renders nothing when logged out", async () => {
  renderComponent(NavBar, false);
  await waitFor(() => {
    expect(screen.queryByTestId("nav-bar")).toBeNull();
  });
});

test("renders sections and buttons when logged in", async () => {
  renderComponent(NavBar, true);
  await waitFor(() => {
    expect(screen.getByTestId("nav-bar")).toBeTruthy();
    expect(screen.getByTestId("section-general")).toBeTruthy();
    expect(screen.getByTestId("section-support")).toBeTruthy();
    expect(screen.getByTestId("nav-button-home")).toBeTruthy();
    expect(screen.getByTestId("nav-button-dashboard")).toBeTruthy();
    expect(screen.getByTestId("nav-button-candidates")).toBeTruthy();
    expect(screen.getByTestId("nav-button-settings")).toBeTruthy();
  });
});

// Doesn't work due to library issues
// test("highlights active route button", () => {
//   const { screen.getByTestId } = renderComponent(NavBar, true);
//   expect(screen.getByTestId("nav-button-dashboard")).toHaveStyleRule(
//     "backgroundColor",
//     "#FFFFFF95"
//   );
//});

test("navigates to correct screen on button press", async () => {
  renderComponent(NavBar, true);

  // Simulate button presses and check navigation calls
  await waitFor(() => {
    fireEvent.press(screen.getByTestId("nav-button-home"));
    expect(mockNavigate).toHaveBeenCalledWith("Home");
  });

  await waitFor(() => {
    fireEvent.press(screen.getByTestId("nav-button-dashboard"));
    expect(mockNavigate).toHaveBeenCalledWith("Dashboard");
  });

  await waitFor(() => {
    fireEvent.press(screen.getByTestId("nav-button-candidates"));
    expect(mockNavigate).toHaveBeenCalledWith("Candidates");
  });
});
