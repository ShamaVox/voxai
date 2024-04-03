import React, { useContext } from "react";
import { View, Text, Image, Pressable } from "react-native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/HeaderStyles";
import { useNavigation } from "@react-navigation/native"; // Import navigation hook

const Header: React.FC = () => {
  const { isLoggedIn, username } = useContext(AuthContext);
  const navigation = useNavigation(); // Get navigation object

  return (
    <View style={styles.container}>
      <Image source={require("../assets/logo.png")} style={styles.logo} />
      <Pressable
        style={styles.profileContainer}
        onPress={() => {
          if (!isLoggedIn) {
            navigation.navigate("Login"); // Navigate to Login if not logged in
          }
        }}
      >
        <Image
          source={
            isLoggedIn
              ? require("../assets/profile-icon-logged-in.png")
              : require("../assets/profile-icon-logged-out.png")
          }
          style={styles.profileIcon}
        />
        <View style={styles.profileTextContainer}>
            <Text style={styles.profileText}>{isLoggedIn ? username : "Log In"}</Text>
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