import React, { FC, useState, useEffect, useContext } from "react";
import { View, Text, Image, Button, TextInput } from "react-native";
import axios from "axios";
import styles from "./styles/DashboardStyles";
import { AuthContext } from "./AuthContext";
import { SERVER_ENDPOINT, handleLogoutResponse } from "./utils/Axios";
import { DASHBOARD_LOGGING } from "./config/Logging";

interface InsightBoxProps {
  testID: string;
  icon: string;
  value: string;
  title: string;
  percentage?: number;
}

/**
 * Renders an insight box with an icon, value, title, and optional percentage change.
 */
const InsightBox: FC<InsightBoxProps> = ({
  testID,
  icon,
  value,
  title,
  percentage = NaN, // temporary default
}) => {
  return (
    <View style={styles.insightBox}>
      <View style={styles.insightNumbers}>
        <Image
          source={require("../assets/icons/dashboard.png")} // Temporary
          style={styles.icon}
        />
        <Text style={styles.value}>{value}</Text>
        {!isNaN(percentage) && (
          <View
            style={[
              styles.percentageBox,
              percentage >= 0
                ? styles.positivePercentage
                : styles.negativePercentage,
            ]}
          >
            <Text style={styles.percentageText}>
              {percentage > 0 && "+"}
              {percentage}%
            </Text>
          </View>
        )}
      </View>
      <Text style={styles.title}>{title}</Text>
    </View>
  );
};

/**
 * Screen displaying insights data fetched from the server.
 */
const InsightsScreen: FC = () => {
  const [insights, setInsights] = useState(null);
  const { handleLogout } = useContext(AuthContext);

  useEffect(() => {
    fetchInsights();
  }, []);

  /**
   * Fetches insights data from the server and updates the state.
   */
  const fetchInsights: () => Promise<void> = async () => {
    try {
      const response = await axios.get(SERVER_ENDPOINT("insights"));
      setInsights(response.data);
    } catch (error) {
      await handleLogoutResponse(
        handleLogout,
        error.response,
        DASHBOARD_LOGGING
      );
      if (DASHBOARD_LOGGING) {
        console.log("Error fetching insights:", error);
      }
    }
  };

  if (!insights) {
    return <Text>Loading...</Text>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Insights</Text>
      <View style={styles.insightsContainer}>
        <InsightBox
          testID="insight-box-candidate-stage"
          icon="icon1"
          value={insights.candidateStage}
          title="Candidate Stage"
        />
        <InsightBox
          testID="insight-box-fitting-job-application"
          icon="icon2"
          value={insights.fittingJobApplication + "%"}
          percentage={insights.fittingJobApplicationPercentage}
          title="Fitting Job Application"
        />
        <InsightBox
          testID="insight-box-average-interview-pace"
          icon="icon3"
          value={insights.averageInterviewPace + " days"}
          percentage={insights.averageInterviewPacePercentage}
          title="Average Interview Pace"
        />
        <InsightBox
          testID="insight-box-compensation-range"
          icon="icon4"
          value={`${insights.lowerCompensationRange}K - ${insights.upperCompensationRange}K`}
          title="Compensation Range"
        />
      </View>
    </View>
  );
};

/**
 * The Dashboard component displays insights and data visualizations related to the user's recruitment activities.
 */
const Dashboard: FC = () => {
  const [greenhouseUrl, setGreenhouseUrl] = useState(
    "https://boards.greenhouse.io/your-company"
  );

const { handleLogout } = useContext(AuthContext);

  const handleAddRoles = async () => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("apis/greenhouse"), {
        url: greenhouseUrl,
      });
      // Handle successful response, e.g., show a success message
      console.log("Roles added successfully:", response.data);
    } catch (error) {
      await handleLogoutResponse(
        handleLogout,
        error.response,
        DASHBOARD_LOGGING
      );
      if (DASHBOARD_LOGGING) {
        console.log("Error adding roles:", error);
      }
    }
  };

  return (
    <View style={styles.container}>
      <InsightsScreen />
      <View style={styles.addRolesContainer}>
        <Text style={styles.addRolesHeader}>Add roles from Greenhouse</Text>
        <TextInput
          style={styles.input}
          value={greenhouseUrl}
          onChangeText={setGreenhouseUrl}
          placeholder="https://boards.greenhouse.io/your-company"
        />
        <Text style={styles.addRolesDescription}>
          This will add all of the roles listed on the linked page to your
          company, with you as the hiring manager.
        </Text>
        <Button title="Add Roles" onPress={handleAddRoles} />
      </View>
    </View>
  );
};

export default Dashboard;
