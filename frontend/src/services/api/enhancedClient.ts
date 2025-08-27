import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import cacheAdapter from './cacheAdapter';

interface RequestCache {
  [key: string]: Promise<any>;
}

interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition: (error: any) => boolean;
}

class EnhancedApiClient {
  private client: AxiosInstance;
  private pendingRequests: RequestCache = {};
  private retryConfig: RetryConfig = {
    retries: 3,
    retryDelay: 1000,
    retryCondition: (error) => {
      return error.response?.status >= 500 || !error.response;
    },
  };

  constructor(baseURL: string = process.env.REACT_APP_API_URL || '/api/v1') {
    this.client = axios.create({
      baseURL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            const refreshToken = localStorage.getItem('refresh_token');
            if (refreshToken) {
              const response = await axios.post(`${this.client.defaults.baseURL}/users/refresh/`, {
                refresh: refreshToken,
              });
              
              const { access } = response.data;
              localStorage.setItem('access_token', access);
              
              originalRequest.headers.Authorization = `Bearer ${access}`;
              return this.client(originalRequest);
            }
          } catch (refreshError) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
          }
        }

        return Promise.reject(error);
      }
    );
  }

  private generateCacheKey(config: AxiosRequestConfig): string {
    const { method, url, params, data } = config;
    return `${method}_${url}_${JSON.stringify(params)}_${JSON.stringify(data)}`;
  }

  private async retryRequest<T>(
    requestFn: () => Promise<T>,
    retries: number = this.retryConfig.retries
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error) {
      if (retries > 0 && this.retryConfig.retryCondition(error)) {
        await new Promise(resolve => setTimeout(resolve, this.retryConfig.retryDelay));
        return this.retryRequest(requestFn, retries - 1);
      }
      throw error;
    }
  }

  private deduplicateRequest<T>(
    cacheKey: string,
    requestFn: () => Promise<T>
  ): Promise<T> {
    const existingRequest = this.pendingRequests[cacheKey];
    if (existingRequest) {
      return existingRequest;
    }

    const promise = requestFn().finally(() => {
      delete this.pendingRequests[cacheKey];
    });

    this.pendingRequests[cacheKey] = promise;
    return promise;
  }

  async get<T>(
    url: string,
    config?: AxiosRequestConfig & { cache?: boolean; cacheTime?: number }
  ): Promise<T> {
    const cacheKey = this.generateCacheKey({ method: 'GET', url, ...config });
    
    // Check cache first
    if (config?.cache !== false) {
      const cachedData = cacheAdapter.get<T>(cacheKey);
      if (cachedData) {
        return cachedData;
      }
    }

    const requestFn = () => this.client.get<T>(url, config);
    
    return this.deduplicateRequest(cacheKey, async () => {
      const response = await this.retryRequest(requestFn);
      
      // Cache successful responses
      if (config?.cache !== false) {
        cacheAdapter.set(cacheKey, response.data, config?.cacheTime);
      }
      
      return response.data;
    });
  }

  async post<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const requestFn = () => this.client.post<T>(url, data, config);
    const response = await this.retryRequest(requestFn);
    return response.data;
  }

  async put<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const requestFn = () => this.client.put<T>(url, data, config);
    const response = await this.retryRequest(requestFn);
    return response.data;
  }

  async patch<T>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const requestFn = () => this.client.patch<T>(url, data, config);
    const response = await this.retryRequest(requestFn);
    return response.data;
  }

  async delete<T>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<T> {
    const requestFn = () => this.client.delete<T>(url, config);
    const response = await this.retryRequest(requestFn);
    return response.data;
  }

  async upload<T>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void
  ): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    const requestFn = () => this.client.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    const response = await this.retryRequest(requestFn);
    return response.data;
  }

  // Utility methods
  clearCache(pattern?: string): void {
    if (pattern) {
      // Clear specific cache entries
      Object.keys(localStorage).forEach(key => {
        if (key.includes(pattern)) {
          localStorage.removeItem(key);
        }
      });
    } else {
      cacheAdapter.clear();
    }
  }

  setRetryConfig(config: Partial<RetryConfig>): void {
    this.retryConfig = { ...this.retryConfig, ...config };
  }

  getPendingRequestsCount(): number {
    return Object.keys(this.pendingRequests).length;
  }
}

const enhancedClient = new EnhancedApiClient();
export default enhancedClient;