export interface SearchSuggestion {
  id: string;
  text: string;
  type: 'mentor' | 'skill' | 'industry' | 'job_title' | 'company';
  relevance: number;
  metadata?: Record<string, any>;
}

export interface SearchResult {
  id: string;
  title: string;
  description: string;
  type: string;
  url: string;
  relevance: number;
  metadata?: Record<string, any>;
}

export interface SearchFilters {
  type?: string[];
  industry?: string[];
  skills?: string[];
  location?: string[];
  experience_level?: string[];
  price_range?: [number, number];
  rating?: number;
  availability?: string[];
}

export interface SearchQuery {
  query: string;
  filters?: SearchFilters;
  sort?: 'relevance' | 'rating' | 'price' | 'experience' | 'date';
  order?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

import { fetchWithRetry } from '../api/searchService';

class SearchService {
  private baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
  private searchCache = new Map<string, SearchSuggestion[]>();
  private cacheExpiry = 5 * 60 * 1000; // 5 minutes

  // Get search suggestions based on partial query
  async getSearchSuggestions(query: string, limit: number = 10): Promise<SearchSuggestion[]> {
    if (!query.trim()) return [];

    const cacheKey = `suggestions_${query.toLowerCase()}`;
    const cached = this.searchCache.get(cacheKey);
    
    if (cached && Date.now() - (cached as any).timestamp < this.cacheExpiry) {
      return (cached as any).data;
    }

    try {
      const response = await fetchWithRetry(
        `${this.baseURL}/search/suggestions/?q=${encodeURIComponent(query)}&limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get search suggestions');
      }

      const suggestions = await response.json();
      
      // Cache the results
      this.searchCache.set(cacheKey, {
        data: suggestions,
        timestamp: Date.now(),
      } as any);

      return suggestions;
    } catch (error) {
      console.error('Error getting search suggestions:', error);
      return [];
    }
  }

  // Get trending searches
  async getTrendingSearches(limit: number = 10): Promise<SearchSuggestion[]> {
    try {
      const response = await fetchWithRetry(
        `${this.baseURL}/search/trending/?limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get trending searches');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting trending searches:', error);
      return [];
    }
  }

  // Get popular skills
  async getPopularSkills(limit: number = 20): Promise<SearchSuggestion[]> {
    try {
      const response = await fetchWithRetry(
        `${this.baseURL}/search/popular-skills/?limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get popular skills');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting popular skills:', error);
      return [];
    }
  }

  // Get popular industries
  async getPopularIndustries(limit: number = 15): Promise<SearchSuggestion[]> {
    try {
      const response = await fetchWithRetry(
        `${this.baseURL}/search/popular-industries/?limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get popular industries');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting popular industries:', error);
      return [];
    }
  }

  // Perform search
  async search(searchQuery: SearchQuery): Promise<{
    results: SearchResult[];
    total: number;
    page: number;
    totalPages: number;
    facets: Record<string, any>;
  }> {
    try {
      const params = new URLSearchParams({
        q: searchQuery.query,
        page: (searchQuery.page || 1).toString(),
        limit: (searchQuery.limit || 20).toString(),
      });

      if (searchQuery.sort) {
        params.append('sort', searchQuery.sort);
      }

      if (searchQuery.order) {
        params.append('order', searchQuery.order);
      }

      if (searchQuery.filters) {
        Object.entries(searchQuery.filters).forEach(([key, value]) => {
          if (Array.isArray(value)) {
            value.forEach(v => params.append(key, v));
          } else if (value !== undefined) {
            params.append(key, value.toString());
          }
        });
      }

      const response = await fetchWithRetry(`${this.baseURL}/search/?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Search error:', error);
      throw error;
    }
  }

  // Get search filters/options
  async getSearchFilters(): Promise<{
    types: { value: string; label: string; count: number }[];
    industries: { value: string; label: string; count: number }[];
    skills: { value: string; label: string; count: number }[];
    locations: { value: string; label: string; count: number }[];
    experience_levels: { value: string; label: string; count: number }[];
    price_ranges: { value: string; label: string; count: number }[];
    availability: { value: string; label: string; count: number }[];
  }> {
    try {
      const response = await fetch(`${this.baseURL}/search/filters/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get search filters');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting search filters:', error);
      throw error;
    }
  }

  // Save search query to user's search history
  async saveSearchQuery(query: string, filters?: SearchFilters): Promise<void> {
    try {
      await fetch(`${this.baseURL}/search/history/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify({
          query,
          filters,
          timestamp: new Date().toISOString(),
        }),
      });
    } catch (error) {
      console.error('Error saving search query:', error);
      // Don't throw error as this is not critical
    }
  }

  // Get user's search history
  async getSearchHistory(limit: number = 20): Promise<{
    query: string;
    filters?: SearchFilters;
    timestamp: string;
    result_count: number;
  }[]> {
    try {
      const response = await fetch(
        `${this.baseURL}/search/history/?limit=${limit}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to get search history');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting search history:', error);
      return [];
    }
  }

  // Clear search history
  async clearSearchHistory(): Promise<void> {
    try {
      await fetch(`${this.baseURL}/search/history/`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
    } catch (error) {
      console.error('Error clearing search history:', error);
      throw error;
    }
  }

  // Get search analytics
  async getSearchAnalytics(): Promise<{
    total_searches: number;
    popular_queries: { query: string; count: number }[];
    search_trends: { date: string; count: number }[];
    no_results_queries: { query: string; count: number }[];
  }> {
    try {
      const response = await fetch(`${this.baseURL}/search/analytics/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get search analytics');
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting search analytics:', error);
      throw error;
    }
  }

  // Utility methods
  debounce<T extends (...args: any[]) => any>(
    func: T,
    wait: number
  ): (...args: Parameters<T>) => void {
    let timeout: NodeJS.Timeout;
    return (...args: Parameters<T>) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func(...args), wait);
    };
  }

  highlightQuery(text: string, query: string): string {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  }

  // Clear search cache
  clearCache(): void {
    this.searchCache.clear();
  }

  // Get cache statistics
  getCacheStats(): { size: number; keys: string[] } {
    return {
      size: this.searchCache.size,
      keys: Array.from(this.searchCache.keys()),
    };
  }
}

export default new SearchService(); 