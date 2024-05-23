import React, { FC, useContext, useState, useEffect } from "react";
import {
  View,
  Pressable,
  Text,
  FlatList,
  GestureResponderEvent,
  ListRenderItem,
  TextInput,
} from "react-native";
import { useNavigation } from "@react-navigation/native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/HomeStyles";
import axios from "axios";
import { HOME_LOGGING } from "./config/Logging";
import { SERVER_ENDPOINT, handleLogoutResponse } from "./utils/Axios";

// TODO: Fix pagination
// TODO: Fix dates & sort by date

/**
 * The Home component displays upcoming interviews and other relevant information for logged-in users.
 * For logged-out users, it shows a placeholder homepage.
 */
const Home: FC = () => {
  const navigation = useNavigation();
  const { isLoggedIn, handleLogout } = useContext(AuthContext);
  const [interviews, setInterviews] = useState([]);
  const [selectedTab, setSelectedTab] = useState("Upcoming");
  const [temporaryUrl, setTemporaryUrl] = useState(""); // Placeholder to test bot from logged-out homepage

  useEffect(() => {
    if (isLoggedIn) {
      fetchInterviews();
    }
  }, [isLoggedIn]);

  /**
   * Fetches interview data from the server and updates the state.
   */
  const fetchInterviews: () => void = async () => {
    try {
      const response = await axios.get(SERVER_ENDPOINT("interviews"));
      setInterviews(response.data);
    } catch (error) {
      await handleLogoutResponse(handleLogout, error.response, HOME_LOGGING);
      if (HOME_LOGGING) {
        console.log("Error fetching interviews:", error);
      }
    }
  };

  /**
   * Handles the login button click by navigating to the Login screen.
   * @param arg The GestureResponderEvent object.
   */
  const handleLoginClick: (
    arg: GestureResponderEvent
  ) => Promise<void> = async () => {
    await navigation.navigate("Login");
  };

  /**
   * Renders a single interview item within the interview list.
   * @param item The interview data object to be rendered.
   */
  const renderInterviewItem: ListRenderItem<any> = ({ item }) => (
    <View testID="interview-table-entry" style={styles.interviewItem}>
      <View style={styles.interviewColumn}>
        <Text style={styles.interviewDate}>{item.date}</Text>
        <Text style={styles.interviewTime}>{item.time}</Text>
      </View>
      <View style={styles.interviewColumn}>
        <Text style={styles.interviewCandidateName}>{item.candidateName}</Text>
        <Text style={styles.interviewCurrentCompany}>
          {item.currentCompany}
        </Text>
      </View>
      <View style={styles.interviewColumn}>
        <Text style={styles.interviewInterviewers}>{item.interviewers}</Text>
      </View>
      <View style={styles.interviewColumn}>
        <Text style={styles.interviewRole}>{item.role}</Text>
      </View>
    </View>
  );

  const temporaryBotJoinMeeting = () => {
    axios.post(SERVER_ENDPOINT("join_meeting"), {
      url: temporaryUrl,
    });
  };

  return (
    <View style={styles.container}>
      {isLoggedIn ? (
        <>
          <Text style={styles.title}>Overview</Text>
          <View style={styles.tabContainer}></View>
          <View style={styles.interviewsContainer}>
            <View style={styles.header}>
              <Text style={styles.interviewsTitle}>My Interviews</Text>
              <View style={styles.interviewsTabs}>
                <Pressable
                  testID="upcoming-tab"
                  style={[
                    styles.tabButton,
                    selectedTab === "Upcoming" && styles.selectedTabButton,
                  ]}
                  onPress={() => setSelectedTab("Upcoming")}
                >
                  <Text
                    style={[
                      styles.tabButtonText,
                      selectedTab === "Upcoming" &&
                        styles.selectedTabButtonText,
                    ]}
                  >
                    Upcoming
                  </Text>
                </Pressable>
                <Pressable
                  testID="completed-tab"
                  style={[
                    styles.tabButton,
                    selectedTab === "Completed" && styles.selectedTabButton,
                  ]}
                  onPress={() => setSelectedTab("Completed")}
                >
                  <Text
                    style={[
                      styles.tabButtonText,
                      selectedTab === "Completed" &&
                        styles.selectedTabButtonText,
                    ]}
                  >
                    Completed
                  </Text>
                </Pressable>
              </View>
            </View>
            <FlatList
              testID="interview-list"
              data={selectedTab === "Upcoming" ? interviews : []}
              renderItem={renderInterviewItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.interviewsList}
            />
            {selectedTab === "Completed" ? (
              <>
                {" "}
                <Text>This is a placeholder for the Completed tab</Text>{" "}
              </>
            ) : (
              <> </>
            )}
            <View style={styles.paginationContainer}>
              <Text style={styles.paginationText}>Showing page 1 of 1</Text>
            </View>
          </View>
        </>
      ) : (
        <>
          <Text>This is a placeholder homepage</Text>
          <Pressable
            testID="homepage-login"
            onPress={async (e: GestureResponderEvent) => {
              await handleLoginClick(e);
            }}
            style={styles.button}
          >
            <Text>Login</Text>
          </Pressable>
          <TextInput
            style={styles.grayBackground}
            onChangeText={setTemporaryUrl}
          />
          <Pressable onPress={temporaryBotJoinMeeting}>
            <Text>Join meeting with bot at this URL</Text>
          </Pressable>
        </>
      )}
    </View>
  );
};

export default Home;
