export type EncodeMethod = "Base64" | "Base62" | "Base32" | "Hex" | "Binary" | "Unicode Escaped" | "Custom";

const BASE62_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz";
const BASE32_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

function encodeBase62(str: string): string {
  const bytes = Buffer.from(str, "utf-8");
  const hex = bytes.toString("hex");
  if (!hex) return "0";
  let num = BigInt("0x" + hex);
  if (num === 0n) return "0";
  let result = "";
  const base = BigInt(62);
  while (num > 0n) {
    result = BASE62_CHARS[Number(num % base)] + result;
    num = num / base;
  }
  return result;
}

function encodeBase32(str: string): string {
  const bytes = Buffer.from(str, "utf-8");
  let result = "";
  let bits = 0;
  let current = 0;
  for (const byte of bytes) {
    current = (current << 8) | byte;
    bits += 8;
    while (bits >= 5) {
      bits -= 5;
      result += BASE32_CHARS[(current >> bits) & 0x1f];
    }
  }
  if (bits > 0) {
    result += BASE32_CHARS[(current << (5 - bits)) & 0x1f];
  }
  return result;
}

export function encodeValue(
  value: string,
  method: EncodeMethod,
  encodeMap?: Record<string, string>,
  prefix?: string
): string {
  switch (method) {
    case "Base64":
      return Buffer.from(value, "utf-8").toString("base64");
    case "Base62":
      return encodeBase62(value);
    case "Base32":
      return encodeBase32(value);
    case "Hex":
      return Buffer.from(value, "utf-8").toString("hex");
    case "Binary":
      return value
        .split("")
        .map((c) => c.charCodeAt(0).toString(2).padStart(8, "0"))
        .join(" ");
    case "Unicode Escaped":
      return value
        .split("")
        .map((c) => `\\u${c.charCodeAt(0).toString(16).padStart(4, "0")}`)
        .join("");
    case "Custom": {
      if (!encodeMap) return value;
      const encoded = value
        .split("")
        .map((c) => encodeMap[c] ?? c)
        .join("");
      return prefix ? prefix + encoded : encoded;
    }
    default:
      return value;
  }
}

export function applyEncode(
  data: Record<string, unknown>,
  key: string,
  method: EncodeMethod,
  encodeMap?: Record<string, string>,
  prefix?: string
): Record<string, unknown> {
  const result = { ...data };
  if (key in result) {
    result[key] = encodeValue(String(result[key]), method, encodeMap, prefix);
  }
  return result;
}

export type EncodeDataType = Record<
  string,
  { Prefix?: string; [char: string]: string | undefined }
>;

export function applyRandomEncode(
  data: Record<string, unknown>,
  key: string,
  encodeData: EncodeDataType
): Record<string, unknown> {
  const keys = Object.keys(encodeData);
  if (!keys.length) return data;
  const chosen = keys[Math.floor(Math.random() * keys.length)];
  const encodeSet = encodeData[chosen];
  const prefix = encodeSet["Prefix"] ?? "";
  const encodeMap: Record<string, string> = {};
  for (const [k, v] of Object.entries(encodeSet)) {
    if (k !== "Prefix" && v) encodeMap[k] = v;
  }
  return applyEncode(data, key, "Custom", encodeMap, prefix);
}
