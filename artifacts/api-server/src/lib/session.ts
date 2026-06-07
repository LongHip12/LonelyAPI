import { Request, Response, NextFunction } from "express";

export interface AppSession {
  userId?: string;
  username?: string;
  isAdmin?: boolean;
}

export function sess(req: Request): AppSession {
  return req.session as unknown as AppSession;
}

export function requireAuth(req: Request, res: Response, next: NextFunction): void {
  if (!sess(req).userId) { res.status(401).json({ error: "Not logged in" }); return; }
  next();
}

export function requireAdmin(req: Request, res: Response, next: NextFunction): void {
  if (!sess(req).userId) { res.status(401).json({ error: "Not logged in" }); return; }
  if (!sess(req).isAdmin) { res.status(403).json({ error: "Admin required" }); return; }
  next();
}
