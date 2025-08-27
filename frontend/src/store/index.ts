import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import mentorReducer from './slices/mentorSlice';
import appointmentReducer from './slices/appointmentSlice';
import resumeReducer from './slices/resumeSlice';
import notificationReducer from './slices/notificationSlice';
import settingsReducer from './slices/settingsSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    mentors: mentorReducer,
    appointments: appointmentReducer,
    resumes: resumeReducer,
    notifications: notificationReducer,
    settings: settingsReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 