import React, { useContext } from "react";
import { View, Text, Image, Pressable } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/HeaderStyles";
import { useNavigation } from "@react-navigation/native";

const Header: React.FC = () => {
  const { isLoggedIn, username } = useContext(AuthContext);
  const navigation = useNavigation();

  return (
    <View style={styles.container}>
      <Pressable
        onPress={() => {
          isLoggedIn
            ? navigation.navigate("Dashboard")
            : navigation.navigate("Home");
        }}
      >
        <Image
          testID="logo"
          source={require("../assets/logo.png")}
          style={styles.logo}
        />
      </Pressable>
      <Pressable
        testID="profile-container"
        style={styles.profileContainer}
        onPress={() => {
          if (!isLoggedIn) {
            navigation.navigate("Login"); // Navigate to Login if not logged in
          }
        }}
      >
        <Image
          testID={
            isLoggedIn ? "profile-icon-logged-in" : "profile-icon-logged-out"
          }
          source={
            isLoggedIn
              ? require("../assets/icons/profile-icon-logged-in.png")
              : require("../assets/icons/profile-icon-logged-out.png")
          }
          style={styles.profileIcon}
        />
        <View style={styles.profileTextContainer}>
          <Text style={styles.profileText}>
            {isLoggedIn ? username : "Log In"}
          </Text>
          {isLoggedIn && (
            <Image
              source={require("../assets/down-arrow.png")}
              style={styles.downArrow}
            />
          )}
        </View>
      </Pressable>
    </View>
  );
};

export default Header;
