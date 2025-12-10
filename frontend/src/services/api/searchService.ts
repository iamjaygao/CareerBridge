import apiClient from './client';

export interface SearchResult {
  jobs?: any[];
  mentors?: any[];
  resumes?: any[];
}

/**
 * Preload popular data for search suggestions
 */
export const preloadPopularData = async (): Promise<void> => {
  try {
    // Preload popular jobs, skills, industries
    await Promise.all([
      apiClient.get('/search/popular-jobs/').catch(() => null),
      apiClient.get('/search/popular-skills/').catch(() => null),
      apiClient.get('/search/popular-industries/').catch(() => null),
    ]);
  } catch (error) {
    // Silently fail - this is just preloading
    console.debug('Failed to preload popular data:', error);
  }
};

/**
 * Search across all resources
 */
export const searchAll = async (query: string): Promise<SearchResult> => {
  try {
    const response = await apiClient.get('/search/', {
      params: { q: query },
    });
    return response.data;
  } catch (error) {
    console.error('Search failed:', error);
    throw error;
  }
};

/**
 * Get popular jobs
 */
export const getPopularJobs = async (): Promise<string[]> => {
  try {
    const response = await apiClient.get('/search/popular-jobs/');
    return response.data;
  } catch (error) {
    console.error('Failed to get popular jobs:', error);
    return [];
  }
};

/**
 * Get popular skills
 */
export const getPopularSkills = async (): Promise<string[]> => {
  try {
    const response = await apiClient.get('/search/popular-skills/');
    return response.data;
  } catch (error) {
    console.error('Failed to get popular skills:', error);
    return [];
  }
};

/**
 * Get popular industries
 */
export const getPopularIndustries = async (): Promise<string[]> => {
  try {
    const response = await apiClient.get('/search/popular-industries/');
    return response.data;
  } catch (error) {
    console.error('Failed to get popular industries:', error);
    return [];
  }
};

/**
 * Fetch with retry logic
 */
export const fetchWithRetry = async (
  url: string,
  options: RequestInit = {},
  maxRetries: number = 3
): Promise<Response> => {
  let lastError: Error | null = null;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) {
        return response;
      }
      lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);
    } catch (error) {
      lastError = error as Error;
    }
    
    if (i < maxRetries - 1) {
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
  
  throw lastError || new Error('Fetch failed after retries');
};

export default {
  preloadPopularData,
  searchAll,
  getPopularJobs,
  getPopularSkills,
  getPopularIndustries,
  fetchWithRetry,
};

