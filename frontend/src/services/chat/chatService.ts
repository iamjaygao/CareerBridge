import { io, Socket } from 'socket.io-client';
import { ChatMessage, ChatParticipant } from '../../components/chat/ChatWindow';

export interface ChatRoom {
  id: string;
  name: string;
  participants: ChatParticipant[];
  lastMessage?: ChatMessage;
  unreadCount: number;
}

export interface TypingIndicator {
  userId: number;
  userName: string;
  isTyping: boolean;
}

class ChatService {
  private socket: Socket | null = null;
  private baseURL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;

  // Event handlers
  private messageHandlers: ((message: ChatMessage) => void)[] = [];
  private typingHandlers: ((typing: TypingIndicator) => void)[] = [];
  private onlineStatusHandlers: ((userId: number, isOnline: boolean) => void)[] = [];
  private roomUpdateHandlers: ((room: ChatRoom) => void)[] = [];

  // Initialize WebSocket connection
  connect(userId: number, token: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.socket = io(this.baseURL, {
          auth: {
            token,
          },
          transports: ['websocket', 'polling'],
          reconnection: true,
          reconnectionAttempts: this.maxReconnectAttempts,
          reconnectionDelay: this.reconnectDelay,
        });

        this.setupEventListeners();
        this.setupReconnectionHandling();

        this.socket.on('connect', () => {
          console.log('Connected to chat server');
          this.reconnectAttempts = 0;
          resolve();
        });

        this.socket.on('connect_error', (error) => {
          console.error('Connection error:', error);
          reject(error);
        });

        this.socket.on('disconnect', (reason) => {
          console.log('Disconnected from chat server:', reason);
        });

      } catch (error) {
        console.error('Failed to connect to chat server:', error);
        reject(error);
      }
    });
  }

  private setupEventListeners() {
    if (!this.socket) return;

    // Message events
    this.socket.on('message', (message: ChatMessage) => {
      this.messageHandlers.forEach(handler => handler(message));
    });

    this.socket.on('message_sent', (message: ChatMessage) => {
      this.messageHandlers.forEach(handler => handler(message));
    });

    // Typing events
    this.socket.on('typing_start', (typing: TypingIndicator) => {
      this.typingHandlers.forEach(handler => handler(typing));
    });

    this.socket.on('typing_stop', (typing: TypingIndicator) => {
      this.typingHandlers.forEach(handler => handler({ ...typing, isTyping: false }));
    });

    // Online status events
    this.socket.on('user_online', (userId: number) => {
      this.onlineStatusHandlers.forEach(handler => handler(userId, true));
    });

    this.socket.on('user_offline', (userId: number) => {
      this.onlineStatusHandlers.forEach(handler => handler(userId, false));
    });

    // Room events
    this.socket.on('room_update', (room: ChatRoom) => {
      this.roomUpdateHandlers.forEach(handler => handler(room));
    });

    // Error events
    this.socket.on('error', (error: any) => {
      console.error('Chat server error:', error);
    });
  }

  private setupReconnectionHandling() {
    if (!this.socket) return;

    this.socket.on('reconnect_attempt', (attemptNumber: number) => {
      this.reconnectAttempts = attemptNumber;
      console.log(`Reconnection attempt ${attemptNumber}`);
    });

    this.socket.on('reconnect', (attemptNumber: number) => {
      console.log(`Reconnected after ${attemptNumber} attempts`);
      this.reconnectAttempts = 0;
    });

    this.socket.on('reconnect_failed', () => {
      console.error('Failed to reconnect to chat server');
    });
  }

  // Join a chat room
  joinRoom(roomId: string): void {
    if (this.socket) {
      this.socket.emit('join_room', { room_id: roomId });
    }
  }

  // Leave a chat room
  leaveRoom(roomId: string): void {
    if (this.socket) {
      this.socket.emit('leave_room', { room_id: roomId });
    }
  }

  // Send a message
  sendMessage(roomId: string, content: string, type: 'text' | 'file' = 'text'): void {
    if (this.socket) {
      this.socket.emit('send_message', {
        room_id: roomId,
        content,
        type,
        timestamp: new Date().toISOString(),
      });
    }
  }

  // Send typing indicator
  sendTypingIndicator(roomId: string, isTyping: boolean): void {
    if (this.socket) {
      this.socket.emit('typing', {
        room_id: roomId,
        is_typing: isTyping,
      });
    }
  }

  // Upload file and send as message
  async uploadFileAndSend(roomId: string, file: File): Promise<void> {
    try {
      // First upload the file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('room_id', roomId);

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/chat/upload-file/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload file');
      }

      const { file_url, file_name } = await response.json();

      // Send file message
      this.sendMessage(roomId, file_url, 'file');
    } catch (error) {
      console.error('File upload failed:', error);
      throw error;
    }
  }

  // Mark message as read
  markMessageAsRead(messageId: string): void {
    if (this.socket) {
      this.socket.emit('mark_read', { message_id: messageId });
    }
  }

  // Get chat history
  async getChatHistory(roomId: string, limit: number = 50, offset: number = 0): Promise<ChatMessage[]> {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/chat/history/${roomId}/?limit=${limit}&offset=${offset}`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch chat history');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching chat history:', error);
      throw error;
    }
  }

  // Get user's chat rooms
  async getChatRooms(): Promise<ChatRoom[]> {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/chat/rooms/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to fetch chat rooms');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching chat rooms:', error);
      throw error;
    }
  }

  // Create a new chat room
  async createChatRoom(participantIds: number[], name?: string): Promise<ChatRoom> {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/chat/rooms/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
          },
          body: JSON.stringify({
            participant_ids: participantIds,
            name,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to create chat room');
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating chat room:', error);
      throw error;
    }
  }

  // Event handlers registration
  onMessage(handler: (message: ChatMessage) => void): void {
    this.messageHandlers.push(handler);
  }

  onTyping(handler: (typing: TypingIndicator) => void): void {
    this.typingHandlers.push(handler);
  }

  onOnlineStatus(handler: (userId: number, isOnline: boolean) => void): void {
    this.onlineStatusHandlers.push(handler);
  }

  onRoomUpdate(handler: (room: ChatRoom) => void): void {
    this.roomUpdateHandlers.push(handler);
  }

  // Remove event handlers
  offMessage(handler: (message: ChatMessage) => void): void {
    this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
  }

  offTyping(handler: (typing: TypingIndicator) => void): void {
    this.typingHandlers = this.typingHandlers.filter(h => h !== handler);
  }

  offOnlineStatus(handler: (userId: number, isOnline: boolean) => void): void {
    this.onlineStatusHandlers = this.onlineStatusHandlers.filter(h => h !== handler);
  }

  offRoomUpdate(handler: (room: ChatRoom) => void): void {
    this.roomUpdateHandlers = this.roomUpdateHandlers.filter(h => h !== handler);
  }

  // Disconnect from chat server
  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  // Check connection status
  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

export default new ChatService(); 