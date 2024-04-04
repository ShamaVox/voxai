import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    width: 250,
    padding: 24,
    flexDirection: "column",
    backgroundColor: "#F2F2F2",
    height: "100%",
  },
  section: {
    marginBottom: 3,
  },
  sectionTitle: {
    fontSize: 16,
    color: "#606060",
    marginBottom: 12,
    fontFamily: "Sora",
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    marginBottom: 16,
    borderRadius: 10,
    paddingLeft: 10,
  },
  icon: {
    marginRight: 12,
  },
  buttonText: {
    fontSize: 18,
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
    marginBottom: 16,
    backgroundColor: "#FFFFFF95",
    borderWidth: 2,
    borderColor: "#FFFFFF",
    borderRadius: 10,
    width: 150,
    paddingLeft: 10,
  },
  selectedButtonText: {
    fontSize: 18,
    fontFamily: "Sora",
    fontWeight: "bold",
  },
});

export default styles;
