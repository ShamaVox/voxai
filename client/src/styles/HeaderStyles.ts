import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 20,
    backgroundColor: "#f0f0f0",
  },
  logo: {
    width: 100,
    height: 30,
    resizeMode: "contain",
  },
  profileContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  profileIcon: {
    width: 24,
    height: 24,
    marginRight: 8,
  },
  profileText: {
    fontSize: 16,
    fontWeight: "bold",
  },
});

export default styles;