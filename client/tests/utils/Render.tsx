import { useCookies } from "react-cookie";
import { render } from "@testing-library/react-native";
import { FC } from "react";

export const CookieResetComponent: FC = () => {
  const [cookies, setCookie, removeCookie] = useCookies(["voxai"]);
  removeCookie("voxai");
  return <> </>;
};

export const clearCookies: () => void = () => {
  render(<CookieResetComponent />);
};
