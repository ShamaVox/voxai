import React, { createContext, useState } from "react";
import axios from "axios";
import { AUTH_LOGGING, SERVER_URL } from "./Constants";

interface AuthContextProps {
  isLoggedIn: boolean;
  username: string;
  handleLogin: (username: string, password: string) => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  username: "",
  handleLogin: async () => false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  const handleLogin: AuthContextProps["handleLogin"] = async (
    username,
    password
  ) => {
    try {
      const response = await axios.post(SERVER_URL + "login", {
        username,
        password,
      });
      if (response.status === 200) {
        setIsLoggedIn(true);
        setUsername(username);
        return true;
      } else {
        if (AUTH_LOGGING) {
          console.log("Login failed");
        }
        return false;
      }
    } catch (error) {
      console.error("Error during login:", error);
      return false;
    }
  };

  if (AUTH_LOGGING) {
    console.log("isLoggedIn value:", isLoggedIn);
    console.log("username value:", username);
  }

  return (
    <AuthContext.Provider value={{ isLoggedIn, username, handleLogin }}>
      {children}
    </AuthContext.Provider>
  );
};
