import apiClient from './client';

export interface ChatRoom {
  id: number;
  user: number;
  mentor: number;
  user_name: string;
  mentor_name: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  last_message?: {
    content: string;
    sender: string;
    created_at: string;
    message_type: string;
  };
  unread_count: number;
}

export interface Message {
  id: number;
  chat_room: number;
  sender: number;
  sender_name: string;
  sender_avatar?: string;
  message_type: string;
  content: string;
  file?: string;
  created_at: string;
  is_read: boolean;
}

export interface ChatParticipant {
  id: number;
  user: number;
  user_name: string;
  user_avatar?: string;
  chat_room: number;
  is_online: boolean;
  last_seen: string;
  joined_at: string;
}

const chatService = {
  // Chat Rooms
  async getChatRooms(): Promise<ChatRoom[]> {
    const response = await apiClient.get<ChatRoom[]>('/chat/rooms/');
    return response.data;
  },

  async createChatRoom(mentorId: number): Promise<ChatRoom> {
    const response = await apiClient.post<ChatRoom>('/chat/rooms/', {
      mentor_id: mentorId,
    });
    return response.data;
  },

  async getChatRoom(roomId: number): Promise<ChatRoom> {
    const response = await apiClient.get<ChatRoom>(`/chat/rooms/${roomId}/`);
    return response.data;
  },

  async markMessagesRead(roomId: number): Promise<void> {
    await apiClient.post(`/chat/rooms/${roomId}/mark_messages_read/`);
  },

  async getParticipants(roomId: number): Promise<ChatParticipant[]> {
    const response = await apiClient.get<ChatParticipant[]>(`/chat/rooms/${roomId}/participants/`);
    return response.data;
  },

  // Messages
  async getMessages(roomId: number): Promise<Message[]> {
    const response = await apiClient.get<Message[]>(`/chat/messages/?chat_room=${roomId}`);
    return response.data;
  },

  async sendMessage(roomId: number, content: string, messageType: string = 'text'): Promise<Message> {
    const response = await apiClient.post<Message>('/chat/messages/', {
      chat_room: roomId,
      content,
      message_type: messageType,
    });
    return response.data;
  },

  async markMessageRead(messageId: number): Promise<void> {
    await apiClient.post(`/chat/messages/${messageId}/mark_read/`);
  },

  async getUnreadCount(): Promise<{ unread_count: number }> {
    const response = await apiClient.get<{ unread_count: number }>('/chat/messages/unread_count/');
    return response.data;
  },
};

export default chatService; 