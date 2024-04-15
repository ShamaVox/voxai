import React, { createContext, useState } from "react";
import axios from "axios";
import { AUTH_LOGGING, SERVER_ENDPOINT } from "./Constants";

interface AuthContextProps {
  isLoggedIn: boolean;
  email: string;
  sendVerificationCode: (email: string) => Promise<boolean>;
  validateVerificationCode: (email: string, code: string) => Promise<boolean>;
  handleLogin: (email: string) => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  email: "",
  sendVerificationCode: async () => false,
  validateVerificationCode: async () => false,
  handleLogin: async () => false,
});

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [email, setEmail] = useState("");

  if (AUTH_LOGGING) {
    console.log("AuthProvider rendered");
  }

  const sendVerificationCode = async (email: string) => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("send_code"), {
        email,
      });
      if (response.status === 200) {
        setEmail(email);
        return true;
      } else {
        if (AUTH_LOGGING) {
          console.log("Sending verification code failed");
        }
        return false;
      }
    } catch (error) {
      console.error("Error during sending verification code:", error);
      return false;
    }
  };

  const validateVerificationCode = async (email: string, code: string) => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("validate_code"), {
        email,
        code,
      });
      if (response.status === 200) {
        return true;
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

  const handleLogin = async (email: string) => {
    try {
      setIsLoggedIn(true);
      setEmail(email);
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
        sendVerificationCode,
        validateVerificationCode,
        handleLogin,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
