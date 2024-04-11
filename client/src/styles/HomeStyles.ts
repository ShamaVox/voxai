import { StyleSheet } from "react-native";

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
  },
  interviewsTabs: {
    marginLeft: "auto",
    marginRight: 0,
    flexDirection: "row",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
  },
  tabContainer: {
    flexDirection: "row",
  },
  tabButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
    marginLeft: 10,
    backgroundColor: "#EFEFEF",
  },
  selectedTabButton: {
    backgroundColor: "#2196F3",
  },
  tabButtonText: {
    color: "#333",
  },
  selectedTabButtonText: {
    color: "#fff",
  },
  interviewsContainer: {
    flex: 0.6,
    backgroundColor: "white",
    margin: 20,
    borderRadius: 12,
    width: "60%",
  },
  interviewsTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  interviewItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: 10,
    borderBottomWidth: 1,
    borderBottomColor: "#ddd",
  },
  interviewColumn: {
    flex: 1,
  },
  interviewDate: {
    fontWeight: "bold",
  },
  interviewTime: {
    color: "#666",
  },
  interviewCandidateName: {
    fontSize: 16,
  },
  interviewCurrentCompany: {
    color: "#999",
  },
  interviewInterviewers: {
    fontStyle: "italic",
  },
  interviewRole: {
    fontWeight: "500",
  },
  paginationContainer: {
    alignItems: "center",
    marginTop: 10,
  },
  paginationText: {
    color: "#999",
  },
  interviewsList: {
    flexGrow: 1,
  },
  button: {
    backgroundColor: "#2196F3",
    padding: 15,
    borderRadius: 5,
    alignItems: "center",
    marginTop: 20,
  },
});

export default styles;
