import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    width: 200,
    padding: 24,
    flexDirection: "column",
  },
  section: {
    marginBottom: 3,
  },
  sectionTitle: {
    fontSize: 18,
    color: "#606060",
    marginBottom: 12,
    fontFamily: "Sora",
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
  },
  icon: {
    marginRight: 12,
  },
  buttonText: {
    fontSize: 20,
    fontFamily: "Sora",
  },
  divider: {
    borderBottomWidth: 1,
    borderBottomColor: "#DBD9D9",
    marginBottom: 16,
  },
  selectedButton: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 8,
    backgroundColor: "#E0E0E0",
  },
  selectedButtonText: {
    fontSize: 20,
    fontFamily: "Sora",
    fontWeight: "bold",
  },
});

export default styles;
