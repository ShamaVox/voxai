import React, { useState, useContext, useEffect } from "react";
import { View, Text, TextInput, Pressable, Picker } from "react-native";
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
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [accountType, setAccountType] = useState("Recruiter");
  const [showNewAccountFields, setShowNewAccountFields] = useState(false);
  // This isn't very elegant, but I don't want the error messages to show when the user hasn't typed anything
  const [typedEmail, setTypedEmail] = useState(false);
  const [typedCode, setTypedCode] = useState(false);
  const [typedName, setTypedName] = useState(false);
  const [typedOrganization, setTypedOrganization] = useState(false);

  const {
    handleLogin,
    sendVerificationCode,
    validateVerificationCode,
  } = useContext(AuthContext);
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

  const handleSendCode = async () => {
    const response = await sendVerificationCode(email);
    if (response !== null && response.status >= 200 && response.status <= 299) {
      setShowCodeField(true);
      if (!response.data.account_exists) {
        if (LOGIN_LOGGING) {
          console.log(
            "response.account_exists is " + response.data.account_exists
          );
        }
        setShowNewAccountFields(true);
      }
    } else {
      setErrors({ email: "Invalid email" });
    }
  };

  const validateCode = (): boolean => {
    // Validate the verification code (6 digits)
    const codeRegex = /^\d{6}$/;
    return codeRegex.test(code);
  };

  const validateForm = (): boolean => {
    if (typedEmail && !validateEmail()) {
      setErrors({ email: "Invalid email" });
    } else if (showCodeField && typedCode && !validateCode()) {
      setErrors({ code: "Verfication code should be be 6 digits" });
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

  const handleSubmit = async () => {
    if (isCodeValid) {
      const name_from_response = await validateVerificationCode(
        email,
        code,
        name,
        organization,
        accountType
      );
      if (name_from_response) {
        const isLoginSuccessful = await handleLogin(email, name_from_response);
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
      {showCodeField && errors.code && (
        <Text style={styles.error}>{errors.code}</Text>
      )}
      {showNewAccountFields && (
        <>
          <TextInput
            style={styles.input}
            placeholder="Name"
            value={name}
            onChangeText={setName}
          />
          {errors.name && <Text style={styles.error}>{errors.name}</Text>}

          <TextInput
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
