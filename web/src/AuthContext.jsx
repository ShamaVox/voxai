import React, { createContext, useState } from "react";
import axios from "axios";

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  console.log("AuthProvider rendered"); // Debug statement

  const handleLogin = async (username, password) => {
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
    }
  };

  console.log("isLoggedIn value:", isLoggedIn);

  return (
    <AuthContext.Provider value={{ isLoggedIn, handleLogin }}>
      {children}
    </AuthContext.Provider>
  );
};
