import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
import NavBar from "../src/NavBar";
import { AuthContext } from "../src/AuthContext";
// import "jest-styled-components";

const mockNavigate = jest.fn();
jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
    addListener: () => jest.fn(),
  }),
}));

const renderNavBar = (isLoggedIn, activeRouteName) => {
  return render(
    <AuthContext.Provider value={{ isLoggedIn }}>
      <NavBar />
    </AuthContext.Provider>
  );
};

beforeEach(() => {
  jest.clearAllMocks();
});

test("renders nothing when logged out", () => {
  const { queryByTestId } = renderNavBar(false, "");
  expect(queryByTestId("nav-bar")).toBeNull();
});

test("renders sections and buttons when logged in", () => {
  const { getByTestId, getAllByTestId } = renderNavBar(true, "Home");
  expect(getByTestId("nav-bar")).toBeTruthy();
  expect(getByTestId("section-general")).toBeTruthy();
  expect(getByTestId("section-support")).toBeTruthy();
  expect(getByTestId("nav-button-home")).toBeTruthy();
  expect(getByTestId("nav-button-dashboard")).toBeTruthy();
  expect(getByTestId("nav-button-candidates")).toBeTruthy();
  expect(getByTestId("nav-button-settings")).toBeTruthy();
});

// Doesn't work due to library issues
// test("highlights active route button", () => {
//   const { getByTestId } = renderNavBar(true, "Dashboard");
//   expect(getByTestId("nav-button-dashboard")).toHaveStyleRule(
//     "backgroundColor",
//     "#FFFFFF95"
//   );
//});

test("navigates to correct screen on button press", () => {
  const { getByTestId } = renderNavBar(true, "Home");

  // Simulate button presses and check navigation calls
  fireEvent.press(getByTestId("nav-button-home"));
  expect(mockNavigate).toHaveBeenCalledWith("Home");

  fireEvent.press(getByTestId("nav-button-dashboard"));
  expect(mockNavigate).toHaveBeenCalledWith("Dashboard");

  fireEvent.press(getByTestId("nav-button-candidates"));
  expect(mockNavigate).toHaveBeenCalledWith("Candidates");
});
