import React, { createContext, useState } from "react";
import axios from "axios";
import { AUTH_LOGGING, SERVER_ENDPOINT } from "./Constants";

interface AuthContextProps {
  isLoggedIn: boolean;
  email: string;
  sendVerificationCode: (email: string) => Promise<boolean>;
  validateVerificationCode: (email: string, code: string) => Promise<boolean>;
  handleLogin: (email: string, name: string) => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  email: "",
  username: "",
  sendVerificationCode: async () => false,
  validateVerificationCode: async () => false,
  handleLogin: async () => false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  const sendVerificationCode = async (email: string) => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("send_code"), {
        email,
      });
      if (response.status >= 200 && response.status <= 299) {
        return response;
      } else {
        if (AUTH_LOGGING) {
          console.log("Sending verification code failed");
        }
        return null;
      }
    } catch (error) {
      console.error("Error sending verification code:", error);
      return null;
    }
  };

  const validateVerificationCode = async (
    email: string,
    code: string,
    name: string,
    organization: string,
    accountType: string
  ) => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("validate_code"), {
        email,
        code,
        name,
        organization,
        accountType,
      });
      if (response.status >= 200 && response.status <= 299) {
        return response.data.name; // TODO: Rework these functions
      } else {
        if (AUTH_LOGGING) {
          console.log("Verification code validation failed");
        }
        return false;
      }
    } catch (error) {
      console.error("Error during verification code validation:", error);
      return false;
    }
  };

  const handleLogin = async (email: string, name: string) => {
    try {
      setIsLoggedIn(true);
      setEmail(email);
      setUsername(name);
      if (AUTH_LOGGING) {
        console.log("Username set to: ", username);
      }
      return true;
    } catch (error) {
      console.error("Error during login:", error);
      return false;
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
        sendVerificationCode,
        validateVerificationCode,
        handleLogin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
