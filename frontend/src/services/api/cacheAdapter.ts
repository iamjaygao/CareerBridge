interface CacheItem<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

class CacheAdapter {
  private storage: Storage;
  private prefix: string;
  private defaultMaxAge: number;

  constructor(
    storage: Storage = localStorage,
    prefix: string = 'api_cache_',
    defaultMaxAge: number = 15 * 60 * 1000 // 15 minutes
  ) {
    this.storage = storage;
    this.prefix = prefix;
    this.defaultMaxAge = defaultMaxAge;
  }

  private getKey(key: string): string {
    return `${this.prefix}${key}`;
  }

  set<T>(key: string, data: T, maxAge?: number): void {
    const timestamp = Date.now();
    const expiresAt = timestamp + (maxAge || this.defaultMaxAge);
    const item: CacheItem<T> = { data, timestamp, expiresAt };
    this.storage.setItem(this.getKey(key), JSON.stringify(item));
  }

  get<T>(key: string): T | null {
    const item = this.storage.getItem(this.getKey(key));
    if (!item) return null;

    const { data, expiresAt }: CacheItem<T> = JSON.parse(item);
    if (Date.now() > expiresAt) {
      this.remove(key);
      return null;
    }

    return data;
  }

  remove(key: string): void {
    this.storage.removeItem(this.getKey(key));
  }

  clear(): void {
    Object.keys(this.storage).forEach(key => {
      if (key.startsWith(this.prefix)) {
        this.storage.removeItem(key);
      }
    });
  }

  has(key: string): boolean {
    const item = this.get(key);
    return item !== null;
  }
}

export const cacheAdapter = new CacheAdapter();
export default cacheAdapter;