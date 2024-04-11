import React, { FC, useContext, useState, useEffect } from "react";
import { View, Pressable, Text, FlatList } from "react-native";
import { useNavigation } from "@react-navigation/native";
import { AuthContext } from "./AuthContext";
import styles from "./styles/HomeStyles";
import axios from "axios";
import { SERVER_ENDPOINT } from "./Constants";

// TODO: Fix pagination
// TODO: Fix dates & sort by date

const Home: FC = () => {
  const navigation = useNavigation();
  const { isLoggedIn } = useContext(AuthContext);
  const [interviews, setInterviews] = useState([]);
  const [selectedTab, setSelectedTab] = useState("Upcoming");

  useEffect(() => {
    if (isLoggedIn) {
      fetchInterviews();
    }
  }, [isLoggedIn]);

  const fetchInterviews = async () => {
    try {
      const response = await axios.get(SERVER_ENDPOINT("interviews"));
      setInterviews(response.data);
    } catch (error) {
      console.error("Error fetching interviews:", error);
    }
  };

  const handleLoginClick = () => {
    navigation.navigate("Login");
  };

  const renderInterviewItem = ({ item }) => (
    <View style={styles.interviewItem}>
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
              data={selectedTab === "Upcoming" ? interviews : []}
              renderItem={renderInterviewItem}
              keyExtractor={(item) => item.id.toString()}
              style={styles.interviewsList}
            />
            <View style={styles.paginationContainer}>
              <Text style={styles.paginationText}>Showing page 1 of 1</Text>
            </View>
          </View>
        </>
      ) : (
        <>
          <Text>This is a placeholder homepage</Text>
          <Pressable onPress={handleLoginClick} style={styles.button}>
            <Text>Login</Text>
          </Pressable>
        </>
      )}
    </View>
  );
};

export default Home;
