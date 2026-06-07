import { Router } from "express";
import bcrypt from "bcryptjs";
import { randomBytes } from "node:crypto";
import { readJson, writeJson } from "../lib/storage";
import { sess } from "../lib/session";

interface User {
  id: string;
  username: string;
  password: string;
  isAdmin: boolean;
  createdAt: string;
}

const router = Router();

router.post("/login", async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password)
    return res.status(400).json({ error: "Username and password required" });
  const users = await readJson<User[]>("users.json");
  const user = users.find((u) => u.username === username);
  if (!user || !(await bcrypt.compare(password, user.password)))
    return res.status(401).json({ error: "Invalid credentials" });
  const s = sess(req);
  s.userId = user.id;
  s.username = user.username;
  s.isAdmin = user.isAdmin;
  return res.json({ success: true, user: { id: user.id, username: user.username, isAdmin: user.isAdmin } });
});

router.post("/register", async (req, res) => {
  const { username, password } = req.body;
  if (!username || !password)
    return res.status(400).json({ error: "Username and password required" });
  const users = await readJson<User[]>("users.json");
  if (users.find((u) => u.username === username))
    return res.status(409).json({ error: "Username already taken" });
  const hashed = await bcrypt.hash(password, 10);
  const isAdmin = users.length === 0;
  const newUser: User = {
    id: randomBytes(8).toString("hex"),
    username,
    password: hashed,
    isAdmin,
    createdAt: new Date().toISOString(),
  };
  users.push(newUser);
  await writeJson("users.json", users);
  const s = sess(req);
  s.userId = newUser.id;
  s.username = newUser.username;
  s.isAdmin = newUser.isAdmin;
  return res.json({ success: true, user: { id: newUser.id, username: newUser.username, isAdmin: newUser.isAdmin } });
});

router.get("/me", (req, res) => {
  const s = sess(req);
  if (!s.userId) return res.json({ loggedIn: false });
  return res.json({ loggedIn: true, user: { id: s.userId, username: s.username, isAdmin: s.isAdmin } });
});

router.post("/logout", (req, res) => {
  req.session.destroy(() => {});
  return res.json({ success: true });
});

export default router;
