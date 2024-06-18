import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  heading: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
  },
  detailItem: {
    marginBottom: 15,
  },
  label: {
    fontWeight: "bold",
  },
  grayBackground: {
    backgroundColor: "#CCCCCC",
  },
  subheading: {
    fontSize: 18,
    fontWeight: "bold",
    marginTop: 20,
  },
  transcriptText: {
    fontSize: 16,
    marginBottom: 10,
  },
  positiveText: {
    color: "green",
  },
  negativeText: {
    color: "red",
  },
  blueBackground: {
    backgroundColor: "blue",
    padding: 10,
    borderRadius: 5,
    alignItems: "center",
    marginTop: 10,
  },
});

export default styles;
