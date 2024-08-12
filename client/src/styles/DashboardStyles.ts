import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  title: {
    fontSize: 20,
    fontWeight: "bold",
    marginBottom: 20,
  },
  insightsContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    flexWrap: "wrap",
    width: "70%",
  },
  insightBox: {
    alignItems: "center",
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    marginBottom: 20,
  },
  insightNumbers: {
    flexDirection: "row",
    alignItems: "center",
  },
  value: {
    fontSize: 18,
    fontWeight: "bold",
    marginRight: 8,
  },
  percentageBox: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 4,
  },
  positivePercentage: {
    backgroundColor: "green",
  },
  negativePercentage: {
    backgroundColor: "red",
  },
  percentageText: {
    color: "white",
    fontSize: 12,
  },
  icon: {
    marginRight: 8,
  },
  addRolesContainer: {
    marginTop: 20, 
    padding: 10,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
  },
  addRolesHeader: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 10,
    marginBottom: 10,
    borderRadius: 4,
  },
  addRolesDescription: {
    fontSize: 14,
    marginBottom: 10,
  },
});

export default styles;
