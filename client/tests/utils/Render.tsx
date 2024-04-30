import { render } from "@testing-library/react-native";
import AuthContext from "../../src/AuthContext";
import Header from "../../src/Header";
import Home from "../../src/Home";
import Login from "../../src/Login";
import NavBar from "../../src/NavBar";

/**
 * Renders the Header component within an AuthContext provider.
 *
 * @param isLoggedIn Whether the user is currently logged in.
 * @param username (Optional) The username to display in the header.
 * @returns The rendered Header component.
 */
export const renderHeader: (
  isLoggedIn: boolean,
  username?: string
) => Object = (isLoggedIn, username) => {
  return render(
    <AuthContext.Provider
      value={{
        isLoggedIn: isLoggedIn,
        username: username,
        email: "",
        handleLogin: async () => {},
        authToken: "",
        handleLogout: async () => {},
      }}
    >
      <Header />
    </AuthContext.Provider>
  );
};

/**
 * Renders the Home component with the specified login state.
 *
 * @param isLoggedIn - Boolean indicating whether the user is logged in.
 */
export const renderHome: (isLoggedIn: boolean) => Object = (isLoggedIn) => {
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
};

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
      }}
    >
      <Login />
    </AuthContext.Provider>
  );
};

/**
 * Renders the NavBar component based on the login state.
 *
 * @param isLoggedIn - Boolean indicating whether the user is logged in.
 */
export const renderNavBar: (a: boolean) => Object = (isLoggedIn: boolean) => {
  return render(
    <AuthContext.Provider
      value={{
        isLoggedIn: isLoggedIn,
        email: "",
        username: "",
        handleLogin: async () => {},
        authToken: "",
        handleLogout: async () => {},
      }}
    >
      <NavBar />
    </AuthContext.Provider>
  );
};
