import { FC, createElement, useContext } from "react";
import { Text } from "react-native";
import { render, screen, waitFor } from "@testing-library/react-native";
import AuthProvider, { AuthContext } from "../../src/AuthContext";
import Header from "../../src/Header";
import Home from "../../src/Home";
import Login from "../../src/Login";
import NavBar from "../../src/NavBar";
import { setCookies } from "./Cookies";
import { mockTokenValidation } from "./MockRequests";

/**
 * Renders a component with the specified login state.
 *
 * @param component - The component to render.
 * @param isLoggedIn - Boolean indicating whether the user is logged in.
 * @param username (Optional) - The username of the logged in user.
 */
export const renderComponent = (
  component: FC,
  isLoggedIn: boolean,
  username: string = "Test User",
  tokenCheckSuccess: boolean = true
) => {
  if (isLoggedIn) {
    mockTokenValidation("check_token", tokenCheckSuccess);
    setCookies({
      auth: {
        username: username,
        email: "test@email.com",
        authToken: "AUTHTOKEN",
      },
    });
  }
  return render(<AuthProvider>{createElement(component)}</AuthProvider>);
};

/**
 * Renders the Login component with a mocked handleLogin function.
 *
 * @param mockHandleLogin - The mock to pass in place of handleLogin.
 */
export const renderLoginFromMock: (
  mockHandleLogin: (a: string, b: string, c: string) => Promise<void>
) => Object = (mockHandleLogin) => {
  return render(
    <AuthContext.Provider
      value={{
        isLoggedIn: false,
        handleLogin: mockHandleLogin,
        username: "",
        email: "",
        authToken: "",
        handleLogout: async () => {},
        onboarded: false,
        okta: false,
        finishOnboarding: () => {},
      }}
    >
      <Login />
    </AuthContext.Provider>
  );
};
