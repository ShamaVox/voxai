import React, { createContext, useState } from "react";
import { AUTH_LOGGING } from "./Constants";

interface AuthContextProps {
  isLoggedIn: boolean;
  email: string;
  username: string;
  sendVerificationCode: (email: string) => Promise<boolean>;
  validateVerificationCode: (email: string, code: string) => Promise<boolean>;
  handleLogin: (email: string, name: string) => Promise<boolean>;
}

export const AuthContext = createContext<AuthContextProps>({
  isLoggedIn: false,
  email: "",
  username: "",
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

  const handleLogin = async (email: string, name: string) => {
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
