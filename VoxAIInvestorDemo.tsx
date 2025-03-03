import React from 'react';
import { Card, CardContent, Typography, Box, Grid } from '@mui/material';
import {
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

interface TranscriptEntry {
  speaker: string;
  text: string;
}

interface SkillEntry {
  name: string;
  score: number;
  speaker: string;
}

interface InsightEntry {
  sentiment?: { summary: string[] };
  engagement?: { summary: string[] };
}

interface VoxAIInvestorDemoProps {
  insights: Record<string, InsightEntry>;
  skills: Record<string, Record<string, { score: number }>>;
  transcript: TranscriptEntry[];
}

const VoxAIInvestorDemo: React.FC<VoxAIInvestorDemoProps> = ({ insights = {}, skills = {}, transcript = [] }) => {
  console.log("Insights:", insights);
  console.log("Skills:", skills);
  console.log("Transcript:", transcript);

  console.log("Insights:", insights);
  console.log("Skills:", skills);
  console.log("Transcript:", transcript);
  
  const sentimentData = Object.keys(insights || {}).map((speaker) => ({
    name: speaker,
    sentiment: insights[speaker]?.sentiment?.summary?.length || 0,
  }));
  
  const engagementData = Object.keys(insights || {}).map((speaker) => ({
    name: speaker,
    engagement: insights[speaker]?.engagement?.summary?.length || 0,
  }));
  
  const speakerCounts: Record<string, number> =
    Array.isArray(transcript) && transcript.length > 0
      ? transcript.reduce<Record<string, number>>((acc, entry) => {
          acc[entry.speaker] = (acc[entry.speaker] || 0) + 1;
          return acc;
        }, {})
      : {};
  
  const speakerData = Object.keys(speakerCounts).map((key) => ({
    name: key,
    value: speakerCounts[key],
  }));
  
  const skillsData =
    skills && Object.keys(skills).length > 0
      ? Object.keys(skills).flatMap((speaker) =>
          Object.keys(skills[speaker]).map((skill) => ({
            name: skill,
            score: skills[speaker][skill]?.score || 0,
            speaker: speaker,
          }))
        )
      : [];

  return (
    <Grid container spacing={3}>
      {sentimentData.length > 0 && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Sentiment Analysis</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sentimentData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="sentiment" fill="#3f51b5" barSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      {engagementData.length > 0 && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Engagement Levels</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={engagementData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="engagement" fill="#00C49F" barSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      {speakerData.length > 0 && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Speaker Contribution</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={speakerData} cx="50%" cy="50%" outerRadius={100} label dataKey="value">
                    {speakerData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      {skillsData.length > 0 && (
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Skills Breakdown</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={skillsData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value, name, props) => [`Score: ${value}`, `Speaker: ${props.payload.speaker}`]} />
                  <Legend />
                  <Bar dataKey="score" fill="#FF8042" barSize={30} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      )}

      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6">Interview Transcript & TL;DR Summary</Typography>
            <Box sx={{ maxHeight: 300, overflow: 'auto', padding: 2 }}>
              {Array.isArray(transcript) && transcript.length > 0 ? (
                transcript.map((entry, index) => (
                  <Typography key={index} variant="body2" gutterBottom>
                    <strong>{entry.speaker}: </strong>{entry.text}
                  </Typography>
                ))
              ) : (
                <Typography variant="body2" color="textSecondary">
                  No transcript available.
                </Typography>
              )}
            </Box>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default VoxAIInvestorDemo;
