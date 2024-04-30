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
  dropdownOverlay: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
  },
  dropdownMenu: {
    backgroundColor: "white",
    position: "absolute",
    top: 64,
    right: 10,
    borderRadius: 5,
    elevation: 5,
    shadowColor: "black",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  dropdownItem: {
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#ddd",
  },
});

export default styles;
