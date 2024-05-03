import { server_url } from "../ServerUrl";
import { AxiosResponse } from "axios";

// Server
export const SERVER_URL = server_url;

/**
 * Constructs the full server endpoint URL based on the provided path.
 *
 * @param path - The relative path to the API endpoint.
 * @returns The full URL of the server endpoint.
 */
export function SERVER_ENDPOINT(endpoint_name: string): string {
  return SERVER_URL + "api/" + endpoint_name;
}

/**
 * Checks the status code of an Axios response.
 *
 * @param response The Axios response object.
 * @param checkType The type of status check to perform (e.g., "OK" for 2xx success codes).
 * @returns True if the status code matches the check type, false otherwise.
 */
export function checkStatus(
  response: AxiosResponse,
  checkType: string
): boolean {
  if (checkType == "OK") {
    return response.status >= 200 && response.status <= 299;
  } else if (checkType == "Auth") {
    return response.status != 401;
  }
}

/**
 * Logs out if the server's auth token check is invalid.
 *
 * @param response The Axios response object.
 * @param checkType The type of status check to perform (e.g., "OK" for 2xx success codes).
 * @returns True if the status code matches the check type, false otherwise.
 */
export async function handleLogoutResponse(
  handleLogout: (a: boolean) => Promise<void>,
  response: AxiosResponse,
  log: boolean
): Promise<void> {
  if (!checkStatus(response, "Auth")) {
    if (log) {
      console.log("Server detected invalid auth token; logging out");
    }
    await handleLogout(true);
  }
}
