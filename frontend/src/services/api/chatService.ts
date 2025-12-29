import apiClient from './client';
import { io, Socket } from 'socket.io-client';

export interface Message {
  id: number;
  chat_room?: number;
  sender: number;
  sender_name?: string;
  sender_avatar?: string;
  message_type?: string;
  content: string;
  timestamp?: string;
  created_at?: string;
  read?: boolean;
  is_read?: boolean;
}

export interface ChatRoom {
  id: number;
  participants: number[];
  lastMessage?: Message;
  last_message?: Message; // Alias
  unreadCount: number;
  unread_count?: number; // Alias
  mentor_name?: string;
  created_at?: string;
}

export interface ChatParticipant {
  id: number;
  username: string;
  avatar?: string;
}

class ChatService {
  private socket: Socket | null = null;

  /**
   * Initialize WebSocket connection
   */
  connect(): Socket {
    if (!this.socket) {
      const token = localStorage.getItem('access_token');
      // Extract base URL without /api/v1 for socket.io
      const baseURL = apiClient.defaults.baseURL?.replace('/api/v1', '') || 'http://localhost:8001';
      this.socket = io(baseURL, {
        auth: {
          token: token,
        },
        transports: ['websocket'],
      });
    }
    return this.socket;
  }

  /**
   * Disconnect WebSocket
   */
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * Get all chat rooms for the current user
   */
  async getChatRooms(): Promise<ChatRoom[]> {
    try {
      const response = await apiClient.get('/chat/rooms/');
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to get chat rooms:', error);
      throw error;
    }
  }

  /**
   * Get a single chat room by ID
   */
  async getChatRoom(roomId: number): Promise<ChatRoom> {
    try {
      const response = await apiClient.get(`/chat/rooms/${roomId}/`);
      return response.data;
    } catch (error) {
      console.error('Failed to get chat room:', error);
      throw error;
    }
  }

  /**
   * Get messages for a chat room
   */
  async getMessages(roomId: number): Promise<Message[]> {
    try {
      const response = await apiClient.get(`/chat/rooms/${roomId}/messages/`);
      return response.data.results || response.data;
    } catch (error) {
      console.error('Failed to get messages:', error);
      throw error;
    }
  }

  /**
   * Send a message
   */
  async sendMessage(roomId: number, content: string): Promise<Message> {
    try {
      const response = await apiClient.post(`/chat/rooms/${roomId}/messages/`, {
        content,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to send message:', error);
      throw error;
    }
  }

  /**
   * Create or get a chat room with a user
   */
  async getOrCreateRoom(userId: number): Promise<ChatRoom> {
    try {
      const response = await apiClient.post('/chat/rooms/', {
        mentor_id: userId,
      });
      return response.data;
    } catch (error) {
      console.error('Failed to get or create room:', error);
      throw error;
    }
  }

  /**
   * Mark messages as read
   */
  async markAsRead(roomId: number, messageIds: number[]): Promise<void> {
    try {
      await apiClient.post(`/chat/rooms/${roomId}/mark-read/`, {
        message_ids: messageIds,
      });
    } catch (error) {
      console.error('Failed to mark messages as read:', error);
      throw error;
    }
  }

  /**
   * Subscribe to new messages in a room
   */
  onMessage(roomId: number, callback: (message: Message) => void): void {
    if (this.socket) {
      this.socket.on(`room_${roomId}_message`, callback);
    }
  }

  /**
   * Unsubscribe from messages
   */
  offMessage(roomId: number, callback?: (message: Message) => void): void {
    if (this.socket) {
      if (callback) {
        this.socket.off(`room_${roomId}_message`, callback);
      } else {
        this.socket.off(`room_${roomId}_message`);
      }
    }
  }
}

const chatService = new ChatService();
export default chatService;
