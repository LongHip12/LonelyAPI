import { Router, Request, Response } from "express";
import { readJson, writeJson } from "../lib/storage";
import { sess, requireAdmin } from "../lib/session";

interface User {
  id: string;
  username: string;
  password: string;
  isAdmin: boolean;
  createdAt: string;
}

const router = Router();

router.get("/users", requireAdmin, async (req: Request, res: Response) => {
  const page = Math.max(1, parseInt(String(req.query.page ?? "1")));
  const users = await readJson<User[]>("users.json");
  const total = users.length;
  const pageSize = 15;
  const paged = users
    .slice((page - 1) * pageSize, page * pageSize)
    .map((u) => ({ id: u.id, username: u.username, isAdmin: u.isAdmin, createdAt: u.createdAt }));
  return res.json({ users: paged, total, page, pages: Math.ceil(total / pageSize) || 1 });
});

router.put("/users/:id/permission", requireAdmin, async (req: Request, res: Response) => {
  const users = await readJson<User[]>("users.json");
  const idx = users.findIndex((u) => u.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "User not found" });
  users[idx].isAdmin = !users[idx].isAdmin;
  await writeJson("users.json", users);
  return res.json({ success: true, isAdmin: users[idx].isAdmin });
});

router.delete("/users/:id", requireAdmin, async (req: Request, res: Response) => {
  const users = await readJson<User[]>("users.json");
  const idx = users.findIndex((u) => u.id === req.params.id);
  if (idx === -1) return res.status(404).json({ error: "User not found" });
  if (users[idx].id === sess(req).userId)
    return res.status(400).json({ error: "Cannot delete yourself" });
  users.splice(idx, 1);
  await writeJson("users.json", users);
  return res.json({ success: true });
});

export default router;
