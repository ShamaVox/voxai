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

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});
