import React, { useState, useContext, useEffect } from "react";
import { View, Text, TextInput, Pressable } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/LoginStyles";
import { MIN_PASSWORD_LENGTH, LOGIN_LOGGING } from "./Constants";
import { useNavigation } from "@react-navigation/native";

interface Errors {
  username?: string;
  password?: string;
}

const Login: React.FC = () => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [isFormValid, setIsFormValid] = useState(false);

  // This isn't very elegant, but I don't want the error messages to show when the user hasn't typed anything
  const [typedUsername, setTypedUsername] = useState(false);
  const [typedPassword, setTypedPassword] = useState(false);

  const { handleLogin } = useContext(AuthContext);
  const navigation = useNavigation();

  const validateForm = (): boolean => {
    let validationErrors: Record<string, string> = {};

    if (username.trim() && !typedUsername) {
      setTypedUsername(true);
    }

    if (password.trim() && !typedPassword) {
      setTypedPassword(true);
    }

    // Validate username
    if (!username.trim() && typedUsername) {
      validationErrors.username = "Username is required.";
    }

    // Validate password
    if (!password.trim() && typedPassword) {
      validationErrors.password = "Password is required.";
    } else if (password.trim() && password.length < MIN_PASSWORD_LENGTH) {
      validationErrors.password = "Password must be at least 6 characters.";
    }

    setErrors(validationErrors);

    // Form is valid if there are no errors
    return (
      username.trim() &&
      password.trim() &&
      Object.keys(validationErrors).length === 0
    );
  };

  useEffect(() => {
    // Check form validity whenever username or password changes
    setIsFormValid(validateForm());
  }, [username, password]);

  const handleSubmit = async () => {
    // Call handleLogin from AuthContext if form is valid
    if (isFormValid) {
      const isLoginSuccessful = await handleLogin(username, password);
      if (isLoginSuccessful) {
        // Navigate to the Dashboard page on successful login
        navigation.navigate("Dashboard");
      } else {
        const validationErrors: Record<string, string> = {};
        validationErrors.password = "Invalid credentials.";
        setErrors(validationErrors);
        setIsFormValid(false);
      }
    } else {
      if (LOGIN_LOGGING) {
        console.log("Form has errors; not submitting request.");
      }
    }
  };

  return (
    <View style={styles.container} role={"form"}>
      <Text style={styles.title}>Login</Text>
      <TextInput
        style={styles.input}
        placeholder="Username"
        value={username}
        onChangeText={setUsername}
      />
      {errors.username && <Text style={styles.error}>{errors.username}</Text>}
      <TextInput
        style={styles.input}
        placeholder="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
      />
      {errors.password && <Text style={styles.error}>{errors.password}</Text>}
      <Pressable
        style={[styles.button, { opacity: isFormValid ? 1 : 0.5 }]}
        disabled={!isFormValid}
        onPress={handleSubmit}
      >
        <Text style={styles.buttonText}>Login</Text>
      </Pressable>
    </View>
  );
};

export default Login;
