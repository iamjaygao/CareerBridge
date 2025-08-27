import React, { useState, useEffect } from 'react';
import {
  TextField,
  MenuItem,
  Button,
  Box,
  Autocomplete,
  Chip,
} from '@mui/material';
import { Grid } from '@mui/material';
import { FilterList as FilterIcon, Clear as ClearIcon } from '@mui/icons-material';
import { MentorFilters } from '../../services/api/mentorService';

interface MentorFilterBarProps {
  filters: MentorFilters;
  onFilterChange: (filters: MentorFilters) => void;
  onFilterClear: () => void;
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

  return (
    <Box sx={{ mb: 4 }}>
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            select
            fullWidth
            label="Industry"
            value={localFilters.industry || ''}
            onChange={(e) => handleFilterChange('industry', e.target.value)}
          >
            <MenuItem value="">All Industries</MenuItem>
            {industries.map((industry) => (
              <MenuItem key={industry} value={industry.toLowerCase()}>
                {industry}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <TextField
            select
            fullWidth
            label="Experience Level"
            value={localFilters.experience_level || ''}
            onChange={(e) => handleFilterChange('experience_level', e.target.value)}
          >
            <MenuItem value="">All Levels</MenuItem>
            {experienceLevels.map((level) => (
              <MenuItem key={level.value} value={level.value}>
                {level.label}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Autocomplete
            multiple
            options={specializations}
            value={localFilters.specialization ? [localFilters.specialization] : []}
            onChange={(_, newValue) =>
              handleFilterChange('specialization', newValue[0] || '')
            }
            renderInput={(params) => (
              <TextField {...params} label="Specialization" />
            )}
            renderTags={(value, getTagProps) =>
              value.map((option, index) => (
                <Chip
                  label={option}
                  {...getTagProps({ index })}
                  size="small"
                />
              ))
            }
          />
        </Grid>



        <Grid item xs={12}>
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              startIcon={<ClearIcon />}
              onClick={onFilterClear}
              variant="outlined"
            >
              Clear Filters
            </Button>
            <Button
              startIcon={<FilterIcon />}
              onClick={() => onFilterChange(localFilters)}
              variant="contained"
            >
              Apply Filters
            </Button>
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
};

export default MentorFilterBar;