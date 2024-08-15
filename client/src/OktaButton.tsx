import React from 'react';
import { Button, Linking } from 'react-native';

const OktaSignInButton = () => {
  const redirectToOkta = () => {
    
    const authorizationUrl = `https://dev-05459793.okta.com/oauth2/default/v1/authorize?client_id=0oaitt4y79BThLYvY5d7&redirect_uri=${encodeURIComponent("http://localhost:5000/okta")}&response_type=code&scope=openid profile email&state=test`;

    // Open the authorization URL in the browser or an in-app browser
    Linking.openURL(authorizationUrl).catch(err => console.error('Error opening URL:', err));
  };

  return (
    <Button
      title="Sign in with Okta"
      onPress={redirectToOkta}
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