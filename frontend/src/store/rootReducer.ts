import { combineReducers } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import mentorReducer from './slices/mentorSlice';
import appointmentReducer from './slices/appointmentSlice';
import resumeReducer from './slices/resumeSlice';
import settingsReducer from './slices/settingsSlice';
import chatReducer from './slices/chatSlice';
import notificationReducer from './slices/notificationSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  mentors: mentorReducer,
  appointments: appointmentReducer,
  resumes: resumeReducer,
  settings: settingsReducer,
  chat: chatReducer,
  notifications: notificationReducer,
});

export default rootReducer;

