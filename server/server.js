const express = require("express");
const bodyParser = require("body-parser");
const cors = require("cors");

const app = express();
app.use(bodyParser.json());
app.use(cors());

app.post("/login", (req, res) => {
  const { username, password } = req.body;

  // 50% chance to accept 
  const isAccepted = Math.random() < 0.5;

  if (isAccepted) {
    res.status(200).json({ message: "Login successful" });
  } else {
    res.status(401).json({ message: "Login failed" });
  }
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});