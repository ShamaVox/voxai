import React, { createContext, useState, FC, ReactNode } from "react";
import { AUTH_LOGGING } from "./config/Logging";

interface AuthContextProps {
  isLoggedIn: boolean;
  email: string;
  username: string;
  handleLogin: (email: string, name: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  email: "",
  username: "",
  handleLogin: async (email: string, name: string) => {},
});

export const AuthProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  const handleLogin: (email: string, name: string) => Promise<void> = async (
    email: string,
    name: string
  ) => {
    setIsLoggedIn(true);
    setEmail(email);
    setUsername(name);
    if (AUTH_LOGGING) {
      console.log("Username set to: ", username);
    }
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
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
