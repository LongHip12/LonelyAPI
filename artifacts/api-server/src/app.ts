import express, { type Express } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import session from "express-session";
import cookieParser from "cookie-parser";
import path from "node:path";
import { existsSync } from "node:fs";
import router from "./routes";
import { logger } from "./lib/logger";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return { id: req.id, method: req.method, url: req.url?.split("?")[0] };
      },
      res(res) {
        return { statusCode: res.statusCode };
      },
    },
  })
);

app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(cookieParser());

app.use(
  session({
    secret: process.env["SESSION_SECRET"] || "lonely-hub-secret-key",
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 7 * 24 * 60 * 60 * 1000, sameSite: "lax" },
  })
);

const publicDir = path.join(process.cwd(), "public");

app.use(express.static(publicDir));

function servePage(page: string) {
  return (_req: express.Request, res: express.Response) => {
    const filePath = path.join(publicDir, `${page}.html`);
    if (existsSync(filePath)) {
      res.sendFile(filePath);
    } else {
      res.status(404).send("Page not found");
    }
  };
}

app.get("/", servePage("index"));
app.get("/auth", servePage("auth"));
app.get("/manager", servePage("manager"));
app.get("/view", servePage("view"));
app.get("/admin", servePage("admin"));
app.get("/manager-user", servePage("manager-user"));
app.get("/error", servePage("error"));

app.use("/api", router);

export default app;
