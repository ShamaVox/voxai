// Header.test.tsx

import React from "react";
import { render, fireEvent } from "@testing-library/react-native";
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

test("renders logo and logged out profile icon", () => {
  const { getByTestId } = render(
    <AuthContext.Provider value={{ isLoggedIn: false }}>
      <Header />
    </AuthContext.Provider>
  );

  expect(getByTestId("logo")).toBeTruthy();
  expect(getByTestId("profile-icon-logged-out")).toBeTruthy();
});

test("renders logo and logged in profile icon", () => {
  const { getByTestId } = render(
    <AuthContext.Provider value={{ isLoggedIn: true, username: "TestUser" }}>
      <Header />
    </AuthContext.Provider>
  );

  expect(getByTestId("logo")).toBeTruthy();
  expect(getByTestId("profile-icon-logged-in")).toBeTruthy();
});

test("navigates to Home on logo press when logged out", () => {
  const { getByTestId } = render(
    <AuthContext.Provider value={{ isLoggedIn: false }}>
      <Header />
    </AuthContext.Provider>
  );

  fireEvent.press(getByTestId("logo"));
  expect(mockNavigate).toHaveBeenCalledWith("Home");

  fireEvent.press(getByTestId("profile-container"));
  expect(mockNavigate).toHaveBeenCalledWith("Login");
});

test("navigates to Dashboard on logo press when logged in", () => {
  const { getByTestId } = render(
    <AuthContext.Provider value={{ isLoggedIn: true }}>
      <Header />
    </AuthContext.Provider>
  );

  fireEvent.press(getByTestId("logo"));
  expect(mockNavigate).toHaveBeenCalledWith("Dashboard");
});
