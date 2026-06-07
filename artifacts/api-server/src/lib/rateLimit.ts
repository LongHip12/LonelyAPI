const rateLimitMap = new Map<string, { count: number; resetAt: number }>();

export function checkRateLimit(key: string, limitPerMin: number): boolean {
  const now = Date.now();
  const entry = rateLimitMap.get(key);
  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(key, { count: 1, resetAt: now + 60000 });
    return true;
  }
  if (entry.count >= limitPerMin) return false;
  entry.count++;
  return true;
}
