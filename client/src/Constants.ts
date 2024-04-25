import { server_url } from "./ServerUrl";

// Debug
export const LOGIN_LOGGING = false;
export const AUTH_LOGGING = false;
export const NAV_BAR_LOGGING = false;
export const APP_LOGGING = false;
export const HOME_LOGGING = false;
export const DASHBOARD_LOGGING = false;

// Server
export const SERVER_URL = server_url;
export function SERVER_ENDPOINT(endpoint_name: string): string {
  return SERVER_URL + "api/" + endpoint_name;
}

// Login page
export const MIN_PASSWORD_LENGTH = 6;
