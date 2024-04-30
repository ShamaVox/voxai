// Header.test.tsx

import React from "react";
import { render, fireEvent, screen } from "@testing-library/react-native";
import Header from "../src/Header";
import { useNavigation } from "@react-navigation/native";
import { renderHeader } from "./utils/Render";
import { verifyHeader } from "./actions/HeaderActions";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

beforeEach(() => {
  jest.clearAllMocks();
});

test("renders logo and logged out profile icon", async () => {
  renderHeader(false);
  await verifyHeader(false);
});

test("renders logo and logged in profile icon", async () => {
  renderHeader(true, "TestUser");
  await verifyHeader(true, "TestUser");
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
