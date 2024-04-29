import React, { FC, useState, useEffect } from "react";
import { View, Text, Image } from "react-native";
import axios from "axios";
import styles from "./styles/DashboardStyles";
import { SERVER_ENDPOINT, DASHBOARD_LOGGING } from "./utils/Constants";

interface InsightBoxProps {
  testID: string;
  icon: string;
  value: string;
  title: string;
  percentage?: number;
}

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

const InsightsScreen: FC = () => {
  const [insights, setInsights] = useState(null);

  useEffect(() => {
    fetchInsights();
  }, []);

  const fetchInsights: () => Promise<void> = async () => {
    try {
      const response = await axios.get(SERVER_ENDPOINT("insights"));
      setInsights(response.data);
    } catch (error) {
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

const Dashboard: FC = () => {
  return <InsightsScreen />;
};

export default Dashboard;
