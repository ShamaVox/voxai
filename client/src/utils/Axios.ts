import { server_url } from "../ServerUrl";
import { AxiosResponse } from "axios";

// Server
export const SERVER_URL = server_url;
export function SERVER_ENDPOINT(endpoint_name: string): string {
  return SERVER_URL + "api/" + endpoint_name;
}

export function checkStatus(
  response: AxiosResponse,
  checkType: string
): boolean {
  if (checkType == "OK") {
    return response.status >= 200 && response.status <= 299;
  }
}
