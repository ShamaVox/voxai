import React, { useEffect, useState } from "react";
import VoxAIInvestorDemo from "./VoxAIInvestorDemo";

interface TranscriptEntry {
  speaker: string;
  text: string;
}

const App: React.FC = () => {
  const [insights, setInsights] = useState<Record<string, any>>({});
  const [skills, setSkills] = useState<Record<string, Record<string, { score: number }>>>({});
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log("Fetching data...");

        const fetchJson = async (url: string) => {
          const response = await fetch(url);
          const text = await response.text();

          if (text.startsWith("<!DOCTYPE html>")) {
            throw new Error(`Invalid JSON: ${url} is returning HTML instead of JSON`);
          }

          return JSON.parse(text);
        };

        const insightsData = await fetchJson("/sample-insights.json");
        const skillsData = await fetchJson("/sample-skills.json");
        const transcriptData = await fetchJson("/sample-interview.json");

        console.log("✅ Insights Data:", insightsData);
        console.log("✅ Skills Data:", skillsData);
        console.log("✅ Transcript Data:", transcriptData);

        if (!Array.isArray(transcriptData)) {
          throw new Error("Transcript data is not an array");
        }

        setInsights(insightsData);
        setSkills(skillsData);
        setTranscript(transcriptData);
        setLoading(false);
      } catch (error) {
        console.error("❌ Error loading data:", error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <p>Loading data...</p>;
  }

  return <VoxAIInvestorDemo insights={insights} skills={skills} transcript={transcript} />;
};

export default App;
