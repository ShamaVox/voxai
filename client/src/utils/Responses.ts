import { AxiosResponse } from "axios";

export function checkStatus(
  response: AxiosResponse,
  checkType: string
): boolean {
  if (checkType == "OK") {
    return response.status >= 200 && response.status <= 299;
  }
}
