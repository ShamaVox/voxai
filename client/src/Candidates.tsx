import React, { FC } from "react";
import { View, Pressable, Text } from "react-native";
// import { useNavigation } from "@react-navigation/native";
import styles from "./styles/LoginStyles"; // Placeholder style

const Home: FC = () => {
  // const navigation = useNavigation();

  return (
    <View style={styles.container}>
      <Text>This is a placeholder page <br /></Text> 
    </View>
  );
};

export default Home;