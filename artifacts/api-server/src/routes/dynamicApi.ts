import { Router, Request, Response } from "express";
import { readJson, writeJson } from "../lib/storage";
import { applyEncode, EncodeMethod } from "../lib/encode";
import { sendDiscordWebhook } from "../lib/webhook";
import { checkRateLimit } from "../lib/rateLimit";

interface ApiDef {
  id: string;
  apiId: string;
  apiName: string;
  displayName: string;
  emptyValue: boolean;
  defaultValue: unknown;
  webhookUrl: string | null;
  visibility: "Public" | "Private";
  whitelistIps: string[];
  rateLimit: number | null;
  allowDuplicate: boolean;
  encodeEnabled: boolean;
  encodeMethod: string | null;
  encodePrefix: string | null;
  encodeMap: Record<string, string> | null;
  encodeKey: string | null;
  ownerId: string;
  ownerName: string;
  data: unknown[];
  createdAt: string;
}

const router = Router();

function getIp(req: Request): string {
  const fwd = req.headers["x-forwarded-for"];
  if (fwd) return String(fwd).split(",")[0].trim();
  return req.ip || req.socket.remoteAddress || "N/A";
}

function buildResponse(api: ApiDef): unknown {
  if (api.emptyValue) return {};
  return {
    source: "python 3.15",
    success: true,
    owner: api.ownerName,
    id: api.apiId,
    name: api.displayName,
    total: String(Array.isArray(api.data) ? api.data.length : 0),
    data: api.data,
  };
}

router.get("/v4/:apiId/all", async (req: Request, res: Response) => {
  const { apiId } = req.params;
  const apis = await readJson<ApiDef[]>("apis.json");
  const matching = apis.filter((a) => a.apiId === apiId);
  if (!matching.length) return res.status(404).json({ error: "API not found" });
  const result: Record<string, unknown> = {};
  for (const api of matching) result[api.apiName] = buildResponse(api);
  return res.json(result);
});

router.get("/v4/:apiId/:apiName", async (req: Request, res: Response) => {
  const { apiId, apiName } = req.params;
  const apis = await readJson<ApiDef[]>("apis.json");
  const api = apis.find((a) => a.apiId === apiId && a.apiName === apiName);
  if (!api) return res.status(404).json({ error: "API not found" });
  const ip = getIp(req);
  if (api.visibility === "Private" && api.whitelistIps.length && !api.whitelistIps.includes(ip))
    return res.status(403).json({ err: "You do not have permission to access this API" });
  return res.json(buildResponse(api));
});

router.post("/v4/:apiId/:apiName", async (req: Request, res: Response) => {
  const { apiId, apiName } = req.params;
  const apis = await readJson<ApiDef[]>("apis.json");
  const idx = apis.findIndex((a) => a.apiId === apiId && a.apiName === apiName);
  if (idx === -1) return res.status(404).json({ error: "API not found" });
  const api = apis[idx];
  const ip = getIp(req);
  if (api.visibility === "Private" && api.whitelistIps.length && !api.whitelistIps.includes(ip))
    return res.status(403).json({ err: "You do not have permission to access this API" });
  if (api.rateLimit) {
    if (!checkRateLimit(`v4:${apiId}:${apiName}:${ip}`, api.rateLimit))
      return res.status(429).json({ error: "Rate limit exceeded" });
  }
  let body: Record<string, unknown> = req.body || {};
  if (api.encodeEnabled && api.encodeMethod && api.encodeKey) {
    body = applyEncode(
      body,
      api.encodeKey,
      api.encodeMethod as EncodeMethod,
      api.encodeMap ?? undefined,
      api.encodePrefix ?? undefined
    );
  }
  if (!api.allowDuplicate) {
    const dup = api.data.some((d) => JSON.stringify(d) === JSON.stringify(body));
    if (dup) return res.status(409).json({ error: "Duplicate data" });
  }
  apis[idx].data.push(body);
  await writeJson("apis.json", apis);
  if (api.webhookUrl) {
    sendDiscordWebhook(api.webhookUrl, api.displayName, ip, req.headers as Record<string, string | string[] | undefined>).catch(() => {});
  }
  return res.json(buildResponse(apis[idx]));
});

router.post("/v3/:apiId/send/:apiName", async (req: Request, res: Response) => {
  const { apiId, apiName } = req.params;
  const apis = await readJson<ApiDef[]>("apis.json");
  const api = apis.find((a) => a.apiId === apiId && a.apiName === apiName);
  if (!api || !api.webhookUrl) return res.status(404).json({ error: "API or webhook not found" });
  const ip = getIp(req);
  if (api.rateLimit) {
    if (!checkRateLimit(`v3:${apiId}:${apiName}:${ip}`, api.rateLimit))
      return res.status(429).json({ error: "Rate limit exceeded" });
  }
  let content: string = req.body?.content ?? JSON.stringify(req.body);
  content = content.replace(/@everyone/g, "@\u200beveryone").replace(/@here/g, "@\u200bhere");
  try {
    await fetch(api.webhookUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    return res.json({ success: true });
  } catch {
    return res.status(500).json({ error: "Failed to send webhook" });
  }
});

export default router;
