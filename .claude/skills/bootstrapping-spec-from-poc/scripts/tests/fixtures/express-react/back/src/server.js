const express = require("express");
const cors = require("cors");
const app = express();
app.use(cors());

app.get("/api/orders", (req, res) => res.json([]));
app.post("/api/orders", (req, res) => {
  if (!req.body.total) return res.status(422).json({ error: "total required" });
  res.status(201).json(req.body);
});
app.delete("/api/orders/:id", (req, res) => res.status(204).end());

app.listen(3000);
