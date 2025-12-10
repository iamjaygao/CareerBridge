import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface Message {
  id: number;
  sender: number;
  content: string;
  timestamp: string;
  read: boolean;
}

interface ChatRoom {
  id: number;
  participants: number[];
  lastMessage?: Message;
  unreadCount: number;
}

interface ChatState {
  rooms: ChatRoom[];
  currentRoom: ChatRoom | null;
  messages: Message[];
  loading: boolean;
  error: string | null;
}

const initialState: ChatState = {
  rooms: [],
  currentRoom: null,
  messages: [],
  loading: false,
  error: null,
};

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setRooms: (state, action: PayloadAction<ChatRoom[]>) => {
      state.rooms = action.payload;
    },
    setCurrentRoom: (state, action: PayloadAction<ChatRoom | null>) => {
      state.currentRoom = action.payload;
    },
    addMessage: (state, action: PayloadAction<Message>) => {
      state.messages.push(action.payload);
    },
    setMessages: (state, action: PayloadAction<Message[]>) => {
      state.messages = action.payload;
    },
    markAsRead: (state, action: PayloadAction<number>) => {
      const message = state.messages.find((m) => m.id === action.payload);
      if (message) {
        message.read = true;
      }
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setRooms,
  setCurrentRoom,
  addMessage,
  setMessages,
  markAsRead,
  clearError,
} = chatSlice.actions;

export default chatSlice.reducer;

