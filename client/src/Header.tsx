import React, { useContext, FC, useState } from "react";
import { View, Text, Image, Pressable, Modal } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/HeaderStyles";
import { useNavigation } from "@react-navigation/native";

/**
 * The Header component displays the app logo and provides access to profile or login options based on the user's login status.
 */
const Header: FC = () => {
  const { isLoggedIn, username, handleLogout } = useContext(AuthContext);
  const navigation = useNavigation();
  const [showDropdown, setShowDropdown] = useState(false);

  return (
    <View style={styles.container}>
      <Pressable
        onPress={async () => {
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
        onPress={async () => {
          if (isLoggedIn) {
            setShowDropdown(!showDropdown); // Toggle dropdown on profile click
          } else {
            await navigation.navigate("Login");
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
          <Text style={styles.profileText} testID="header-username">
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

      <Modal visible={showDropdown} transparent>
        <Pressable
          style={styles.dropdownOverlay}
          onPress={() => setShowDropdown(false)}
        >
          <View style={styles.dropdownMenu}>
            <Pressable
              style={styles.dropdownItem}
              onPress={async () => {
                await handleLogout();
                setShowDropdown(false);
              }}
            >
              <Text>Logout</Text>
            </Pressable>
          </View>
        </Pressable>
      </Modal>
    </View>
  );
};

export default Header;
