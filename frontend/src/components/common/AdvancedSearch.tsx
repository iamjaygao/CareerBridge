import React, { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Typography,
  Collapse,
  IconButton,
  Paper,
  Grid,
  Divider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  Clear as ClearIcon,
  ExpandMore as ExpandMoreIcon,
  Tune as TuneIcon,
} from '@mui/icons-material';

export interface SearchFilter {
  field: string;
  value: string | number | boolean | string[];
  operator: 'equals' | 'contains' | 'starts_with' | 'ends_with' | 'greater_than' | 'less_than' | 'in' | 'not_in';
}

export interface SortOption {
  field: string;
  direction: 'asc' | 'desc';
}

export interface SearchField {
  key: string;
  label: string;
  type: 'text' | 'select' | 'multiselect' | 'range' | 'boolean' | 'date';
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  step?: number;
  placeholder?: string;
}

export interface AdvancedSearchProps {
  fields: SearchField[];
  onSearch: (query: string, filters: SearchFilter[], sort: SortOption | null) => void;
  onClear?: () => void;
  loading?: boolean;
  placeholder?: string;
  showAdvanced?: boolean;
  defaultSort?: SortOption;
}

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  fields,
  onSearch,
  onClear,
  loading = false,
  placeholder = 'Search...',
  showAdvanced = false,
  defaultSort = null,
}) => {
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<SearchFilter[]>([]);
  const [sort, setSort] = useState<SortOption | null>(defaultSort);
  const [showFilters, setShowFilters] = useState(showAdvanced);
  const [fieldValues, setFieldValues] = useState<Record<string, any>>({});

  useEffect(() => {
    // Initialize field values
    const initialValues: Record<string, any> = {};
    fields.forEach(field => {
      if (field.type === 'multiselect') {
        initialValues[field.key] = [];
      } else if (field.type === 'range') {
        initialValues[field.key] = [field.min || 0, field.max || 100];
      } else if (field.type === 'boolean') {
        initialValues[field.key] = '';
      } else {
        initialValues[field.key] = '';
      }
    });
    setFieldValues(initialValues);
  }, [fields]);

  const handleSearch = () => {
    const activeFilters = filters.filter(filter => 
      filter.value !== '' && 
      filter.value !== null && 
      filter.value !== undefined &&
      (Array.isArray(filter.value) ? filter.value.length > 0 : true)
    );
    onSearch(query, activeFilters, sort);
  };

  const handleClear = () => {
    setQuery('');
    setFilters([]);
    setSort(defaultSort);
    setFieldValues({});
    onClear?.();
  };

  const addFilter = (field: SearchField) => {
    const value = fieldValues[field.key];
    if (value && value !== '') {
      const newFilter: SearchFilter = {
        field: field.key,
        value: value,
        operator: field.type === 'multiselect' ? 'in' : 'contains',
      };
      setFilters(prev => [...prev, newFilter]);
      setFieldValues(prev => ({ ...prev, [field.key]: field.type === 'multiselect' ? [] : '' }));
    }
  };

  const removeFilter = (index: number) => {
    setFilters(prev => prev.filter((_, i) => i !== index));
  };

  const handleFieldChange = (fieldKey: string, value: any) => {
    setFieldValues(prev => ({ ...prev, [fieldKey]: value }));
  };

  const renderFieldInput = (field: SearchField) => {
    const value = fieldValues[field.key];

    switch (field.type) {
      case 'text':
        return (
          <TextField
            fullWidth
            label={field.label}
            value={value}
            onChange={(e) => handleFieldChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            size="small"
          />
        );

      case 'select':
        return (
          <FormControl fullWidth size="small">
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={value}
              label={field.label}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              {field.options?.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'multiselect':
        return (
          <FormControl fullWidth size="small">
            <InputLabel>{field.label}</InputLabel>
            <Select
              multiple
              value={value}
              label={field.label}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
              renderValue={(selected: string[]) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value: string) => {
                    const option = field.options?.find(opt => opt.value === value);
                    return (
                      <Chip key={value} label={option?.label || value} size="small" />
                    );
                  })}
                </Box>
              )}
            >
              {field.options?.map(option => (
                <MenuItem key={option.value} value={option.value}>
                  {option.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        );

      case 'range':
        return (
          <Box>
            <Typography variant="body2" gutterBottom>
              {field.label}
            </Typography>
            <Slider
              value={value}
              onChange={(_, newValue) => handleFieldChange(field.key, newValue)}
              valueLabelDisplay="auto"
              min={field.min || 0}
              max={field.max || 100}
              step={field.step || 1}
            />
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="caption">{value[0]}</Typography>
              <Typography variant="caption">{value[1]}</Typography>
            </Box>
          </Box>
        );

      case 'boolean':
        return (
          <FormControl fullWidth size="small">
            <InputLabel>{field.label}</InputLabel>
            <Select
              value={value}
              label={field.label}
              onChange={(e) => handleFieldChange(field.key, e.target.value)}
            >
              <MenuItem value="">All</MenuItem>
              <MenuItem value="true">Yes</MenuItem>
              <MenuItem value="false">No</MenuItem>
            </Select>
          </FormControl>
        );

      default:
        return null;
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      {/* Search Bar */}
      <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
        <TextField
          fullWidth
          placeholder={placeholder}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          InputProps={{
            startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />,
          }}
        />
        <Button
          variant="contained"
          onClick={handleSearch}
          disabled={loading}
          startIcon={<SearchIcon />}
        >
          Search
        </Button>
        <IconButton
          onClick={() => setShowFilters(!showFilters)}
          color={showFilters ? 'primary' : 'default'}
        >
          <FilterIcon />
        </IconButton>
        <IconButton onClick={handleClear} color="error">
          <ClearIcon />
        </IconButton>
      </Box>

      {/* Active Filters */}
      {filters.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Active Filters:
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {filters.map((filter, index) => (
              <Chip
                key={index}
                label={`${filter.field}: ${Array.isArray(filter.value) ? filter.value.join(', ') : filter.value}`}
                onDelete={() => removeFilter(index)}
                size="small"
              />
            ))}
          </Box>
        </Box>
      )}

      {/* Advanced Filters */}
      <Collapse in={showFilters}>
        <Divider sx={{ my: 2 }} />
        
        <Accordion defaultExpanded>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <TuneIcon sx={{ mr: 1 }} />
            <Typography>Advanced Filters</Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Grid container spacing={2}>
              {/* Filter Fields */}
              <Grid item xs={12} md={8}>
                <Typography variant="h6" gutterBottom>
                  Filters
                </Typography>
                <Grid container spacing={2}>
                  {fields.map((field) => (
                    <Grid item xs={12} sm={6} key={field.key}>
                      <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
                        <Box sx={{ flex: 1 }}>
                          {renderFieldInput(field)}
                        </Box>
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => addFilter(field)}
                          disabled={!fieldValues[field.key] || 
                            (Array.isArray(fieldValues[field.key]) && fieldValues[field.key].length === 0)}
                        >
                          Add
                        </Button>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              </Grid>

              {/* Sort Options */}
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>
                  Sort By
                </Typography>
                <FormControl fullWidth size="small">
                  <InputLabel>Field</InputLabel>
                  <Select
                    value={sort?.field || ''}
                    label="Field"
                    onChange={(e) => setSort(prev => ({ 
                      field: e.target.value, 
                      direction: prev?.direction || 'asc' 
                    }))}
                  >
                    <MenuItem value="">None</MenuItem>
                    {fields.map(field => (
                      <MenuItem key={field.key} value={field.key}>
                        {field.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                {sort?.field && (
                  <FormControl fullWidth size="small" sx={{ mt: 1 }}>
                    <InputLabel>Direction</InputLabel>
                    <Select
                      value={sort?.direction || 'asc'}
                      label="Direction"
                      onChange={(e) => setSort(prev => prev ? { 
                       ...prev, 
                       direction: e.target.value as 'asc' | 'desc' 
                     } : null)}
                    >
                      <MenuItem value="asc">Ascending</MenuItem>
                      <MenuItem value="desc">Descending</MenuItem>
                    </Select>
                  </FormControl>
                )}
              </Grid>
            </Grid>
          </AccordionDetails>
        </Accordion>
      </Collapse>
    </Paper>
  );
};

export default AdvancedSearch; 