import { readFile, writeFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { existsSync } from "node:fs";

const DATA_DIR = path.join(process.cwd(), "data");

async function ensureDataDir(): Promise<void> {
  if (!existsSync(DATA_DIR)) {
    await mkdir(DATA_DIR, { recursive: true });
  }
}

export async function readJson<T>(filename: string): Promise<T> {
  await ensureDataDir();
  const filePath = path.join(DATA_DIR, filename);
  try {
    const content = await readFile(filePath, "utf-8");
    return JSON.parse(content) as T;
  } catch {
    if (filename === "bloxfruit.json") return { servers: {} } as T;
    return [] as T;
  }
}

export async function writeJson<T>(filename: string, data: T): Promise<void> {
  await ensureDataDir();
  const filePath = path.join(DATA_DIR, filename);
  await writeFile(filePath, JSON.stringify(data, null, 2), "utf-8");
}
