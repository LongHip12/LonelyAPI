export async function sendDiscordWebhook(
  webhookUrl: string,
  displayName: string,
  ip: string,
  headers: Record<string, string | string[] | undefined>
): Promise<void> {
  const skip = new Set(["host", "connection", "content-length", "transfer-encoding"]);
  const headerLines = Object.entries(headers)
    .filter(([k]) => !skip.has(k.toLowerCase()))
    .map(([k, v]) => `- **${k}**: ${Array.isArray(v) ? v.join(", ") : (v ?? "")}`)
    .join("\n");
  const content = `**${displayName} API Webhook**\nPost By: ${ip || "N/A"}\n${headerLines}`;
  await fetch(webhookUrl, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}
