import React, { FC, useContext, useEffect, useState } from "react";
import { View } from "react-native";
import { AuthProvider, AuthContext } from "./AuthContext";
import { NavigationContainer, useNavigation } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import Home from "./Home";
import Dashboard from "./Dashboard";
import Login from "./Login";
import Header from "./Header";
import Candidates from "./Candidates";
import NavBar from "./NavBar";
import { APP_LOGGING } from "./config/Logging";
import styles from "./styles/AppStyles";

// Fixes TypeScript error in my IDE
declare global {
  namespace ReactNavigation {
    interface RootParamList {
      Candidates: undefined;
      Dashboard: undefined;
      Home: undefined;
      Login: undefined;
    }
  }
}

const Stack = createStackNavigator();

const App: FC = () => {
  return (
    <NavigationContainer>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </NavigationContainer>
  );
};

const AppContent: FC = () => {
  const navigation = useNavigation();

  const { isLoggedIn } = useContext(AuthContext);
  if (APP_LOGGING) {
    console.log("User is logged in: ", isLoggedIn);
  }
  return (
    <View style={styles.app}>
      <Header />
      <View style={styles.contentView}>
        {isLoggedIn && (
          <View style={styles.navBar}>
            <NavBar />
          </View>
        )}
        <Stack.Navigator
          screenOptions={{
            header: () => <View />, // Disable default header
          }}
        >
          <Stack.Screen name="Home" component={Home} />
          <Stack.Screen name="Login" component={Login} />
          <Stack.Screen name="Dashboard" component={Dashboard} />
          <Stack.Screen name="Candidates" component={Candidates} />
        </Stack.Navigator>
      </View>
    </View>
  );
};

export default App;
