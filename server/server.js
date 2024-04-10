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

app.get("/insights", (req, res) => {
  const insights = {
    candidateStage: getRandom(5),
    fittingJobApplication: getRandom(10),
    fittingJobApplicationPercentage: getRandom(25, true),
    averageInterviewPace: getRandom(7),
    averageInterviewPacePercentage: getRandom(25, true),
    lowerCompensationRange: getRandom(100000),
    upperCompensationRange: getRandom(200000),
  };

  res.json(insights);
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
