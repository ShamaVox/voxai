import React, { useState, useContext, useEffect } from "react";
import { View, Text, TextInput, Pressable } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/LoginStyles";
import { LOGIN_LOGGING } from "./Constants";
import { useNavigation } from "@react-navigation/native";

interface Errors {
  email?: string;
  code?: string;
}

const Login: React.FC = () => {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [isEmailValid, setIsEmailValid] = useState(false);
  const [showCodeField, setShowCodeField] = useState(false);
  const [isCodeValid, setIsCodeValid] = useState(false);

  const {
    handleLogin,
    sendVerificationCode,
    validateVerificationCode,
  } = useContext(AuthContext);
  const navigation = useNavigation();

  const validateEmail = (): boolean => {
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  useEffect(() => {
    setIsEmailValid(validateEmail());
  }, [email]);

  const handleSendCode = async () => {
    const success = await sendVerificationCode(email);
    if (success) {
      setShowCodeField(true);
    } else {
      setErrors({ email: "Invalid email" });
    }
  };

  const validateCode = (): boolean => {
    // Validate the verification code (6 digits)
    const codeRegex = /^\d{6}$/;
    return codeRegex.test(code);
  };

  useEffect(() => {
    setIsCodeValid(validateCode());
  }, [code]);

  const handleSubmit = async () => {
    if (isCodeValid) {
      const success = await validateVerificationCode(email, code);
      if (success) {
        const isLoginSuccessful = await handleLogin(email);
        if (isLoginSuccessful) {
          navigation.navigate("Home");
        } else {
          setErrors({ code: "Invalid code" });
        }
      } else {
        setErrors({ code: "Invalid code" });
      }
    } else {
      if (LOGIN_LOGGING) {
        console.log("Code is invalid; not submitting request.");
      }
    }
  };

  return (
    <View style={styles.container} role={"form"}>
      <Text style={styles.title}>Login</Text>
      <TextInput
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
      />
      {errors.email && <Text style={styles.error}>{errors.email}</Text>}
      {showCodeField && (
        <TextInput
          style={styles.input}
          placeholder="Verification code"
          value={code}
          onChangeText={setCode}
          keyboardType="numeric"
        />
      )}
      {errors.code && <Text style={styles.error}>{errors.code}</Text>}
      {!showCodeField ? (
        <Pressable
          style={[styles.button, { opacity: isEmailValid ? 1 : 0.5 }]}
          disabled={!isEmailValid}
          onPress={handleSendCode}
        >
          <Text style={styles.buttonText}>Send code</Text>
        </Pressable>
      ) : (
        <Pressable
          style={[styles.button, { opacity: isCodeValid ? 1 : 0.5 }]}
          disabled={!isCodeValid}
          onPress={handleSubmit}
        >
          <Text style={styles.buttonText}>Validate code</Text>
        </Pressable>
      )}
    </View>
  );
};

export default Login;
