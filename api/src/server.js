// api/server.js
import express from "express";
import cors from "cors";

const app = express();
app.use(express.json());

const allowed = (process.env.ALLOWED_ORIGINS || "")
  .split(",").map(s => s.trim()).filter(Boolean);
app.use(cors({ origin: allowed.length ? allowed : true }));

app.get("/health", (_req, res) => res.json({ ok: true, service: "api" }));
app.get("/", (_req, res) => res.send("API up"));

const port = Number(process.env.PORT || 8080);
app.listen(port, () => console.log(`API listening on :${port}`));