import React, { FC } from "react";
import { View, Pressable, Text } from "react-native";
import { useNavigation } from "@react-navigation/native";
import styles from "./styles/LoginStyles"; // Placeholder style

const Home: FC = () => {
  const navigation = useNavigation();

  const handleLoginClick = () => {
    navigation.navigate("Login");
  };

  return (
    <View style={styles.container}>
      <Text>
        This is a placeholder homepage <br />
      </Text>
      <Pressable onPress={handleLoginClick} style={styles.button}>
        <Text> Login </Text>
      </Pressable>
    </View>
  );
};

export default Home;
