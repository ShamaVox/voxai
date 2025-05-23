import React, {
  createContext,
  useState,
  useContext,
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
    authToken: string,
    onboarded: boolean,
    okta: boolean
  ) => Promise<void>;
  authToken: string;
  handleLogout: (a: boolean) => Promise<void>;
  onboarded: boolean;
  okta: boolean;
  finishOnboarding: () => void;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  email: "",
  username: "",
  handleLogin: async (email: string, name: string, authToken: string, onboarded: boolean, okta: boolean) => {},
  authToken: "",
  handleLogout: async (a: boolean) => {},
  onboarded: false,
  okta: false,
  finishOnboarding: () => {},
});

/**
 * The AuthProvider component manages the authentication state and provides
 * functions for login, logout, and access to user information.
 */
export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [onboarded, setOnboarded] = useState(false);
  const [cookies, setCookie, removeCookie] = useCookies(["voxai"]);
  const [needTokenCheck, setNeedTokenCheck] = useState(false);
  const [firstLoad, setFirstLoad] = useState(true);
  // Buffer login navigation if navigation is not loaded
  const [loginNavigationPending, setLoginNavigationPending] = useState(false);
  const navigation = useNavigation();
  const [okta, setOkta] = useState(false); // may need to set some kind of token

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  // TODO: Configure cookie settings properly
  useEffect(() => {
    if (loginNavigationPending) {
      // Handling this here ensures navigation is fully initialized if we log out on initial page load
      navigation.navigate("Login");
      setLoginNavigationPending(false);
      return;
    }
    if (!isLoggedIn && firstLoad) {
      // Log in if there are cookies on first load
      if (AUTH_LOGGING) {
        console.log("Cookies: ", cookies);
      }
      if (cookies.voxai && cookies.voxai.auth) {
        axios
          .post(SERVER_ENDPOINT("check_token"), {
            authToken: cookies.voxai.auth.authToken,
          })
          .then((response) => {
            if (response.data.validToken === true) {
              handleLogin(
                cookies.voxai.auth.email,
                cookies.voxai.auth.username,
                cookies.voxai.auth.authToken,
                Boolean(cookies.voxai.auth.onboarded),
                Boolean(cookies.voxai.auth.okta),
              );
            }
          })
          .catch((error) => {
            if (AUTH_LOGGING) {
              console.log("Auth token in cookies was invalid");
            }
            handleLogout(true);
          });
      }
      setFirstLoad(false);
    } else {
      if (AUTH_LOGGING) {
        console.log(cookies);
      }
      // Update the cookie if it is different
      let currentAuthCookie: Record<string, string> = {
        email: email,
        username: username,
        authToken: authToken,
        onboarded: String(onboarded),
        okta: String(okta),
      };
      if (
        cookies.voxai == undefined ||
        !arraysEqual(cookies.voxai.auth, currentAuthCookie)
      ) {
        setCookie("voxai", { auth: currentAuthCookie });
      }
    }
  }, [isLoggedIn, loginNavigationPending]);

  /**
   * Handles user login by setting authentication state and storing information in cookies.
   *
   * @param email The user's email address.
   * @param name The user's name.
   * @param authToken The authentication token.
   */
  const handleLogin: (
    a: string,
    b: string,
    c: string,
    d: boolean,
    e: boolean
  ) => Promise<void> = async (email, name, authToken, onboarded, okta) => {
    setEmail(email);
    setUsername(name);
    setAuthToken(authToken);
    setOnboarded(onboarded);
    setOkta(okta);
    if (AUTH_LOGGING) {
      console.log("Username set to: ", username);
    }
    setIsLoggedIn(true);
  };

  /**
   * Handles user logout by clearing authentication state and removing cookies.
   */
  const handleLogout: (a: boolean) => Promise<void> = async (
    navigateToLogin
  ) => {
    setCookie("voxai", {
      auth: null,
    });
    setIsLoggedIn(false);
    setEmail("");
    setUsername("");
    setAuthToken("");
    setOnboarded(false);
    try {
      await axios.post(SERVER_ENDPOINT("logout"), {
        authToken: authToken,
      });
    } catch (error) {
      if (AUTH_LOGGING) {
        console.log("Error during logout: ", error);
      }
    }
    if (navigateToLogin) {
      setLoginNavigationPending(true);
    }
  };

  if (AUTH_LOGGING) {
    console.log("isLoggedIn value:", isLoggedIn);
    console.log("email value:", email);
  }

  const finishOnboarding = () => 
  {
    setOnboarded(true);
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
        onboarded,
        finishOnboarding,
        okta
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
export default AuthProvider;
