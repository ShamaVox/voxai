// Header.test.tsx

import React from "react";
import {
  render,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react-native";
import Header from "../src/Header";
import { useNavigation } from "@react-navigation/native";
import { renderComponent } from "./utils/Render";
import { clearCookies } from "./utils/Cookies";
import { verifyHeader, logout } from "./actions/HeaderActions";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

beforeEach(() => {
  jest.clearAllMocks();
  clearCookies();
});

test("renders logo and logged out profile icon", async () => {
  renderComponent(Header, false);
  await verifyHeader(false);
});

test("renders logo and logged in profile icon", async () => {
  renderComponent(Header, true, "TestUser");
  await verifyHeader(true, "TestUser");
});

test("navigates to Home on logo press when logged out", async () => {
  renderComponent(Header, false);

  await waitFor(() => {
    fireEvent.press(screen.getByTestId("logo"));
    expect(mockNavigate).toHaveBeenCalledWith("Home");
  });
  await waitFor(() => {
    fireEvent.press(screen.getByTestId("profile-container"));
    expect(mockNavigate).toHaveBeenCalledWith("Login");
  });
});

test("navigates to Dashboard on logo press when logged in", async () => {
  renderComponent(Header, true);

  await waitFor(() => {
    fireEvent.press(screen.getByTestId("logo"));
    expect(mockNavigate).toHaveBeenCalledWith("Dashboard");
  });
});

test("successfully logs out", async () => {
  renderComponent(Header, true, "Logout Test Username");
  await logout("Logout Test Username");
});
