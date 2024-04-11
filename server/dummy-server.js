const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(bodyParser.json());
app.use(cors());

let isAccepted = false;

app.post("/login", (req, res) => {
  const { username, password } = req.body;

  // reject the first, accept the second

  if (isAccepted) {
    res.status(200).json({ message: "Login successful" });
  } else {
    res.status(401).json({ message: "Login failed" });
  }

  isAccepted = !isAccepted;
});

function getRandom(max, negative = false) {
  if (!negative) {
    return Math.round(Math.random() * max);
  } else {
    return Math.round((Math.random() - 0.5) * (max * 2));
  }
}

const firstNames = [
  "John",
  "Emma",
  "Michael",
  "Olivia",
  "William",
  "Ava",
  "James",
  "Sophia",
  "Benjamin",
  "Isabella",
];
const lastNames = [
  "Smith",
  "Johnson",
  "Brown",
  "Taylor",
  "Miller",
  "Davis",
  "Garcia",
  "Wilson",
  "Martinez",
  "Anderson",
];
const roles = [
  "Software Engineer",
  "Product Manager",
  "UX Designer",
  "Data Analyst",
  "Marketing Specialist",
];
const companies = [
  "ABC Inc.",
  "XYZ Corp.",
  "Acme Co.",
  "Delta Ltd.",
  "Epsilon LLC",
];

function getRandomItem(array) {
  return array[Math.floor(Math.random() * array.length)];
}

function getRandomDate() {
  const start = new Date(2023, 0, 1);
  const end = new Date(2023, 11, 31);
  return new Date(
    start.getTime() + Math.random() * (end.getTime() - start.getTime())
  )
    .toISOString()
    .split("T")[0];
}

function getRandomTime() {
  const hours = Math.floor(Math.random() * 24);
  const minutes = Math.floor(Math.random() * 60);
  return `${hours.toString().padStart(2, "0")}:${minutes
    .toString()
    .padStart(2, "0")}`;
}

app.get("/insights", (req, res) => {
  let lowerCompensationRange = getRandom(100);
  const insights = {
    candidateStage: getRandom(5),
    fittingJobApplication: getRandom(10),
    fittingJobApplicationPercentage: getRandom(25, true),
    averageInterviewPace: getRandom(7),
    averageInterviewPacePercentage: getRandom(25, true),
    lowerCompensationRange: lowerCompensationRange,
    upperCompensationRange: lowerCompensationRange + getRandom(100),
  };

  res.json(insights);
});

app.get("/interviews", (req, res) => {
  const interviews = Array.from({ length: 10 }, (_, index) => ({
    id: index + 1,
    date: getRandomDate(),
    time: getRandomTime(),
    candidateName: `${getRandomItem(firstNames)} ${getRandomItem(lastNames)}`,
    currentCompany: getRandomItem(companies),
    interviewers: `${getRandomItem(firstNames)} ${getRandomItem(
      lastNames
    )}, ${getRandomItem(firstNames)} ${getRandomItem(lastNames)}`,
    role: getRandomItem(roles),
  }));

  res.json(interviews);
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
