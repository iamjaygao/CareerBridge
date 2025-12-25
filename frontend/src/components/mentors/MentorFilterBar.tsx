import React from 'react';
import {
  TextField,
  Button,
  Box,
  Chip,
  Typography,
  InputAdornment,
  Paper,
  Stack,
} from '@mui/material';
import {
  Clear as ClearIcon,
  Search as SearchIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { MentorFilters } from '../../types';

interface MentorFilterBarProps {
  filters: MentorFilters;
  onFilterChange: (patch: Partial<MentorFilters>) => void;
  onFilterClear: () => void;
  searchTerm?: string;
  onSearchChange?: (value: string) => void;
}

/**
 * 1. Primary Track Options (P0)
 * Aligned with "What do you want help with right now?" section in Final Draft.
 */
const PRIMARY_TRACK_OPTIONS = [
  {
    value: 'resume_review',
    label: 'Resume review',
    description: 'Improve clarity, structure, and impact',
  },
  {
    value: 'mock_interview',
    label: 'Mock interview',
    description: 'Practice real interview scenarios',
  },
  {
    value: 'career_switch',
    label: 'Career switch',
    description: 'Plan and execute a career transition',
  },
  {
    value: 'advanced_interview',
    label: 'Advanced interview',
    description: 'System design, case studies, or senior roles',
  },
] as const;

/**
 * 2. Industry Options (Secondary Filters)
 * Cross-industry support as per positioning document.
 */
const INDUSTRY_OPTIONS = [
  'Technology',
  'Product & Design',
  'Business & Consulting',
  'Data & Analytics',
  'Startup & Entrepreneurship',
  'Other',
];

const MentorFilterBar: React.FC<MentorFilterBarProps> = ({
  filters,
  onFilterChange,
  onFilterClear,
  searchTerm = '',
  onSearchChange,
}) => {

  return (
    <Box sx={{ width: '100%', mb: 4 }}>
      {/* --- Section 1: Problem-Oriented Guidance (Primary) --- */}
      <Typography variant="h6" sx={{ mb: 2, fontWeight: 700 }}>
        What do you want help with right now?
      </Typography>
      
      <Box 
        sx={{ 
          display: 'grid', 
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' }, 
          gap: 2, 
          mb: 4 
        }}
      >
        {PRIMARY_TRACK_OPTIONS.map((opt) => {
          const isSelected = filters.primary_track === opt.value;
          return (
            <Paper
              key={opt.value}
              elevation={isSelected ? 0 : 1}
              onClick={() => onFilterChange({ primary_track: opt.value })}
              sx={{
                p: 2,
                cursor: 'pointer',
                borderRadius: 2,
                border: '2px solid',
                borderColor: isSelected ? 'primary.main' : 'transparent',
                bgcolor: isSelected ? 'primary.50' : 'background.paper',
                transition: 'all 0.2s ease',
                '&:hover': { borderColor: isSelected ? 'primary.main' : 'grey.300' },
              }}
            >
              <Typography variant="subtitle1" sx={{ fontWeight: 700, color: isSelected ? 'primary.main' : 'text.primary' }}>
                {opt.label}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {opt.description}
              </Typography>
            </Paper>
          );
        })}
      </Box>

      {/* --- Section 2: Industry Filters --- */}
      <Typography variant="subtitle1" sx={{ mb: 1.5, fontWeight: 600 }}>
        Industry
      </Typography>
      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap sx={{ mb: 4 }}>
        {INDUSTRY_OPTIONS.map((industry) => (
          <Chip
            key={industry}
            label={industry}
            onClick={() => onFilterChange({ industry: filters.industry === industry ? undefined : industry })}
            color={filters.industry === industry ? 'primary' : 'default'}
            // Fixed L141: Changed 'contained' to 'filled'
            variant={filters.industry === industry ? 'filled' : 'outlined'}
            sx={{ fontWeight: 500 }}
          />
        ))}
      </Stack>

      {/* --- Section 3: Refinement & Search --- */}
      <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
        <TextField
          size="small"
          placeholder="Search by background or expertise..."
          value={searchTerm}
          onChange={(e) => onSearchChange?.(e.target.value)}
          sx={{ flexGrow: 1, maxWidth: { md: '400px' } }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        
        <Chip
          icon={<FilterIcon />}
          label="Verified Professionals Only"
          onClick={() => onFilterChange({ is_verified: !filters.is_verified })}
          color={filters.is_verified ? 'success' : 'default'}
          // Fixed L168: Changed 'contained' to 'filled'
          variant={filters.is_verified ? 'filled' : 'outlined'}
        />

        <Button
          startIcon={<ClearIcon />}
          onClick={onFilterClear}
          sx={{ ml: 'auto', textTransform: 'none', color: 'text.secondary' }}
        >
          Clear all
        </Button>
      </Box>
    </Box>
  );
};

export default MentorFilterBar;
