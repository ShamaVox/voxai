import React, { FC } from "react";
import { AuthProvider, AuthContext } from "./AuthContext";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import Home from "./Home";
import Dashboard from "./Dashboard";
import Login from "./Login";
import Header from "./Header";
import Candidates from "./Candidates";

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
    <AuthProvider>
      <NavigationContainer>
        <Stack.Navigator 
          screenOptions={{
            header: () => <Header />,
        }}>
          <Stack.Screen name="Home" component={Home} />
          <Stack.Screen name="Login" component={Login} />
          <Stack.Screen name="Dashboard" component={Dashboard} />
          <Stack.Screen name="Candidates" component={Candidates} />
        </Stack.Navigator>
      </NavigationContainer>
    </AuthProvider>
  );
};

export default App;