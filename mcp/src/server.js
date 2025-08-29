// mcp/server.js
import express from "express";
const app = express();
app.use(express.json());

app.get("/tools", (_req, res) => {
  res.json({
    tools: [
      { name: "seed.getRosters", description: "Return seeded rosters" },
      { name: "seed.getMatchups", description: "Return seeded matchups" }
    ]
  });
});

app.get("/health", (_req, res) => res.json({ ok: true, service: "mcp" }));

const port = Number(process.env.PORT || 9000);
app.listen(port, () => console.log(`MCP listening on :${port}`));