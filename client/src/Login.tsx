import React, { FC, useState, useContext, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  Keyboard,
  KeyboardTypeOptions,
  NativeSyntheticEvent,
  TextInputKeyPressEventData,
} from "react-native";
import { Picker } from "@react-native-picker/picker";
import { AuthContext } from "./AuthContext";
import styles from "./styles/LoginStyles";
import { LOGIN_LOGGING } from "./config/Logging";
import { SERVER_ENDPOINT } from "./utils/Axios";
import { useNavigation } from "@react-navigation/native";
import axios from "axios";
import { checkStatus } from "./utils/Axios";

interface Errors {
  email?: string;
  code?: string;
  name?: string;
  organization?: string;
}

interface InputWithErrorProps {
  value: string;
  onChangeText: (text: string) => void;
  placeholder: string;
  keyboardType?: KeyboardTypeOptions;
  error?: string;
  testID: string;
  handleKeyPress: (e: NativeSyntheticEvent<TextInputKeyPressEventData>) => void;
}

/**
 * Component that renders an input field with an error message.
 */
const InputWithError: FC<InputWithErrorProps> = ({
  value,
  onChangeText,
  placeholder,
  keyboardType,
  error,
  testID,
  handleKeyPress,
}) => {
  return (
    <>
      <TextInput
        onKeyPress={handleKeyPress}
        testID={testID}
        style={styles.input}
        placeholder={placeholder}
        value={value}
        onChangeText={onChangeText}
        keyboardType={keyboardType}
      />
      {error && <Text style={styles.error}>{error}</Text>}
    </>
  );
};

/**
 * The Login component handles user authentication, allowing users to log in with existing accounts or create new ones.
 */
const Login: FC = () => {
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [isEmailValid, setIsEmailValid] = useState(false);
  const [showCodeField, setShowCodeField] = useState(false);
  const [name, setName] = useState("");
  const [organization, setOrganization] = useState("");
  const [accountType, setAccountType] = useState("Recruiter");
  const [showNewAccountFields, setShowNewAccountFields] = useState(false);
  const [pressedSendCode, setPressedSendCode] = useState(false);
  const [pressedSubmit, setPressedSubmit] = useState(false);
  const { handleLogin } = useContext(AuthContext);
  const navigation = useNavigation();

  /**
   * Validates the email address using a regular expression.
   * @returns {boolean} true if the email is valid, false otherwise
   */
  const validateEmail = (): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  /**
   * Validates the name field ensuring it's not empty.
   * @returns {boolean} true if the name is valid, false otherwise
   */
  const validateName = () => name.trim() !== "";

  /**
   * Validates the organization field ensuring it's not empty.
   * @returns {boolean} true if the organization is valid, false otherwise
   */
  const validateOrganization = () => organization.trim() !== "";

  /**
   * Validates the verification code ensuring it's 6 digits.
   * @returns {boolean} true if the code is valid, false otherwise
   */
  const validateCode = (): boolean => {
    const codeRegex = /^\d{6}$/;
    return codeRegex.test(code);
  };

  /**
   * Validates the form based on the current state and updates errors.
   */
  const validateForm = (): void => {
    const emailError = !validateEmail() ? "Invalid email" : undefined;
    const codeError =
      showCodeField && !validateCode()
        ? "Verification code should be 6 digits"
        : undefined;
    const nameError =
      showNewAccountFields && !validateName()
        ? "Please enter your name"
        : undefined;
    const organizationError =
      showNewAccountFields && !validateOrganization()
        ? "Please enter your organization"
        : undefined;

    setErrors({
      email: emailError,
      code: codeError,
      name: nameError,
      organization: organizationError,
    });
  };

  /**
   * Checks whether there are any errors preventing the code validation request from being sent.
   */
  const canSubmit = (fromButton = true) => {
    if (!fromButton) {
      validateForm();
    }
    return (
      (showCodeField &&
        errors.code === undefined &&
        errors.name === undefined &&
        errors.organization === undefined) ||
      (!showCodeField && errors.email === undefined)
    );
  };

  useEffect(() => {
    validateForm();
  }, [email, code, name, organization]);

  /**
   * Handles sending the verification code to the provided email.
   */
  const handleSendCode = async () => {
    setPressedSendCode(true);
    if (!canSubmit(false)) {
      return;
    }
    try {
      const response = await axios.post(SERVER_ENDPOINT("send_code"), {
        email,
      });
      if (!checkStatus(response, "OK")) {
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
      if (LOGIN_LOGGING) {
        console.log("Error sending verification code:", error);
      }
      setErrors({ email: "Invalid email" });
      return;
    }
  };

  /**
   * Handles submitting the form and validating the code.
   */
  const handleSubmit: () => Promise<void> = async () => {
    setPressedSubmit(true);
    if (!canSubmit(false)) {
      return;
    }
    if (validateCode()) {
      try {
        const response = await axios.post(SERVER_ENDPOINT("validate_code"), {
          email,
          code,
          name,
          organization,
          accountType,
        });
        if (
          !checkStatus(response, "OK") ||
          !response.data.name ||
          !response.data.authToken
        ) {
          if (LOGIN_LOGGING) {
            console.log("Verification code validation failed");
          }
          setErrors({ code: "Invalid code" });
          return;
        }
        await handleLogin(email, response.data.name, response.data.authToken);
        await navigation.navigate("Home");
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

  /**
   * Handles submitting the form when the Enter key is pressed.
   */
  const handleKeyPress = (
    e: NativeSyntheticEvent<TextInputKeyPressEventData>
  ) => {
    if (e.nativeEvent.key === "Enter") {
      e.preventDefault();
      if (showCodeField) {
        handleSubmit();
      } else {
        handleSendCode();
      }
    }
  };

  return (
    <View style={styles.container} role={"form"}>
      <Text style={styles.title}>Login</Text>
      <InputWithError
        testID="email-input"
        placeholder="Email"
        value={email}
        onChangeText={setEmail}
        keyboardType="email-address"
        error={pressedSendCode && errors.email}
        handleKeyPress={handleKeyPress}
      />
      {showCodeField && (
        <InputWithError
          testID="code-input"
          placeholder="Verification code"
          value={code}
          onChangeText={setCode}
          keyboardType="numeric"
          error={pressedSubmit && errors.code}
          handleKeyPress={handleKeyPress}
        />
      )}
      {showNewAccountFields && (
        <>
          <InputWithError
            testID="name-input"
            placeholder="Name"
            value={name}
            onChangeText={setName}
            keyboardType="default"
            error={pressedSubmit && errors.name}
            handleKeyPress={handleKeyPress}
          />
          <InputWithError
            testID="organization-input"
            placeholder="Organization"
            value={organization}
            onChangeText={setOrganization}
            keyboardType="default"
            error={pressedSubmit && errors.organization}
            handleKeyPress={handleKeyPress}
          />
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
          style={[
            styles.button,
            { opacity: errors.email === undefined ? 1 : 0.5 },
          ]}
          onPress={async () => {
            await handleSendCode();
          }}
        >
          <Text style={styles.buttonText}>Send code</Text>
        </Pressable>
      ) : (
        <Pressable
          style={[styles.button, { opacity: canSubmit() ? 1 : 0.5 }]}
          onPress={async () => {
            await handleSubmit();
          }}
        >
          <Text style={styles.buttonText}>Validate code</Text>
        </Pressable>
      )}
    </View>
  );
};

export default Login;
