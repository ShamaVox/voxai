import React, { createContext, useState } from "react";
import axios from "axios";
import { DEBUG_AUTH } from "./Constants";

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

export const AuthProvider: React.FC = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState("");

  if (DEBUG_AUTH) {
    console.log("AuthProvider rendered");
  }

  const handleLogin: AuthContextProps["handleLogin"] = async (username, password) => {
    try {
      const response = await axios.post("http://localhost:5000/login", {
        username,
        password,
      });
      if (response.status === 200) {
        setIsLoggedIn(true);
        setUsername(username);
        return true;
      } else {
        if (DEBUG_AUTH) {
          console.log("Login failed");
        }
        return false;
      }
    } catch (error) {
      console.error("Error during login:", error);
      return false;
    }
  };

  if (DEBUG_AUTH) {
    console.log("isLoggedIn value:", isLoggedIn);
    console.log("username value:", username);
  }

  return (
    <AuthContext.Provider value={{ isLoggedIn, username, handleLogin }}>
      {children}
    </AuthContext.Provider>
  );
};