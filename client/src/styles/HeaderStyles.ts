import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: "#f0f0f0",
  },
  logo: {
    width: 100,
    height: 50,
    resizeMode: "contain",
  },
  profileContainer: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
  },
  profileTextContainer: {
    flexDirection: "row",
    alignItems: "center",
  },
  profileIcon: {
    width: 34,
    height: 34,
    marginRight: 8,
  },
  profileText: {
    fontSize: 16,
    fontWeight: "bold",
  },
  downArrow: {
    width: 25,
    height: 25,
    resizeMode: "contain",
    paddingLeft: 10,
    paddingRight: 10,
  },
});

export default styles;
