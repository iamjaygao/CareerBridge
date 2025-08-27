import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Avatar,
  List,
  ListItem,
  CircularProgress,
  Alert,
  Chip,
} from '@mui/material';
import {
  Send as SendIcon,
  AttachFile as AttachIcon,
  EmojiEmotions as EmojiIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';

export interface ChatMessage {
  id: string;
  senderId: number;
  senderName: string;
  senderAvatar?: string;
  content: string;
  timestamp: Date;
  type: 'text' | 'file' | 'image';
  fileUrl?: string;
  fileName?: string;
  isRead: boolean;
}

export interface ChatParticipant {
  id: number;
  name: string;
  avatar?: string;
  isOnline: boolean;
  lastSeen?: Date;
}

interface ChatWindowProps {
  messages: ChatMessage[];
  participants: ChatParticipant[];
  currentUserId: number;
  onSendMessage: (content: string, type?: 'text' | 'file') => Promise<void>;
  onFileUpload?: (file: File) => Promise<void>;
  loading?: boolean;
  error?: string;
  title?: string;
  onLoadMore?: () => void;
  hasMoreMessages?: boolean;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  participants,
  currentUserId,
  onSendMessage,
  onFileUpload,
  loading = false,
  error,
  title,
  onLoadMore,
  hasMoreMessages = false,
}) => {
  const [newMessage, setNewMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const otherParticipants = participants.filter(p => p.id !== currentUserId);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!newMessage.trim()) return;

    try {
      await onSendMessage(newMessage.trim());
      setNewMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && onFileUpload) {
      try {
        await onFileUpload(file);
      } catch (error) {
        console.error('Failed to upload file:', error);
      }
    }
  };

  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  const formatDate = (date: Date) => {
    const today = new Date();
    const messageDate = new Date(date);
    
    if (messageDate.toDateString() === today.toDateString()) {
      return 'Today';
    }
    
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (messageDate.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    
    return messageDate.toLocaleDateString();
  };

  const renderMessage = (message: ChatMessage, index: number) => {
    const isOwnMessage = message.senderId === currentUserId;
    const showDate = index === 0 || 
      formatDate(message.timestamp) !== formatDate(messages[index - 1].timestamp);

    return (
      <React.Fragment key={message.id}>
        {showDate && (
          <Box sx={{ textAlign: 'center', my: 2 }}>
            <Chip
              label={formatDate(message.timestamp)}
              size="small"
              variant="outlined"
            />
          </Box>
        )}
        
        <ListItem
          sx={{
            flexDirection: 'column',
            alignItems: isOwnMessage ? 'flex-end' : 'flex-start',
            px: 0,
          }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'flex-end',
              gap: 1,
              maxWidth: '70%',
              flexDirection: isOwnMessage ? 'row-reverse' : 'row',
            }}
          >
            {!isOwnMessage && (
              <Avatar
                src={message.senderAvatar}
                sx={{ width: 32, height: 32 }}
              >
                {message.senderName.charAt(0)}
              </Avatar>
            )}
            
            <Box
              sx={{
                bgcolor: isOwnMessage ? 'primary.main' : 'grey.100',
                color: isOwnMessage ? 'white' : 'text.primary',
                borderRadius: 2,
                px: 2,
                py: 1,
                maxWidth: '100%',
                wordBreak: 'break-word',
              }}
            >
              {!isOwnMessage && (
                <Typography variant="caption" sx={{ opacity: 0.7, display: 'block', mb: 0.5 }}>
                  {message.senderName}
                </Typography>
              )}
              
              {message.type === 'text' && (
                <Typography variant="body2">
                  {message.content}
                </Typography>
              )}
              
              {message.type === 'file' && (
                <Box>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    📎 {message.fileName}
                  </Typography>
                  <Typography variant="caption" sx={{ opacity: 0.7 }}>
                    File attachment
                  </Typography>
                </Box>
              )}
              
              <Typography
                variant="caption"
                sx={{
                  opacity: 0.7,
                  display: 'block',
                  mt: 0.5,
                  textAlign: isOwnMessage ? 'right' : 'left',
                }}
              >
                {formatTime(message.timestamp)}
                {isOwnMessage && (
                  <span style={{ marginLeft: 4 }}>
                    {message.isRead ? '✓✓' : '✓'}
                  </span>
                )}
              </Typography>
            </Box>
          </Box>
        </ListItem>
      </React.Fragment>
    );
  };

  return (
    <Paper
      sx={{
        height: '600px',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Chat Header */}
      <Box
        sx={{
          p: 2,
          borderBottom: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'center',
          gap: 2,
        }}
      >
        <Avatar
          src={otherParticipants[0]?.avatar}
          sx={{ width: 40, height: 40 }}
        >
          {otherParticipants[0]?.name.charAt(0)}
        </Avatar>
        
        <Box sx={{ flex: 1 }}>
          <Typography variant="h6">
            {title || otherParticipants.map(p => p.name).join(', ')}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {otherParticipants.some(p => p.isOnline) ? 'Online' : 'Offline'}
          </Typography>
        </Box>
        
        <IconButton size="small">
          <MoreIcon />
        </IconButton>
      </Box>

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: 2,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}

        {hasMoreMessages && (
          <Box sx={{ textAlign: 'center', py: 1 }}>
            <Typography
              variant="caption"
              color="primary"
              sx={{ cursor: 'pointer' }}
              onClick={onLoadMore}
            >
              Load more messages
            </Typography>
          </Box>
        )}

        <List sx={{ flex: 1 }}>
          {messages.map((message, index) => renderMessage(message, index))}
        </List>
        
        <div ref={messagesEndRef} />
      </Box>

      {/* Message Input */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          display: 'flex',
          alignItems: 'flex-end',
          gap: 1,
        }}
      >
        <IconButton
          size="small"
          onClick={() => fileInputRef.current?.click()}
          disabled={!onFileUpload}
        >
          <AttachIcon />
        </IconButton>
        
        <IconButton size="small">
          <EmojiIcon />
        </IconButton>
        
        <TextField
          fullWidth
          multiline
          maxRows={4}
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type a message..."
          variant="outlined"
          size="small"
          sx={{ mr: 1 }}
        />
        
        <IconButton
          color="primary"
          onClick={handleSendMessage}
          disabled={!newMessage.trim() || loading}
        >
          <SendIcon />
        </IconButton>
      </Box>

      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        accept="image/*,.pdf,.doc,.docx,.txt"
      />
    </Paper>
  );
};

export default ChatWindow; 