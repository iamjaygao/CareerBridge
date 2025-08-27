import { combineReducers } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import mentorReducer from './slices/mentorSlice';
import appointmentReducer from './slices/appointmentSlice';
import resumeReducer from './slices/resumeSlice';
import notificationReducer from './slices/notificationSlice';
import settingsReducer from './slices/settingsSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  mentors: mentorReducer,
  appointments: appointmentReducer,
  resumes: resumeReducer,
  notifications: notificationReducer,
  settings: settingsReducer,
});

export type RootState = ReturnType<typeof rootReducer>;
export default rootReducer;