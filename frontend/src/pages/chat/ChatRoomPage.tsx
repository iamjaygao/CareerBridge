import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Paper, Typography, IconButton } from '@mui/material';
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material';
import PageHeader from '../../components/common/PageHeader';
import LoadingSpinner from '../../components/common/LoadingSpinner';
import ErrorAlert from '../../components/common/ErrorAlert';
import ChatWindow from '../../components/chat/ChatWindow';
import chatService, { ChatRoom } from '../../services/api/chatService';

const ChatRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const [chatRoom, setChatRoom] = useState<ChatRoom | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (roomId) {
      loadChatRoom();
    }
  }, [roomId]);

  const loadChatRoom = async () => {
    try {
      setLoading(true);
      const room = await chatService.getChatRoom(parseInt(roomId!));
      setChatRoom(room);
    } catch (err) {
      setError('Failed to load chat room');
      console.error('Error loading chat room:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/chat');
  };

  if (loading) {
    return <LoadingSpinner message="Loading chat room..." />;
  }

  if (error) {
    return <ErrorAlert message={error} />;
  }

  if (!chatRoom) {
    return <ErrorAlert message="Chat room not found" />;
  }

  return (
    <>
      <PageHeader
        title={`Chat with ${chatRoom.mentor_name}`}
        breadcrumbs={[
          { label: 'Chats', path: '/chat' },
          { label: chatRoom.mentor_name || 'Chat', path: `/chat/${roomId}` }
        ]}
        action={
          <IconButton onClick={handleBack}>
            <ArrowBackIcon />
          </IconButton>
        }
      />

      <Box sx={{ mt: 3 }}>
        <ChatWindow chatRoomId={parseInt(roomId!)} />
      </Box>
    </>
  );
};

export default ChatRoomPage; 