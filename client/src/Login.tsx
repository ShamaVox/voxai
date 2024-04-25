import React, { useState, useContext, useEffect } from "react";
import { View, Text, TextInput, Pressable } from "react-native";
import { Picker } from "@react-native-picker/picker";
import { AuthContext } from "./AuthContext";
import styles from "./styles/LoginStyles";
import { LOGIN_LOGGING, SERVER_ENDPOINT } from "./Constants";
import { useNavigation } from "@react-navigation/native";
import axios from "axios";

interface Errors {
  email?: string;
  code?: string;
  name?: string;
  organization?: string;
}

const Login: React.FC = () => {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [isEmailValid, setIsEmailValid] = useState(false);
  const [showCodeField, setShowCodeField] = useState(false);
  const [isCodeValid, setIsCodeValid] = useState(false);
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [accountType, setAccountType] = useState("Recruiter");
  const [showNewAccountFields, setShowNewAccountFields] = useState(false);
  // This isn't very elegant, but I don't want the error messages to show when the user hasn't typed anything
  const [typedEmail, setTypedEmail] = useState(false);
  const [typedCode, setTypedCode] = useState(false);
  const [typedName, setTypedName] = useState(false);
  const [typedOrganization, setTypedOrganization] = useState(false);

  const { handleLogin } = useContext(AuthContext);
  const navigation = useNavigation();

  if (email.trim() && !typedEmail) {
    setTypedEmail(true);
  }

  if (code.trim() && !typedCode) {
    setTypedCode(true);
  }

  if (name.trim() && !typedName) {
    setTypedName(true);
  }

  if (organization.trim() && !typedOrganization) {
    setTypedOrganization(true);
  }

  const validateEmail = (): boolean => {
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateName = () => name.trim() !== "";
  const validateOrganization = () => organization.trim() !== "";

  const validateCode = (): boolean => {
    // Validate the verification code (6 digits)
    const codeRegex = /^\d{6}$/;
    return codeRegex.test(code);
  };

  const validateForm = (): boolean => {
    if (typedEmail && !validateEmail()) {
      setErrors({ email: "Invalid email" });
    } else if (showCodeField && typedCode && !validateCode()) {
      setErrors({ code: "Verification code should be 6 digits" });
    } else if (showNewAccountFields && typedName && !validateName()) {
      setErrors({ name: "Please enter your name" });
    } else if (
      showNewAccountFields &&
      typedOrganization &&
      !validateOrganization()
    ) {
      setErrors({ organization: "Please enter your organization" });
    } else {
      if (typedEmail) {
        setIsEmailValid(true);
      }
      if (
        showCodeField &&
        typedCode &&
        (!showNewAccountFields || (typedName && typedOrganization))
      ) {
        setIsCodeValid(true);
      }
      setErrors({});
    }
  };

  useEffect(() => {
    validateForm();
  }, [email, code, name, organization]);

  const handleSendCode = async () => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("send_code"), {
        email,
      });
      if (response.status < 200 || response.status > 299) {
        if (LOGIN_LOGGING) {
          console.log("Sending verification code failed");
        }
        setErrors({ email: "Invalid email" });
        return;
      }
      setShowCodeField(true);
      if (!response.data.account_exists) {
        if (LOGIN_LOGGING) {
          console.log(
            "response.account_exists is " + response.data.account_exists
          );
        }
        setShowNewAccountFields(true);
      }
    } catch (error) {
      console.error(error);
      if (LOGIN_LOGGING) {
        console.log("Error sending verification code:", error);
      }
      setErrors({ email: "Invalid email" });
      return;
    }
  };

  const handleSubmit = async () => {
    if (isCodeValid) {
      try {
        const response = await axios.post(SERVER_ENDPOINT("validate_code"), {
          email,
          code,
          name,
          organization,
          accountType,
        });
        if (
          response.status < 200 ||
          response.status > 299 ||
          !response.data.name
        ) {
          if (AUTH_LOGGING) {
            console.log("Verification code validation failed");
          }
          setErrors({ code: "Invalid code" });
          return;
        }
        handleLogin(email, response.data.name);
        navigation.navigate("Home");
      } catch (error) {
        if (LOGIN_LOGGING) {
          console.log("Error during verification code validation:", error);
        }
        setErrors({ code: "Invalid code" });
        return;
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
        testID="email-input"
        style={styles.input}
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
      />
      {errors.email && <Text style={styles.error}>{errors.email}</Text>}
      {showCodeField && (
        <TextInput
          testID="code-input"
          style={styles.input}
          placeholder="Verification code"
          value={code}
          onChangeText={setCode}
          keyboardType="numeric"
        />
      )}
      {showCodeField && errors.code && (
        <Text style={styles.error}>{errors.code}</Text>
      )}
      {showNewAccountFields && (
        <>
          <TextInput
            testID="name-input"
            style={styles.input}
            placeholder="Name"
            value={name}
            onChangeText={setName}
          />
          {errors.name && <Text style={styles.error}>{errors.name}</Text>}

          <TextInput
            testID="organization-input"
            style={styles.input}
            placeholder="Organization"
            value={organization}
            onChangeText={setOrganization}
          />
          {errors.organization && (
            <Text style={styles.error}>{errors.organization}</Text>
          )}
          <Text> Account type: </Text>
          <Picker
            selectedValue={accountType}
            onValueChange={(itemValue) => setAccountType(itemValue)}
          >
            <Picker.Item label="Recruiter" value="Recruiter" />
            <Picker.Item label="Hiring Manager" value="HiringManager" />
          </Picker>
        </>
      )}
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
