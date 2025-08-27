import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Avatar,
  Typography,
  Badge,
  IconButton,
  Divider,
  CircularProgress,
  Alert,
  Fab,
} from '@mui/material';
import {
  Chat as ChatIcon,
  MoreVert as MoreVertIcon,
  Add as AddIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import chatService, { ChatRoom } from '../../services/api/chatService';

const ChatListPage: React.FC = () => {
  const navigate = useNavigate();
  const [chatRooms, setChatRooms] = useState<ChatRoom[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadChatRooms();
  }, []);

  const loadChatRooms = async () => {
    try {
      setLoading(true);
      const rooms = await chatService.getChatRooms();
      setChatRooms(rooms);
    } catch (err) {
      setError('Failed to load chat rooms');
      console.error('Error loading chat rooms:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleChatRoomClick = (roomId: number) => {
    navigate(`/chat/${roomId}`);
  };

  const formatLastMessage = (lastMessage: ChatRoom['last_message']) => {
    if (!lastMessage) return 'No messages yet';
    return lastMessage.content.length > 50 
      ? `${lastMessage.content.substring(0, 50)}...`
      : lastMessage.content;
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);

    if (diffInHours < 24) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffInHours < 48) {
      return 'Yesterday';
    } else {
      return date.toLocaleDateString();
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading chat rooms..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  return (
    <>
      <PageHeader
        title="Chats"
        breadcrumbs={[{ label: 'Chats', path: '/chat' }]}
      />

      <Paper sx={{ mt: 3 }}>
        {chatRooms.length === 0 ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <ChatIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No chats yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Start a conversation with a mentor to begin chatting
            </Typography>
          </Box>
        ) : (
          <List>
            {chatRooms.map((room, index) => (
              <React.Fragment key={room.id}>
                <ListItem
                  button
                  onClick={() => handleChatRoomClick(room.id)}
                  sx={{ py: 2 }}
                >
                  <ListItemAvatar>
                    <Badge
                      badgeContent={room.unread_count}
                      color="primary"
                      invisible={room.unread_count === 0}
                    >
                      <Avatar>
                        {room.mentor_name.charAt(0)}
                      </Avatar>
                    </Badge>
                  </ListItemAvatar>
                  
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography variant="subtitle1" sx={{ fontWeight: room.unread_count > 0 ? 600 : 400 }}>
                          {room.mentor_name}
                        </Typography>
                        {room.unread_count > 0 && (
                          <Box
                            sx={{
                              width: 8,
                              height: 8,
                              borderRadius: '50%',
                              bgcolor: 'primary.main',
                            }}
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            fontWeight: room.unread_count > 0 ? 500 : 400,
                            color: room.unread_count > 0 ? 'text.primary' : 'text.secondary',
                          }}
                        >
                          {formatLastMessage(room.last_message)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {room.last_message ? formatTime(room.last_message.created_at) : ''}
                        </Typography>
                      </Box>
                    }
                  />
                  
                  <ListItemSecondaryAction>
                    <IconButton edge="end" size="small">
                      <MoreVertIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
                
                {index < chatRooms.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      <Fab
        color="primary"
        aria-label="add"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => navigate('/mentors')}
      >
        <AddIcon />
      </Fab>
    </>
  );
};

export default ChatListPage; 