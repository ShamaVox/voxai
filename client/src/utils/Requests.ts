export function checkStatus(response, checkType: string): boolean {
  if (checkType == "OK") {
    return response.status >= 200 && response.status <= 299;
  }
}
