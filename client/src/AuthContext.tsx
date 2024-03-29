import React, { createContext, useState } from "react";
import axios from "axios";

interface AuthContextProps {
  isLoggedIn: boolean;
  handleLogin: (username: string, password: string) => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  handleLogin: async () => false,
});

export const AuthProvider: React.FC = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  console.log("AuthProvider rendered"); // Debug statement

  const handleLogin: AuthContextProps["handleLogin"] = async (username, password) => {
    try {
      const response = await axios.post("http://localhost:5000/login", {
        username,
        password,
      });
      if (response.status === 200) {
        setIsLoggedIn(true);
        return true;
      } else {
        console.log("Login failed");
        return false;
      }
    } catch (error) {
      console.error("Error during login:", error);
      return false;
    }
  };

  console.log("isLoggedIn value:", isLoggedIn);

  return (
    <AuthContext.Provider value={{ isLoggedIn, handleLogin }}>
      {children}
    </AuthContext.Provider>
  );
};