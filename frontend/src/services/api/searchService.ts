export async function fetchWithRetry(url: string, options: RequestInit = {}, retries = 2, backoffMs = 500): Promise<Response> {
  try {
    const res = await fetch(url, options);
    if (!res.ok && retries > 0) {
      await new Promise(r => setTimeout(r, backoffMs));
      return fetchWithRetry(url, options, retries - 1, backoffMs * 2);
    }
    return res;
  } catch (e) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, backoffMs));
      return fetchWithRetry(url, options, retries - 1, backoffMs * 2);
    }
    throw e;
  }
}

// Cache for popular data
const cache = new Map<string, { data: any; timestamp: number; ttl: number }>();

// Cache TTL in milliseconds (5 minutes)
const CACHE_TTL = 5 * 60 * 1000;

function getCachedData(key: string): any | null {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < cached.ttl) {
    return cached.data;
  }
  if (cached) {
    cache.delete(key);
  }
  return null;
}

function setCachedData(key: string, data: any, ttl: number = CACHE_TTL): void {
  cache.set(key, { data, timestamp: Date.now(), ttl });
}

// Popular data pre-fetching functions
export async function getPopularJobs(): Promise<string[]> {
  const cacheKey = 'popular_jobs';
  const cached = getCachedData(cacheKey);
  if (cached) return cached;

  try {
    const response = await fetchWithRetry('/api/v1/search/popular/jobs');
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  } catch (error) {
    console.warn('Failed to fetch popular jobs:', error);
    return [];
  }
}

export async function getPopularSkills(): Promise<string[]> {
  const cacheKey = 'popular_skills';
  const cached = getCachedData(cacheKey);
  if (cached) return cached;

  try {
    const response = await fetchWithRetry('/api/v1/search/popular/skills');
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  } catch (error) {
    console.warn('Failed to fetch popular skills:', error);
    return [];
  }
}

export async function getPopularIndustries(): Promise<string[]> {
  const cacheKey = 'popular_industries';
  const cached = getCachedData(cacheKey);
  if (cached) return cached;

  try {
    const response = await fetchWithRetry('/api/v1/search/popular/industries');
    const data = await response.json();
    setCachedData(cacheKey, data);
    return data;
  } catch (error) {
    console.warn('Failed to fetch popular industries:', error);
    return [];
  }
}

// Pre-fetch popular data on app initialization
export function preloadPopularData(): void {
  // Pre-fetch in background
  Promise.all([
    getPopularJobs(),
    getPopularSkills(),
    getPopularIndustries()
  ]).catch(error => {
    console.warn('Failed to preload popular data:', error);
  });
}

// Clear cache (useful for testing or manual refresh)
export function clearCache(): void {
  cache.clear();
}
