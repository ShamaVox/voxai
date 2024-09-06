import React from 'react';
import axios from "axios";
import { SERVER_ENDPOINT } from "./utils/Axios";
import { Button, Linking } from 'react-native';
import { server_url } from "./config/ServerUrl";
import { generateRandomState } from './utils/Random';
import { useNavigation } from "@react-navigation/native";
import { useAuth } from './AuthContext';

const OktaSignInButton = () => {
  const navigation = useNavigation();
  const { handleLogin } = useAuth();
  const loginWithOkta = async () => {

    const state = generateRandomState();

    const authorizationUrl = `https://dev-05459793.okta.com/oauth2/default/v1/authorize?client_id=0oaitt4y79BThLYvY5d7&redirect_uri=${encodeURIComponent(server_url + "/okta")}&response_type=code&scope=openid profile email https://www.googleapis.com/auth/calendar&state=${state}`;

    // Open the authorization URL in the browser or an in-app browser
    Linking.openURL(authorizationUrl).catch(err => console.error('Error opening URL:', err));

    const response = await axios.post(SERVER_ENDPOINT('okta'), { state: state });

    if (response.data.success) {
      const { email, name, authToken, onboarded, okta } = response.data;
      await handleLogin(email, name, authToken, onboarded, okta);
      navigation.navigate('Home');
    } else {
      throw new Error('Login failed');
    }
  };

  return (
    <Button
      title="Sign in with Okta"
      onPress={loginWithOkta}
    />
  );
};

/*

TODO: Add these lines to Customization -> Brands -> VoxAI -> Page Design -> Code Editor to enable Google SSO with Okta

config.idps= [
        { type: 'GOOGLE', id: 'Your_IDP_ID' }
    ];
    config.idpDisplay = "SECONDARY";

Using this feature requires setting up a custom domain with Okta (for some reason), so we can't do it yet. 

*/

export default OktaSignInButton;