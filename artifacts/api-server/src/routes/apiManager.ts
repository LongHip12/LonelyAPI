import { Router, Request, Response, NextFunction } from "express";
import { randomBytes } from "node:crypto";
import { readJson, writeJson } from "../lib/storage";
import { sess, requireAuth } from "../lib/session";

export interface ApiDef {
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

router.get("/apis", requireAuth, async (req: Request, res: Response) => {
  const apis = await readJson<ApiDef[]>("apis.json");
  const page = Math.max(1, parseInt(String(req.query.page ?? "1")));
  const s = sess(req);
  const all = s.isAdmin ? apis : apis.filter((a) => a.ownerId === s.userId);
  const total = all.length;
  const pageSize = 15;
  const paged = all.slice((page - 1) * pageSize, page * pageSize);
  return res.json({ apis: paged, total, page, pages: Math.ceil(total / pageSize) || 1 });
});

router.post("/apis", requireAuth, async (req: Request, res: Response) => {
  const {
    apiId, apiName, displayName, emptyValue, defaultValue,
    webhookUrl, visibility, whitelistIps, rateLimit,
    allowDuplicate, encodeEnabled, encodeMethod, encodePrefix, encodeMap, encodeKey,
  } = req.body;
  const s = sess(req);
  const finalApiId = apiId || randomBytes(5).toString("hex");
  const finalApiName = apiName || randomBytes(5).toString("hex");
  const apis = await readJson<ApiDef[]>("apis.json");
  const newApi: ApiDef = {
    id: randomBytes(8).toString("hex"),
    apiId: finalApiId,
    apiName: finalApiName,
    displayName: displayName || finalApiName,
    emptyValue: !!emptyValue,
    defaultValue: emptyValue ? null : (defaultValue ?? null),
    webhookUrl: webhookUrl || null,
    visibility: visibility === "Private" ? "Private" : "Public",
    whitelistIps:
      visibility === "Private" && whitelistIps
        ? String(whitelistIps).split(",").map((ip: string) => ip.trim()).filter(Boolean)
        : [],
    rateLimit: rateLimit ? parseInt(String(rateLimit)) : null,
    allowDuplicate: !!allowDuplicate,
    encodeEnabled: !!encodeEnabled,
    encodeMethod: encodeEnabled ? encodeMethod || null : null,
    encodePrefix: encodeEnabled && encodeMethod === "Custom" ? encodePrefix || null : null,
    encodeMap: encodeEnabled && encodeMethod === "Custom" ? encodeMap || null : null,
    encodeKey: encodeEnabled ? encodeKey || null : null,
    ownerId: s.userId!,
    ownerName: s.username!,
    data: [],
    createdAt: new Date().toISOString(),
  };
  apis.push(newApi);
  await writeJson("apis.json", apis);
  return res.json({ success: true, api: { id: newApi.id, apiId: newApi.apiId, apiName: newApi.apiName } });
});

router.put("/apis/:id", requireAuth, async (req: Request, res: Response) => {
  const apis = await readJson<ApiDef[]>("apis.json");
  const idx = apis.findIndex((a) => a.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "API not found" });
  const api = apis[idx];
  const s = sess(req);
  if (api.ownerId !== s.userId && !s.isAdmin)
    return res.status(403).json({ error: "Forbidden" });
  const {
    apiId, apiName, displayName, emptyValue, defaultValue,
    webhookUrl, visibility, whitelistIps, rateLimit,
    allowDuplicate, encodeEnabled, encodeMethod, encodePrefix, encodeMap, encodeKey,
  } = req.body;
  apis[idx] = {
    ...api,
    apiId: apiId ?? api.apiId,
    apiName: apiName ?? api.apiName,
    displayName: displayName ?? api.displayName,
    emptyValue: emptyValue !== undefined ? !!emptyValue : api.emptyValue,
    defaultValue: emptyValue ? null : (defaultValue ?? api.defaultValue),
    webhookUrl: webhookUrl !== undefined ? webhookUrl || null : api.webhookUrl,
    visibility: visibility ?? api.visibility,
    whitelistIps:
      visibility === "Private" && whitelistIps
        ? String(whitelistIps).split(",").map((ip: string) => ip.trim()).filter(Boolean)
        : visibility === "Public"
        ? []
        : api.whitelistIps,
    rateLimit: rateLimit !== undefined ? (rateLimit ? parseInt(String(rateLimit)) : null) : api.rateLimit,
    allowDuplicate: allowDuplicate !== undefined ? !!allowDuplicate : api.allowDuplicate,
    encodeEnabled: encodeEnabled !== undefined ? !!encodeEnabled : api.encodeEnabled,
    encodeMethod: encodeEnabled ? encodeMethod ?? api.encodeMethod : null,
    encodePrefix: encodeEnabled && encodeMethod === "Custom" ? encodePrefix ?? null : null,
    encodeMap: encodeEnabled && encodeMethod === "Custom" ? encodeMap ?? null : null,
    encodeKey: encodeEnabled ? encodeKey ?? api.encodeKey : null,
  };
  await writeJson("apis.json", apis);
  return res.json({ success: true });
});

router.delete("/apis/:id", requireAuth, async (req: Request, res: Response) => {
  const apis = await readJson<ApiDef[]>("apis.json");
  const idx = apis.findIndex((a) => a.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "API not found" });
  const s = sess(req);
  if (apis[idx].ownerId !== s.userId && !s.isAdmin)
    return res.status(403).json({ error: "Forbidden" });
  apis.splice(idx, 1);
  await writeJson("apis.json", apis);
  return res.json({ success: true });
});

router.post("/apis/:id/reset", requireAuth, async (req: Request, res: Response) => {
  const apis = await readJson<ApiDef[]>("apis.json");
  const idx = apis.findIndex((a) => a.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "API not found" });
  const s = sess(req);
  if (apis[idx].ownerId !== s.userId && !s.isAdmin)
    return res.status(403).json({ error: "Forbidden" });
  apis[idx].data = [];
  await writeJson("apis.json", apis);
  return res.json({ success: true });
});

export default router;
