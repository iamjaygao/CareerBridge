import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  CircularProgress,
  Chip,
  Badge,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachFileIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { useAuth } from '../../contexts/AuthContext';
import chatService, { Message } from '../../services/api/chatService';

interface ChatWindowProps {
  chatRoomId: number;
  onClose?: () => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ chatRoomId, onClose }) => {
  const { user } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState<string[]>([]);

  useEffect(() => {
    loadMessages();
    connectWebSocket();
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, [chatRoomId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadMessages = async () => {
    try {
      setLoading(true);
      const response = await chatService.getMessages(chatRoomId);
      setMessages(response);
    } catch (error) {
      console.error('Failed to load messages:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    const wsProto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProto}//${window.location.host}/ws/chat/${chatRoomId}/`;
    const websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
      console.log('WebSocket connected');
    };

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'chat_message') {
        const newMsg: Message = {
          id: data.message_id,
          chat_room: chatRoomId,
          sender: data.sender_id,
          sender_name: data.sender_name,
          sender_avatar: undefined,
          message_type: 'text',
          content: data.message,
          created_at: data.timestamp,
          is_read: false,
        };
        setMessages(prev => [...prev, newMsg]);
      } else if (data.type === 'user_typing') {
        if (data.is_typing) {
          setTypingUsers(prev => {
            const newSet = new Set(prev);
            newSet.add(data.user_id);
            return Array.from(newSet);
          });
        } else {
          setTypingUsers(prev => prev.filter(id => id !== data.user_id));
        }
      }
    };

    websocket.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket disconnected');
    };

    setWs(websocket);
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !ws) return;

    try {
      const messageData = {
        type: 'chat_message',
        message: newMessage,
        sender_id: user?.id,
      };

      ws.send(JSON.stringify(messageData));
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleTyping = (e: React.ChangeEvent<HTMLInputElement>) => {
    setNewMessage(e.target.value);
    
    if (!ws) return;

    if (!isTyping) {
      setIsTyping(true);
      ws.send(JSON.stringify({
        type: 'typing',
        user_id: user?.id,
        is_typing: true,
      }));
    }

    // Clear typing indicator after 2 seconds
    setTimeout(() => {
      if (ws) {
        ws.send(JSON.stringify({
          type: 'typing',
          user_id: user?.id,
          is_typing: false,
        }));
        setIsTyping(false);
      }
    }, 2000);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <Paper sx={{ height: '600px', display: 'flex', flexDirection: 'column' }}>
      {/* Chat Header */}
      <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider', display: 'flex', alignItems: 'center' }}>
        <Avatar sx={{ mr: 2 }}>M</Avatar>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h6">Chat Room {chatRoomId}</Typography>
          <Typography variant="body2" color="text.secondary">
            {typingUsers.length > 0 ? 'Typing...' : 'Online'}
          </Typography>
        </Box>
        <IconButton size="small">
          <MoreVertIcon />
        </IconButton>
      </Box>

      {/* Messages Area */}
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 2 }}>
            <CircularProgress />
          </Box>
        ) : (
          <List>
            {messages.map((message) => (
              <ListItem
                key={message.id}
                sx={{
                  flexDirection: 'column',
                  alignItems: message.sender === user?.id ? 'flex-end' : 'flex-start',
                  px: 0,
                }}
              >
                <Box
                  sx={{
                    maxWidth: '70%',
                    backgroundColor: message.sender === user?.id ? 'primary.main' : 'grey.100',
                    color: message.sender === user?.id ? 'white' : 'text.primary',
                    borderRadius: 2,
                    p: 1.5,
                    mb: 0.5,
                  }}
                >
                  <Typography variant="body2">{message.content}</Typography>
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" color="text.secondary">
                    {message.sender_name}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {message.created_at ? formatTime(message.created_at) : ''}
                  </Typography>
                  {message.sender === user?.id && (
                    <Chip
                      label={message.is_read ? 'Read' : 'Sent'}
                      size="small"
                      variant="outlined"
                      color={message.is_read ? 'success' : 'default'}
                    />
                  )}
                </Box>
              </ListItem>
            ))}
            <div ref={messagesEndRef} />
          </List>
        )}
      </Box>

      {/* Message Input */}
      <Box sx={{ p: 2, borderTop: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <IconButton size="small">
            <AttachFileIcon />
          </IconButton>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Type a message..."
            value={newMessage}
            onChange={handleTyping}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
              }
            }}
            size="small"
          />
          <IconButton
            color="primary"
            onClick={sendMessage}
            disabled={!newMessage.trim()}
          >
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Paper>
  );
};

export default ChatWindow; 