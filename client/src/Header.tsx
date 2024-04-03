import React, { useContext } from "react";
import { View, Text, Image, TouchableOpacity } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/HeaderStyles";

const Header: React.FC = () => {
  const { isLoggedIn, username } = useContext(AuthContext);

  return (
    <View style={styles.container}>
      <Image source={require("../assets/logo.png")} style={styles.logo} />
      <TouchableOpacity style={styles.profileContainer}>
        <Image
          source={
            isLoggedIn
              ? require("../assets/profile-icon-logged-in.png")
              : require("../assets/profile-icon-logged-out.png")
          }
          style={styles.profileIcon}
        />
        <Text style={styles.profileText}>
          {isLoggedIn ? username : "Log In"}
        </Text>
      </TouchableOpacity>
    </View>
  );
};

export default Header;