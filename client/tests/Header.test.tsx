// Header.test.tsx

import React from "react";
import { render, fireEvent, screen } from "@testing-library/react-native";
import Header from "../src/Header";
import { AuthContext } from "../src/AuthContext";
import { useNavigation } from "@react-navigation/native";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

beforeEach(() => {
  jest.clearAllMocks();
});

function renderHeader(isLoggedIn: boolean, username = "") {
  return render(
    <AuthContext.Provider
      value={{
        isLoggedIn: isLoggedIn,
        username: username,
        email: "",
        handleLogin: async () => {},
      }}
    >
      <Header />
    </AuthContext.Provider>
  );
}

test("renders logo and logged out profile icon", () => {
  renderHeader(false);

  expect(screen.getByTestId("logo")).toBeTruthy();
  expect(screen.getByTestId("profile-icon-logged-out")).toBeTruthy();
});

test("renders logo and logged in profile icon", () => {
  renderHeader(true, "TestUser");

  expect(screen.getByTestId("logo")).toBeTruthy();
  expect(screen.getByTestId("profile-icon-logged-in")).toBeTruthy();
});

test("navigates to Home on logo press when logged out", () => {
  renderHeader(false);

  fireEvent.press(screen.getByTestId("logo"));
  expect(mockNavigate).toHaveBeenCalledWith("Home");

  fireEvent.press(screen.getByTestId("profile-container"));
  expect(mockNavigate).toHaveBeenCalledWith("Login");
});

test("navigates to Dashboard on logo press when logged in", () => {
  renderHeader(true);

  fireEvent.press(screen.getByTestId("logo"));
  expect(mockNavigate).toHaveBeenCalledWith("Dashboard");
});
