import { FC, useState } from "react";
import styles from "./styles/InterviewStyles";
import { View, Text, StyleSheet, TextInput, Pressable } from "react-native";
import { RouteProp } from "@react-navigation/native";
import { RootStackParamList } from "./App";
import { INTERVIEW_LOGGING } from "./config/Logging";
import { SERVER_ENDPOINT, handleLogoutResponse } from "./utils/Axios";
import axios from "axios";

export interface InterviewData {
  id: number;
  date: string;
  time: string;
  candidateName: string;
  currentCompany: string;
  interviewers: string;
  role: string;
  analysisId: string | undefined;
}

type InterviewScreenRouteProp = RouteProp<RootStackParamList, "Interview">;

const InterviewScreen: FC<{ route: InterviewScreenRouteProp }> = ({
  route,
}) => {
  const { interview } = route.params;
  const [updatedInterview, setUpdatedInterview] = useState<InterviewData>(
    interview
  );
  const [interviewAnalysisId, setInterviewAnalysisId] = useState("");
  const [analysisResults, setAnalysisResults] = useState<any>(null);

  /**
   * Sends the URL to the server to link an interview to its transcript and analysis.
   * @param url The URL to link this interview to.
   */
  const sendInterviewAnalysisId = async () => {
    const response = await axios.post(SERVER_ENDPOINT("set_recall_id"), {
      recall_id: interviewAnalysisId,
      id: updatedInterview.id,
    });
    if (response.data.success) {
      setUpdatedInterview({
        ...updatedInterview,
        analysisId: interviewAnalysisId,
      });
    }
  };

  /**
   * Gets the analysis results for this interview.
   */
  const getAnalysisResults = async () => {
    try {
      const response = await axios.post(SERVER_ENDPOINT("analyze_interview"), {
        id: updatedInterview.analysisId,
      });
      setAnalysisResults(response.data["intelligence_response"]);
    } catch (error) {
      console.log("Error fetching analysis:", error);
    }
  };

  return (
    <View style={styles.container}>
      {!updatedInterview.analysisId ? (
        <View>
          <Text style={styles.heading}> Link Interview with Analysis </Text>
          <TextInput
            style={styles.grayBackground}
            onChangeText={setInterviewAnalysisId}
            placeholder="Paste recall.ai bot ID for this interview here"
          />
          <Pressable onPress={sendInterviewAnalysisId}>
            <Text>Submit</Text>
          </Pressable>
        </View>
      ) : (
        <View>
          <Text style={styles.heading}>Analysis</Text>
          <Pressable onPress={getAnalysisResults} style={styles.blueBackground}>
            <Text>Get Analysis Results</Text>
          </Pressable>
          {analysisResults && ( // Conditionally render analysis results
            <View>
              <Text style={styles.subheading}>Summary</Text>
              <Text>{analysisResults["assembly_ai.summary"]}</Text>
              <Text style={styles.subheading}>Transcript</Text>
              <Text>
                Color coding key:{" "}
                <Text style={styles.positiveText}>positive sentiment,</Text>{" "}
                neutral sentiment,{" "}
                <Text style={styles.negativeText}>negative sentiment</Text>
              </Text>
              {analysisResults["assembly_ai.sentiment_analysis_results"].map(
                (segment: any, index: number) => (
                  <Text
                    key={index}
                    style={[
                      segment.sentiment === "POSITIVE" && styles.positiveText,
                      segment.sentiment === "NEGATIVE" && styles.negativeText,
                    ]}
                  >
                    {segment.text}
                  </Text>
                )
              )}
            </View>
          )}
        </View>
      )}
      <Text style={styles.heading}>Interview Details</Text>
      <View style={styles.detailItem}>
        <Text style={styles.label}>Date:</Text>
        <Text>{updatedInterview.date}</Text>
      </View>
      <View style={styles.detailItem}>
        <Text style={styles.label}>Time:</Text>
        <Text>{updatedInterview.time}</Text>
      </View>
      <View style={styles.detailItem}>
        <Text style={styles.label}>Candidate:</Text>
        <Text>{updatedInterview.candidateName}</Text>
      </View>
      <View style={styles.detailItem}>
        <Text style={styles.label}>Current Company:</Text>
        <Text>{updatedInterview.currentCompany}</Text>
      </View>
      <View style={styles.detailItem}>
        <Text style={styles.label}>Role:</Text>
        <Text>{updatedInterview.role}</Text>
      </View>
      <View style={styles.detailItem}>
        <Text style={styles.label}>Interviewers:</Text>
        {updatedInterview.interviewers
          .split(",")
          .map((interviewer: string, index: number) => (
            <Text key={index}>{interviewer.trim()}</Text>
          ))}
      </View>
    </View>
  );
};

export default InterviewScreen;
