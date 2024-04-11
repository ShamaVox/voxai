import React, { FC, useState, useEffect } from "react";
import { View, Text, Image } from "react-native";
import axios from "axios";
import styles from "./styles/DashboardStyles";
import { SERVER_URL } from "./Constants";

const Dashboard: FC = () => {
  return <InsightsScreen />;
};

const InsightsScreen = () => {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights = async () => {
    try {
      const response = await axios.get(SERVER_URL + "insights");
      setInsights(response.data);
    } catch (error) {
      console.error("Error fetching insights:", error);
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
          icon="icon1"
          value={insights.candidateStage}
          title="Candidate Stage"
        />
        <InsightBox
          icon="icon2"
          value={insights.fittingJobApplication + " %"}
          percentage={insights.fittingJobApplicationPercentage}
          title="Fitting Job Application"
        />
        <InsightBox
          icon="icon3"
          value={insights.averageInterviewPace + " days"}
          percentage={insights.averageInterviewPacePercentage}
          title="Average Interview Pace"
        />
        <InsightBox
          icon="icon4"
          value={`${insights.lowerCompensationRange}K - ${insights.upperCompensationRange}K`}
          title="Compensation Range"
        />
      </View>
    </View>
  );
};

const InsightBox = ({ icon, value, title, percentage = NaN }) => {
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

export default Dashboard;
