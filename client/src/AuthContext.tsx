import React, {
  createContext,
  useState,
  FC,
  ReactNode,
  useEffect,
} from "react";
import { useCookies } from "react-cookie";
import { AUTH_LOGGING } from "./config/Logging";

interface AuthContextProps {
  isLoggedIn: boolean;
  email: string;
  username: string;
  handleLogin: (
    email: string,
    name: string,
    authToken: string
  ) => Promise<void>;
  authToken: string;
  handleLogout: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  email: "",
  username: "",
  handleLogin: async (email: string, name: string, authToken: string) => {},
  authToken: "",
  handleLogout: async () => {},
});

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [cookies, setCookie, removeCookie] = useCookies(["voxai"]);

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  // TODO: Configure cookie settings properly
  useEffect(() => {
    if (!isLoggedIn) {
      // Log in if there are cookies on first load
      if (cookies["voxai"] && cookies["voxai"]["auth"]) {
        handleLogin(
          cookies["voxai"]["email"],
          cookies["voxai"]["name"],
          cookies["voxai"]["authToken"]
        );
      }
    } else {
      // Set cookies whenever data changes
      setCookie("voxai", {
        auth: {
          email: email,
          username: username,
          authToken: authToken,
        },
      });
    }
  }, [isLoggedIn]);

  const handleLogin: (
    email: string,
    name: string,
    authToken: string
  ) => Promise<void> = async (
    email: string,
    name: string,
    authToken: string
  ) => {
    setIsLoggedIn(true);
    setEmail(email);
    setUsername(name);
    setAuthToken(authToken);
    if (AUTH_LOGGING) {
      console.log("Username set to: ", username);
    }
  };

  const handleLogout: () => Promise<void> = async () => {
    setCookie("voxai", {
      auth: null,
    });
    setIsLoggedIn(false);
    setEmail("");
    setUsername("");
    setAuthToken("");
  };

  if (AUTH_LOGGING) {
    console.log("isLoggedIn value:", isLoggedIn);
    console.log("email value:", email);
  }

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn,
        email,
        username,
        handleLogin,
        authToken,
        handleLogout
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
