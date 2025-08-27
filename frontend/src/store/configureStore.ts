import { configureStore, Middleware } from '@reduxjs/toolkit';
import { persistStore, persistReducer, FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { createLogger } from 'redux-logger';

import rootReducer from './rootReducer';

// Performance monitoring middleware
const performanceMiddleware: Middleware = () => (next) => (action) => {
  const start = performance.now();
  const result = next(action);
  const end = performance.now();
  const duration = end - start;

  if (duration > 100) { // Log slow actions (>100ms)
    console.warn(`Slow action: ${(action as any).type} took ${duration.toFixed(2)}ms`);
  }

  return result;
};

// Error tracking middleware
const errorMiddleware: Middleware = () => (next) => (action) => {
  try {
    return next(action);
  } catch (err) {
    console.error('Caught an exception in reducer:', err);
    // Here you could send the error to your error tracking service
    throw err;
  }
};

// Redux persist configuration
const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['auth', 'settings'], // Only persist these reducers
  blacklist: ['notifications'], // Don't persist these reducers
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

// Development middleware
const getDevelopmentMiddleware = () => {
  const middleware: Middleware[] = [];

  if (process.env.NODE_ENV === 'development') {
    middleware.push(createLogger({
      collapsed: true,
      duration: true,
      timestamp: false,
      colors: {
        title: () => '#139BFE',
        prevState: () => '#9E9E9E',
        action: () => '#149945',
        nextState: () => '#A47104',
        error: () => '#FF0000',
      },
    }));
  }

  return middleware;
};

const configureAppStore = (preloadedState: any = {}) => {
  const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) => {
      const defaultMiddleware = getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
        thunk: true,
      });

      return defaultMiddleware.concat([
        performanceMiddleware,
        errorMiddleware,
        ...getDevelopmentMiddleware(),
      ]);
    },
    preloadedState,
    devTools: process.env.NODE_ENV !== 'production',
  });

  const persistor = persistStore(store);

  if (process.env.NODE_ENV !== 'production' && (module as any).hot) {
    (module as any).hot.accept('./rootReducer', () => {
      const newRootReducer = require('./rootReducer').default;
      store.replaceReducer(persistReducer(persistConfig, newRootReducer));
    });
  }

  return { store, persistor };
};

export default configureAppStore;