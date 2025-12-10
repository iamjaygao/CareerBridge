import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Avatar,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Rating,
  Alert,
} from '@mui/material';
import {
  Search as SearchIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  CheckCircle as VerifiedIcon,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { RootState } from '../../store';
import { useRole } from '../../contexts/RoleContext';
import adminService from '../../services/api/adminService';
import LoadingSpinner from '../../components/common/LoadingSpinner';

interface Mentor {
  mentor_id: number;
  user_id: number;
  username: string;
  name: string;
  first_name?: string;
  last_name?: string;
  email: string;
  status: string;
  is_approved: boolean;
  is_verified: boolean;
  verification_badge?: string;
  specializations?: string[];
  years_of_experience?: number;
  total_sessions: number;
  average_rating: number;
  hourly_rate?: number;
  total_earnings: number;
}

const MentorsPage: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const { isSuperAdmin } = useRole();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  useEffect(() => {
    const fetchMentors = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await adminService.getAllMentors();
        
        // Handle different response formats
        let mentorsList: any[] = [];
        if (Array.isArray(data)) {
          mentorsList = data;
        } else if (data.results && Array.isArray(data.results)) {
          mentorsList = data.results;
        } else if (data.data && Array.isArray(data.data)) {
          mentorsList = data.data;
        }
        
        // Normalize mentor objects - use backend fields directly
        const normalizedMentors: Mentor[] = mentorsList.map((m: any) => ({
          mentor_id: m.mentor_id || m.id,
          user_id: m.user_id || m.user__id,
          username: m.username || m.user?.username || '',
          name: m.name || (m.first_name && m.last_name ? `${m.first_name} ${m.last_name}` : m.username || 'Unknown'),
          first_name: m.first_name || m.user?.first_name || '',
          last_name: m.last_name || m.user?.last_name || '',
          email: m.email || m.user?.email || '',
          status: m.status || 'pending',
          is_approved: m.is_approved !== undefined ? m.is_approved : (m.status === 'approved'),
          is_verified: m.is_verified !== undefined ? m.is_verified : false,
          verification_badge: m.verification_badge || '',
          specializations: Array.isArray(m.specializations) ? m.specializations : [],
          years_of_experience: m.years_of_experience || 0,
          total_sessions: m.total_sessions || 0,
          average_rating: m.average_rating || 0,
          hourly_rate: m.hourly_rate || m.price_per_hour || null,
          total_earnings: m.total_earnings || 0,
        }));
        
        setMentors(normalizedMentors);
      } catch (err: any) {
        const errorMessage = err?.response?.data?.detail 
          || err?.response?.data?.error
          || err?.message 
          || 'Failed to load mentors';
        setError(errorMessage);
        console.error('Failed to fetch mentors:', err);
        setMentors([]);
      } finally {
        setLoading(false);
      }
    };

    fetchMentors();
  }, []);

  if (!isSuperAdmin) {
    return null;
  }

  const filteredMentors = mentors.filter(mentor => {
    const matchesSearch = mentor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         mentor.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         mentor.username.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || 
                         (statusFilter === 'verified' && mentor.is_verified) ||
                         (statusFilter === 'approved' && mentor.is_approved) ||
                         (statusFilter === 'pending' && mentor.status === 'pending');
    return matchesSearch && matchesStatus;
  });

  const getStatusChip = (mentor: Mentor) => {
    if (mentor.is_verified && mentor.verification_badge) {
      return (
        <Chip 
          label={mentor.verification_badge || 'Verified'} 
          color="success" 
          size="small"
          icon={<VerifiedIcon />}
        />
      );
    }
    if (mentor.is_approved) {
      return <Chip label="Approved" color="success" size="small" />;
    }
    if (mentor.status === 'pending') {
      return <Chip label="Pending" color="warning" size="small" />;
    }
    return <Chip label={mentor.status} color="default" size="small" />;
  };

  if (loading) {
    return <LoadingSpinner message="Loading mentors..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Mentor Management
        </Typography>
        <Typography variant="body2" color="text.secondary">
          View and manage all mentors
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Filters */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <TextField
              placeholder="Search mentors..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
              }}
              sx={{ minWidth: 300, flexGrow: 1 }}
              size="small"
            />
            <FormControl sx={{ minWidth: 150 }} size="small">
              <InputLabel>Status</InputLabel>
              <Select
                value={statusFilter}
                label="Status"
                onChange={(e) => setStatusFilter(e.target.value)}
              >
                <MenuItem value="all">All Status</MenuItem>
                <MenuItem value="verified">Verified</MenuItem>
                <MenuItem value="approved">Approved</MenuItem>
                <MenuItem value="pending">Pending</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </CardContent>
      </Card>

      {/* Mentors Table */}
      <Card>
        <CardContent>
          <TableContainer component={Paper} variant="outlined">
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Mentor</TableCell>
                  <TableCell>Specializations</TableCell>
                  <TableCell>Experience</TableCell>
                  <TableCell>Rating</TableCell>
                  <TableCell>Verification</TableCell>
                  <TableCell>Sessions</TableCell>
                  <TableCell>Rate/Hour</TableCell>
                  <TableCell align="right">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {filteredMentors.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={8} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No mentors found
                      </Typography>
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredMentors.map((mentor) => (
                    <TableRow key={mentor.mentor_id} hover>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Avatar sx={{ mr: 2, width: 40, height: 40 }}>
                            {mentor.name.charAt(0).toUpperCase()}
                          </Avatar>
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {mentor.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {mentor.email}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {mentor.specializations && mentor.specializations.length > 0 ? (
                            <>
                              {mentor.specializations.slice(0, 2).map((spec, idx) => (
                                <Chip key={idx} label={spec} size="small" variant="outlined" />
                              ))}
                              {mentor.specializations.length > 2 && (
                                <Chip label={`+${mentor.specializations.length - 2}`} size="small" />
                              )}
                            </>
                          ) : (
                            <Typography variant="caption" color="text.secondary">
                              None
                            </Typography>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {mentor.years_of_experience || 0} years
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Rating value={mentor.average_rating} precision={0.1} readOnly size="small" />
                          <Typography variant="body2" color="text.secondary">
                            {mentor.average_rating > 0 ? mentor.average_rating.toFixed(1) : 'N/A'}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {getStatusChip(mentor)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {mentor.total_sessions}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {mentor.hourly_rate ? `$${mentor.hourly_rate}` : 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <IconButton
                          size="small"
                          color="primary"
                        >
                          <ViewIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          color="primary"
                        >
                          <EditIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    </Box>
  );
};

export default MentorsPage;
