import { useCookies } from "react-cookie";
import { render } from "@testing-library/react-native";
import { FC } from "react";

let authCookies = {};

interface CookieComponentProps {
  cookieValue: Object;
  storeAuthCookie: boolean;
}

/**
 * A helper component used for setting or clearing cookies during testing.
 *
 * @param cookieValue An object containing cookie data to set or an empty object to clear.
 * @param storeAuthCookie A boolean flag. If true, stores the current auth cookie value for retrieval.
 */
const CookieComponent: FC<CookieComponentProps> = ({
  cookieValue,
  storeAuthCookie,
}) => {
  const [cookies, setCookie, removeCookie] = useCookies(["voxai"]);
  if (storeAuthCookie) {
    console.error(cookies);
    return;
  }
  if (Object.keys(cookieValue).length) {
    setCookie("voxai", cookieValue);
  } else {
    removeCookie("voxai");
  }
  return <> </>;
};

/**
 * Clears all cookies associated with the application.
 */
export const clearCookies = () => {
  render(<CookieComponent cookieValue={{}} storeAuthCookie={false} />);
};

/**
 * Sets cookies with the specified values.
 *
 * @param cookieValue An object containing the cookie key-value pairs to set.
 */
export const setCookies = (cookieValue: Object) => {
  render(<CookieComponent cookieValue={cookieValue} storeAuthCookie={false} />);
};

/**
 * Retrieves the authentication cookies from the application.
 *
 * @returns An object containing the authentication cookie data.
 */
export const getAuthCookies = () => {
  render(<CookieComponent cookieValue={{}} storeAuthCookie={true} />);
  return authCookies;
};
