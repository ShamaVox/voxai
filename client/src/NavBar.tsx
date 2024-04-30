import React, { useContext, useState } from "react";
import { View, Text, Pressable, Image } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/NavBarStyles";
import { NAV_BAR_LOGGING } from "./config/Logging";
import { useNavigation } from "@react-navigation/native";

/**
 * The NavBar component provides navigation options for logged-in users, allowing them to access different sections of the app.
 */
const NavBar: React.FC = () => {
  const [activeRouteName, setActiveRouteName] = useState("");
  const navigation = useNavigation();
  React.useEffect(() => {
    const unsubscribe = navigation.addListener("state", (e: any) => {
      if (NAV_BAR_LOGGING) {
        console.log("Focus event");
        console.log(e);
      }
      if (e.data.state !== undefined) {
        if (NAV_BAR_LOGGING) {
          console.log(e.data.state.routes.slice(-1));
          console.log(e.data.state.routes.slice(-1).name);
        }
        setActiveRouteName(e.data.state.routes.slice(-1)[0].name);
      }
    });

    return unsubscribe;
  }, [navigation]);

  if (NAV_BAR_LOGGING) {
    console.log("Active route name is: ", activeRouteName);
  }
  const { isLoggedIn } = useContext(AuthContext);

  if (!isLoggedIn) {
    return null;
  }

  /**
   * Determines the style for a navigation button based on the active route.
   *
   * @param routeName The name of the route associated with the button.
   * @returns The appropriate button style object.
   */
  const getButtonStyle = (routeName: string) => {
    return activeRouteName === routeName
      ? styles.selectedButton
      : styles.button;
  };

  /**
   * Determines the text style for a navigation button based on the active route.
   *
   * @param routeName The name of the route associated with the button.
   * @returns The appropriate text style object.
   */
  const getTextStyle = (routeName: string) => {
    return activeRouteName === routeName
      ? styles.selectedButtonText
      : styles.buttonText;
  };

  return (
    <View testID="nav-bar" style={styles.container}>
      <View testID="section-general" style={styles.section}>
        <Text style={styles.sectionTitle}>General</Text>
        <Pressable
          testID="nav-button-home"
          style={getButtonStyle("Home")}
          onPress={async () => {
            await navigation.navigate("Home");
          }}
        >
          <Image
            source={require("../assets/icons/dashboard.png")}
            style={styles.icon}
          />
          <Text style={getTextStyle("Home")}>Overview</Text>
        </Pressable>
        <Pressable
          testID="nav-button-dashboard"
          style={getButtonStyle("Dashboard")}
          onPress={async () => {
            await navigation.navigate("Dashboard");
          }}
        >
          <Image
            source={require("../assets/icons/dashboard.png")}
            style={styles.icon}
          />
          <Text style={getTextStyle("Dashboard")}>Dashboard</Text>
        </Pressable>
        <Pressable
          testID="nav-button-candidates"
          style={getButtonStyle("Candidates")}
          onPress={async () => {
            await navigation.navigate("Candidates");
          }}
        >
          <Image
            source={require("../assets/icons/candidates.png")}
            style={styles.icon}
          />
          <Text style={getTextStyle("Candidates")}>Candidates</Text>
        </Pressable>
      </View>
      <View style={styles.divider} />
      <View testID="section-support" style={styles.section}>
        <Text style={styles.sectionTitle}>Support</Text>
        <Pressable
          testID="nav-button-settings"
          style={getButtonStyle("Settings")}
          onPress={async () => {
            // temporary as there is no settings page
            await navigation.navigate("Candidates");
          }}
        >
          <Image
            source={require("../assets/icons/settings.png")}
            style={styles.icon}
          />
          <Text style={getTextStyle("Settings")}>Settings</Text>
        </Pressable>
      </View>
    </View>
  );
};

export default NavBar;
