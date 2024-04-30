import React from "react";
import { render, fireEvent, screen } from "@testing-library/react-native";
import Home from "../src/Home";
import { AuthContext } from "../src/AuthContext";
import { mockUpcomingInterviews } from "./utils/MockRequests";
import {
  verifyLoggedOutHomepage,
  verifyUpcomingInterviews,
  verifyTabSwitch,
} from "./actions/HomeActions";

const mockNavigate = jest.fn();

jest.mock("@react-navigation/native", () => ({
  useNavigation: () => ({
    navigate: mockNavigate,
  }),
}));

function renderHome(isLoggedIn: boolean) {
  return render(
    <AuthContext.Provider
      value={{
        isLoggedIn: isLoggedIn,
        username: "",
        email: "",
        handleLogin: async () => {},
        authToken: "",
        handleLogout: async () => {},
      }}
    >
      <Home />
    </AuthContext.Provider>
  );
}

test("renders placeholder content when logged out", () => {
  renderHome(false);
  verifyLoggedOutHomepage();
});

test("fetches and renders interviews when logged in", async () => {
  mockUpcomingInterviews();
  renderHome(true);
  await verifyUpcomingInterviews();
});

test("switches between Upcoming and Completed tabs", async () => {
  mockUpcomingInterviews();
  renderHome(true);
  await verifyTabSwitch("Both");
});
