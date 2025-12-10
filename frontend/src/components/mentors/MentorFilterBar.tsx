import React, { useState, useEffect } from 'react';
import {
  TextField,
  MenuItem,
  Button,
  Box,
  Autocomplete,
  Chip,
  InputAdornment,
} from '@mui/material';
import { FilterList as FilterIcon, Clear as ClearIcon, Search as SearchIcon } from '@mui/icons-material';
import { MentorFilters } from '../../types';

interface MentorFilterBarProps {
  filters: MentorFilters;
  onFilterChange: (filters: MentorFilters) => void;
  onFilterClear: () => void;
  searchTerm?: string;
  onSearchChange?: (value: string) => void;
}

const industries = [
  'Technology',
  'Finance',
  'Healthcare',
  'Education',
  'Marketing',
  'Design',
  'Consulting',
  'Other',
];

const experienceLevels = [
  { value: 'junior', label: '1-3 years' },
  { value: 'mid', label: '4-7 years' },
  { value: 'senior', label: '8+ years' },
];

const specializations = [
  'Software Development',
  'Data Science',
  'Product Management',
  'UX/UI Design',
  'Digital Marketing',
  'Business Strategy',
  'Leadership',
  'Career Development',
];



const MentorFilterBar: React.FC<MentorFilterBarProps> = ({
  filters,
  onFilterChange,
  onFilterClear,
  searchTerm = '',
  onSearchChange,
}) => {
  const [localFilters, setLocalFilters] = useState<MentorFilters>(filters);
  useEffect(() => {
    setLocalFilters(filters);
  }, [filters]);

  const handleFilterChange = (field: keyof MentorFilters, value: any) => {
    const newFilters = { ...localFilters, [field]: value };
    setLocalFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleApply = () => {
    onFilterChange(localFilters);
  };

  // Standard height for all elements: 44px (h-11)
  const standardHeight = '44px';

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: 'center',
        gap: 1.5,
        flexWrap: 'wrap',
        width: '100%',
        mb: 3,
      }}
    >
      {/* Search Input - takes remaining space */}
      <TextField
        placeholder="Search mentors by name, skills, or industry…"
        value={searchTerm}
        onChange={(e) => onSearchChange?.(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        sx={{
          flexGrow: 1,
          minWidth: { xs: '100%', sm: '200px' },
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
            height: standardHeight,
            '& input': {
              py: '12px',
            },
          },
        }}
      />

      {/* Industry Dropdown */}
      <TextField
        select
        label="Industry"
        value={localFilters.industry || ''}
        onChange={(e) => handleFilterChange('industry', e.target.value)}
        sx={{
          minWidth: '150px',
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
            height: standardHeight,
            '& .MuiSelect-select': {
              py: '12px',
            },
          },
          '& .MuiInputLabel-root': {
            transform: localFilters.industry 
              ? 'translate(14px, -9px) scale(0.75)' 
              : 'translate(14px, 14px) scale(1)',
          },
        }}
      >
        <MenuItem value="">All Industries</MenuItem>
        {industries.map((industry) => (
          <MenuItem key={industry} value={industry.toLowerCase()}>
            {industry}
          </MenuItem>
        ))}
      </TextField>

      {/* Experience Level Dropdown */}
      <TextField
        select
        label="Experience"
        value={localFilters.experience_level || ''}
        onChange={(e) => handleFilterChange('experience_level', e.target.value)}
        sx={{
          minWidth: '150px',
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
            height: standardHeight,
            '& .MuiSelect-select': {
              py: '12px',
            },
          },
          '& .MuiInputLabel-root': {
            transform: localFilters.experience_level 
              ? 'translate(14px, -9px) scale(0.75)' 
              : 'translate(14px, 14px) scale(1)',
          },
        }}
      >
        <MenuItem value="">All Levels</MenuItem>
        {experienceLevels.map((level) => (
          <MenuItem key={level.value} value={level.value}>
            {level.label}
          </MenuItem>
        ))}
      </TextField>

      {/* Specialization Dropdown */}
      <Autocomplete
        options={specializations}
        value={localFilters.specialization || null}
        onChange={(_, newValue) =>
          handleFilterChange('specialization', newValue || '')
        }
        renderInput={(params) => (
          <TextField {...params} label="Specialization" />
        )}
        sx={{
          minWidth: '150px',
          '& .MuiOutlinedInput-root': {
            borderRadius: '8px',
            height: standardHeight,
            '& input': {
              py: '12px',
            },
          },
          '& .MuiInputLabel-root': {
            transform: localFilters.specialization 
              ? 'translate(14px, -9px) scale(0.75)' 
              : 'translate(14px, 14px) scale(1)',
          },
        }}
      />

      {/* Apply Button */}
      <Button
        variant="contained"
        onClick={handleApply}
        startIcon={<FilterIcon />}
        sx={{
          bgcolor: '#1976d2',
          color: 'white',
          px: 2,
          height: standardHeight,
          borderRadius: '8px',
          '&:hover': {
            bgcolor: '#1565c0',
          },
          minWidth: '120px',
          textTransform: 'none',
          fontWeight: 500,
        }}
      >
        Apply
      </Button>

      {/* Clear Button */}
      <Button
        variant="outlined"
        onClick={onFilterClear}
        startIcon={<ClearIcon />}
        sx={{
          borderColor: '#e0e0e0',
          color: '#616161',
          px: 2,
          height: standardHeight,
          borderRadius: '8px',
          '&:hover': {
            borderColor: '#bdbdbd',
            bgcolor: '#f5f5f5',
          },
          minWidth: '120px',
          textTransform: 'none',
          fontWeight: 500,
        }}
      >
        Clear
      </Button>
    </Box>
  );
};

export default MentorFilterBar;