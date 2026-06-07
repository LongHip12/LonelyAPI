import { Router, Request, Response } from "express";
import { readJson, writeJson } from "../lib/storage";
import { applyRandomEncode, EncodeDataType } from "../lib/encode";

interface BloxFruitData {
  servers: Record<string, unknown[]>;
}

type BfParams = { server: string };

const router = Router();

function getEncodeData(): EncodeDataType {
  try {
    return JSON.parse(process.env["ENCODE_DATA"] || "{}");
  } catch {
    return {};
  }
}

router.get("/v1/bloxfruit/all", async (_req: Request, res: Response) => {
  const bf = await readJson<BloxFruitData>("bloxfruit.json");
  const all: unknown[] = [];
  for (const arr of Object.values(bf.servers)) all.push(...arr);
  return res.json({ source: "python 3.15", success: true, total: String(all.length), data: all });
});

router.get("/v1/bloxfruit/:server", async (req: Request<BfParams>, res: Response) => {
  const bf = await readJson<BloxFruitData>("bloxfruit.json");
  const key = req.params.server;
  const server = bf.servers[key] || [];
  return res.json({ source: "python 3.15", success: true, total: String(server.length), data: server });
});

router.post("/v1/bloxfruit/:server", async (req: Request<BfParams>, res: Response) => {
  const bf = await readJson<BloxFruitData>("bloxfruit.json");
  const key = req.params.server;
  if (!bf.servers[key]) bf.servers[key] = [];
  let body: Record<string, unknown> = req.body || {};
  const encodeData = getEncodeData();
  if (Object.keys(encodeData).length > 0) {
    body = applyRandomEncode(body, "JobId", encodeData) as Record<string, unknown>;
  }
  bf.servers[key].push(body);
  await writeJson("bloxfruit.json", bf);
  const all: unknown[] = [];
  for (const arr of Object.values(bf.servers)) all.push(...arr);
  return res.json({ source: "python 3.15", success: true, total: String(all.length), data: bf.servers[key] });
});

export default router;
