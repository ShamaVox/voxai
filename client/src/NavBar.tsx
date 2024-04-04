import React, { useContext, useState } from "react";
import { View, Text, Pressable, Image } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/NavBarStyles";
import { NAV_BAR_LOGGING } from "./Constants";
import { useNavigation } from "@react-navigation/native";

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
        console.log(e.data.state.routes.slice(-1));
        console.log(e.data.state.routes.slice(-1).name);
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

  const getButtonStyle = (routeName: string) => {
    return activeRouteName === routeName
      ? styles.selectedButton
      : styles.button;
  };

  const getTextStyle = (routeName: string) => {
    return activeRouteName === routeName
      ? styles.selectedButtonText
      : styles.buttonText;
  };

  return (
    <View style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>General</Text>
        <Pressable
          style={getButtonStyle("Dashboard")}
          onPress={() => navigation.navigate("Dashboard")}
        >
          <Image
            source={require("../assets/icons/dashboard.png")}
            style={styles.icon}
          />
          <Text style={getTextStyle("Dashboard")}>Overview</Text>
        </Pressable>
        <Pressable
          style={getButtonStyle("Candidates")}
          onPress={() => navigation.navigate("Candidates")}
        >
          <Image
            source={require("../assets/icons/candidates.png")}
            style={styles.icon}
          />
          <Text style={getTextStyle("Candidates")}>Candidates</Text>
        </Pressable>
      </View>
      <View style={styles.divider} />
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Support</Text>
        <Pressable
          style={getButtonStyle("Settings")}
          onPress={() => navigation.navigate("Candidates")} // temporary as there is no settings page
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
