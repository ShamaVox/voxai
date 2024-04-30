import React, {
  createContext,
  useState,
  FC,
  ReactNode,
  useEffect,
} from "react";
import { useCookies } from "react-cookie";
import { AUTH_LOGGING } from "./config/Logging";
import axios from "axios";
import { SERVER_ENDPOINT } from "./utils/Axios";
import { arraysEqual } from "./utils/Arrays";
import { useNavigation } from "@react-navigation/native";

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
  const [needTokenCheck, setNeedTokenCheck] = useState(false);
  const navigation = useNavigation();

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  // TODO: Configure cookie settings properly
  useEffect(() => {
    if (!isLoggedIn) {
      // Log in if there are cookies on first load
      if (cookies["voxai"] && cookies["voxai"]["auth"]) {
        axios
          .post(SERVER_ENDPOINT("check_token"), {
            authToken: cookies["voxai"]["auth"]["authToken"],
          })
          .then((response) => {
            if (response.data.validToken === true) {
              handleLogin(
                cookies["voxai"]["auth"]["email"],
                cookies["voxai"]["auth"]["username"],
                cookies["voxai"]["auth"]["authToken"]
              );
            }
          });
      }
    } else {
      console.log(cookies);
      // Update the cookie if it is different
      let currentAuthCookie: Record<string, string> = {
        email: email,
        username: username,
        authToken: authToken,
      };
      if (
        cookies["voxai"] == undefined ||
        !arraysEqual(cookies["voxai"]["auth"], currentAuthCookie)
      ) {
        setCookie("voxai", { auth: currentAuthCookie });
      }
    }
  }, [isLoggedIn]);

  const handleLogin: (
    a: string,
    b: string,
    c: string
  ) => Promise<void> = async (email, name, authToken) => {
    setEmail(email);
    setUsername(name);
    setAuthToken(authToken);
    if (AUTH_LOGGING) {
      console.log("Username set to: ", username);
    }
    setIsLoggedIn(true);
  };

  const handleLogout: () => Promise<void> = async () => {
    setCookie("voxai", {
      auth: null,
    });
    setIsLoggedIn(false);
    setEmail("");
    setUsername("");
    setAuthToken("");
    axios.post(SERVER_ENDPOINT("logout"), {
      authToken: authToken,
    });
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
        handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
