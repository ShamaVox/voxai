import { useCookies } from "react-cookie";
import { render } from "@testing-library/react-native";
import { FC } from "react";

let authCookies = {};

interface CookieComponentProps {
  cookieValue: Object;
  storeAuthCookie: boolean;
}

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
  console.error(cookieValue, cookies);
  return <> </>;
};

export const clearCookies = () => {
  render(<CookieComponent cookieValue={{}} storeAuthCookie={false} />);
};

export const setCookies = (cookieValue: Object) => {
  render(<CookieComponent cookieValue={cookieValue} storeAuthCookie={false} />);
};

export const getAuthCookies = () => {
  render(<CookieComponent cookieValue={{}} storeAuthCookie={true} />);
  return authCookies;
};
