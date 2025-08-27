import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  TextField,
  Autocomplete,
  Chip,
  Paper,
  Typography,
  Button,
  IconButton,
  Collapse,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  FormControlLabel,
  Checkbox,
  Divider,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  TrendingUp as TrendingIcon,
  History as HistoryIcon,
} from '@mui/icons-material';
import { useDebounce } from '../../hooks/useDebounce';
import { getPopularJobs, getPopularSkills, getPopularIndustries } from '../../services/api/searchService';

interface SearchFilters {
  location: string;
  experience: string;
  salary: [number, number];
  jobType: string[];
  skills: string[];
  industries: string[];
}

interface SearchSuggestion {
  type: 'job' | 'skill' | 'industry';
  value: string;
  count?: number;
}

const AdvancedSearch: React.FC<{
  onSearch: (query: string, filters: SearchFilters) => void;
  onSuggestionClick?: (suggestion: SearchSuggestion) => void;
}> = ({ onSearch, onSuggestionClick }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [suggestions, setSuggestions] = useState<SearchSuggestion[]>([]);
  const [popularData, setPopularData] = useState<{
    jobs: string[];
    skills: string[];
    industries: string[];
  }>({ jobs: [], skills: [], industries: [] });
  const [searchHistory, setSearchHistory] = useState<string[]>([]);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<SearchFilters>({
    location: '',
    experience: '',
    salary: [0, 200000],
    jobType: [],
    skills: [],
    industries: [],
  });

  const debouncedQuery = useDebounce(searchQuery, 300);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadPopularData();
    loadSearchHistory();
  }, []);

  useEffect(() => {
    if (debouncedQuery) {
      generateSuggestions(debouncedQuery);
    } else {
      setSuggestions([]);
    }
  }, [debouncedQuery]);

  const loadPopularData = async () => {
    try {
      const [jobs, skills, industries] = await Promise.all([
        getPopularJobs(),
        getPopularSkills(),
        getPopularIndustries()
      ]);
      setPopularData({ jobs, skills, industries });
    } catch (error) {
      console.error('Failed to load popular data:', error);
    }
  };

  const loadSearchHistory = () => {
    const history = localStorage.getItem('searchHistory');
    if (history) {
      setSearchHistory(JSON.parse(history));
    }
  };

  const saveSearchHistory = (query: string) => {
    const newHistory = [query, ...searchHistory.filter(item => item !== query)].slice(0, 10);
    setSearchHistory(newHistory);
    localStorage.setItem('searchHistory', JSON.stringify(newHistory));
  };

  const generateSuggestions = (query: string) => {
    const allSuggestions: SearchSuggestion[] = [];

    // Job title suggestions
    popularData.jobs
      .filter(job => job.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 5)
      .forEach(job => {
        allSuggestions.push({ type: 'job', value: job });
      });

    // Skill suggestions
    popularData.skills
      .filter(skill => skill.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 5)
      .forEach(skill => {
        allSuggestions.push({ type: 'skill', value: skill });
      });

    // Industry suggestions
    popularData.industries
      .filter(industry => industry.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 5)
      .forEach(industry => {
        allSuggestions.push({ type: 'industry', value: industry });
      });

    setSuggestions(allSuggestions);
  };

  const handleSearch = () => {
    if (searchQuery.trim()) {
      saveSearchHistory(searchQuery);
      onSearch(searchQuery, filters);
    }
  };

  const handleSuggestionClick = (suggestion: SearchSuggestion) => {
    setSearchQuery(suggestion.value);
    if (onSuggestionClick) {
      onSuggestionClick(suggestion);
    }
  };

  const handleClearFilters = () => {
    setFilters({
      location: '',
      experience: '',
      salary: [0, 200000],
      jobType: [],
      skills: [],
      industries: [],
    });
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const formatSalary = (value: number) => {
    return `$${value.toLocaleString()}`;
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Main Search Bar */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Box sx={{ flex: 1, position: 'relative' }}>
            <TextField
              ref={searchInputRef}
              fullWidth
              placeholder="Search jobs, skills, or companies..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
                endAdornment: searchQuery && (
                  <IconButton size="small" onClick={() => setSearchQuery('')}>
                    <ClearIcon />
                  </IconButton>
                ),
              }}
            />

            {/* Search Suggestions */}
            {suggestions.length > 0 && (
              <Paper
                sx={{
                  position: 'absolute',
                  top: '100%',
                  left: 0,
                  right: 0,
                  zIndex: 1000,
                  mt: 1,
                  maxHeight: 300,
                  overflow: 'auto',
                }}
              >
                {suggestions.map((suggestion, index) => (
                  <Box
                    key={index}
                    sx={{
                      p: 1.5,
                      cursor: 'pointer',
                      '&:hover': { bgcolor: 'action.hover' },
                      display: 'flex',
                      alignItems: 'center',
                      gap: 1,
                    }}
                    onClick={() => handleSuggestionClick(suggestion)}
                  >
                    <TrendingIcon sx={{ fontSize: 16, color: 'text.secondary' }} />
                    <Typography variant="body2">
                      {suggestion.value}
                    </Typography>
                    <Chip
                      label={suggestion.type}
                      size="small"
                      variant="outlined"
                      sx={{ ml: 'auto' }}
                    />
                  </Box>
                ))}
              </Paper>
            )}
          </Box>

          <Button
            variant="outlined"
            onClick={() => setShowFilters(!showFilters)}
            startIcon={<FilterIcon />}
          >
            Filters
          </Button>

          <Button
            variant="contained"
            onClick={handleSearch}
            disabled={!searchQuery.trim()}
          >
            Search
          </Button>
        </Box>

        {/* Search History */}
        {searchHistory.length > 0 && !searchQuery && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <HistoryIcon sx={{ fontSize: 14 }} />
              Recent searches
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
              {searchHistory.slice(0, 5).map((item, index) => (
                <Chip
                  key={index}
                  label={item}
                  size="small"
                  variant="outlined"
                  onClick={() => setSearchQuery(item)}
                  sx={{ cursor: 'pointer' }}
                />
              ))}
            </Box>
          </Box>
        )}
      </Paper>

      {/* Advanced Filters */}
      <Collapse in={showFilters}>
        <Paper sx={{ p: 2, mb: 2 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">Advanced Filters</Typography>
            <Button size="small" onClick={handleClearFilters}>
              Clear All
            </Button>
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 2 }}>
            {/* Location */}
            <TextField
              label="Location"
              value={filters.location}
              onChange={(e) => setFilters({ ...filters, location: e.target.value })}
              placeholder="City, State, or Remote"
            />

            {/* Experience Level */}
            <FormControl fullWidth>
              <InputLabel>Experience Level</InputLabel>
              <Select
                value={filters.experience}
                onChange={(e) => setFilters({ ...filters, experience: e.target.value })}
                label="Experience Level"
              >
                <MenuItem value="">Any</MenuItem>
                <MenuItem value="entry">Entry Level</MenuItem>
                <MenuItem value="mid">Mid Level</MenuItem>
                <MenuItem value="senior">Senior Level</MenuItem>
                <MenuItem value="lead">Lead</MenuItem>
                <MenuItem value="executive">Executive</MenuItem>
              </Select>
            </FormControl>

            {/* Salary Range */}
            <Box>
              <Typography gutterBottom>Salary Range</Typography>
              <Slider
                value={filters.salary}
                onChange={(_, value) => setFilters({ ...filters, salary: value as [number, number] })}
                valueLabelDisplay="auto"
                valueLabelFormat={formatSalary}
                min={0}
                max={200000}
                step={5000}
              />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="caption">{formatSalary(filters.salary[0])}</Typography>
                <Typography variant="caption">{formatSalary(filters.salary[1])}</Typography>
              </Box>
            </Box>

            {/* Job Type */}
            <Box>
              <Typography gutterBottom>Job Type</Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {['Full-time', 'Part-time', 'Contract', 'Internship', 'Remote'].map((type) => (
                  <FormControlLabel
                    key={type}
                    control={
                      <Checkbox
                        checked={filters.jobType.includes(type)}
                        onChange={(e) => {
                          const newTypes = e.target.checked
                            ? [...filters.jobType, type]
                            : filters.jobType.filter(t => t !== type);
                          setFilters({ ...filters, jobType: newTypes });
                        }}
                      />
                    }
                    label={type}
                  />
                ))}
              </Box>
            </Box>

            {/* Skills */}
            <Autocomplete
              multiple
              options={popularData.skills}
              value={filters.skills}
              onChange={(_, newValue) => setFilters({ ...filters, skills: newValue })}
              renderInput={(params) => (
                <TextField {...params} label="Skills" placeholder="Select skills" />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip label={option} {...getTagProps({ index })} />
                ))
              }
            />

            {/* Industries */}
            <Autocomplete
              multiple
              options={popularData.industries}
              value={filters.industries}
              onChange={(_, newValue) => setFilters({ ...filters, industries: newValue })}
              renderInput={(params) => (
                <TextField {...params} label="Industries" placeholder="Select industries" />
              )}
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip label={option} {...getTagProps({ index })} />
                ))
              }
            />
          </Box>
        </Paper>
      </Collapse>
    </Box>
  );
};

export default AdvancedSearch; 