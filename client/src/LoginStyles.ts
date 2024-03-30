import { StyleSheet } from "react-native";
import "@fontsource/sora";

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#f8f8f8",
  },
  title: {
    fontSize: 32,
    fontWeight: "bold",
    marginBottom: 24,
    color: "#333333",
    fontFamily: "Sora, sans-serif",
  },
  input: {
    borderWidth: 1,
    borderColor: "#dddddd",
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    width: "15%",
    fontSize: 16,
    fontFamily: "Sora, sans-serif",
  },
  error: {
    marginBottom: 16,
    color: "#ff4d4f",
    fontFamily: "Sora, sans-serif",
  },
  button: {
    backgroundColor: "#1890ff",
    borderRadius: 8,
    paddingVertical: 16,
    paddingHorizontal: 32,
    marginTop: 16,
  },
  buttonText: {
    color: "#ffffff",
    fontSize: 18,
    fontWeight: "bold",
    textAlign: "center",
    fontFamily: "Sora, sans-serif",
  },
});

export default styles;