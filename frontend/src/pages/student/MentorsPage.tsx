import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Avatar,
  Chip,
  Rating,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from '@mui/material';
import {
  Search as SearchIcon,
  BookOnline as BookIcon,
} from '@mui/icons-material';
import LoadingSpinner from '../../components/common/LoadingSpinner';

interface Mentor {
  id: number;
  name: string;
  title: string;
  company: string;
  expertise: string[];
  rating: number;
  reviews: number;
  price_per_hour: number;
  avatar?: string;
}

const StudentMentorsPage: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [mentors, setMentors] = useState<Mentor[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [expertiseFilter, setExpertiseFilter] = useState('all');

  useEffect(() => {
    setTimeout(() => {
      setMentors([
        {
          id: 1,
          name: 'John Doe',
          title: 'Senior Software Engineer',
          company: 'Tech Corp',
          expertise: ['Software Engineering', 'Career Development'],
          rating: 4.8,
          reviews: 45,
          price_per_hour: 75,
        },
        {
          id: 2,
          name: 'Jane Smith',
          title: 'Data Science Lead',
          company: 'DataCo',
          expertise: ['Data Science', 'Machine Learning'],
          rating: 4.9,
          reviews: 32,
          price_per_hour: 90,
        },
        {
          id: 3,
          name: 'Bob Johnson',
          title: 'Product Manager',
          company: 'ProductInc',
          expertise: ['Product Management', 'Strategy'],
          rating: 4.7,
          reviews: 28,
          price_per_hour: 85,
        },
      ]);
      setLoading(false);
    }, 500);
  }, []);

  const filteredMentors = mentors.filter(mentor => {
    const matchesSearch = mentor.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         mentor.expertise.some(exp => exp.toLowerCase().includes(searchTerm.toLowerCase()));
    const matchesExpertise = expertiseFilter === 'all' || mentor.expertise.includes(expertiseFilter);
    return matchesSearch && matchesExpertise;
  });

  if (loading) {
    return <LoadingSpinner message="Loading mentors..." />;
  }

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" sx={{ fontWeight: 700, mb: 1 }}>
          Find a Mentor
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Connect with experienced professionals to advance your career
        </Typography>
      </Box>

      {/* Filters */}
      <Card sx={{ mb: 4 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                placeholder="Search mentors or expertise..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                }}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <FormControl fullWidth>
                <InputLabel>Expertise Area</InputLabel>
                <Select
                  value={expertiseFilter}
                  label="Expertise Area"
                  onChange={(e) => setExpertiseFilter(e.target.value)}
                >
                  <MenuItem value="all">All Expertise</MenuItem>
                  <MenuItem value="Software Engineering">Software Engineering</MenuItem>
                  <MenuItem value="Data Science">Data Science</MenuItem>
                  <MenuItem value="Product Management">Product Management</MenuItem>
                  <MenuItem value="Career Development">Career Development</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button
                variant="outlined"
                fullWidth
                onClick={() => {
                  setSearchTerm('');
                  setExpertiseFilter('all');
                }}
              >
                Clear
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Mentors Grid */}
      <Grid container spacing={3}>
        {filteredMentors.map((mentor) => (
          <Grid item xs={12} sm={6} md={4} key={mentor.id}>
            <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
              <CardContent sx={{ flexGrow: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar
                    src={mentor.avatar}
                    sx={{ width: 64, height: 64, mr: 2, bgcolor: 'primary.main' }}
                  >
                    {mentor.name.charAt(0)}
                  </Avatar>
                  <Box sx={{ flexGrow: 1 }}>
                    <Typography variant="h6" sx={{ fontWeight: 600 }}>
                      {mentor.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {mentor.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {mentor.company}
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Rating value={mentor.rating} precision={0.1} readOnly size="small" />
                    <Typography variant="body2" sx={{ ml: 1 }}>
                      {mentor.rating} ({mentor.reviews} reviews)
                    </Typography>
                  </Box>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Expertise:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {mentor.expertise.map((exp, idx) => (
                      <Chip key={idx} label={exp} size="small" variant="outlined" />
                    ))}
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    ${mentor.price_per_hour}/hr
                  </Typography>
                </Box>
                <Button
                  variant="contained"
                  fullWidth
                  startIcon={<BookIcon />}
                  onClick={() => navigate('/student/appointments')}
                  sx={{
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    '&:hover': {
                      background: 'linear-gradient(135deg, #5568d3 0%, #6a3d8f 100%)',
                    },
                  }}
                >
                  Book Session
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
};

export default StudentMentorsPage;

