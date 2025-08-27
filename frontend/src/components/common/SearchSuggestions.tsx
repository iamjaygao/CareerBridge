import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Chip,
  Divider,
  Paper,
  CircularProgress,
} from '@mui/material';
import {
  Search as SearchIcon,
  TrendingUp as TrendingIcon,
  Work as WorkIcon,
  Business as BusinessIcon,
  School as SchoolIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { SearchSuggestion } from '../../services/search/searchService';

interface SearchSuggestionsProps {
  query: string;
  suggestions: SearchSuggestion[];
  loading?: boolean;
  onSuggestionClick: (suggestion: SearchSuggestion) => void;
  onTrendingClick?: (suggestion: SearchSuggestion) => void;
  showTrending?: boolean;
  trendingSearches?: SearchSuggestion[];
  maxSuggestions?: number;
}

const SearchSuggestions: React.FC<SearchSuggestionsProps> = ({
  query,
  suggestions,
  loading = false,
  onSuggestionClick,
  onTrendingClick,
  showTrending = true,
  trendingSearches = [],
  maxSuggestions = 10,
}) => {
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setHighlightedIndex(-1);
  }, [query]);

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'mentor':
        return <PersonIcon color="primary" />;
      case 'skill':
        return <SchoolIcon color="secondary" />;
      case 'industry':
        return <BusinessIcon color="info" />;
      case 'job_title':
        return <WorkIcon color="success" />;
      case 'company':
        return <BusinessIcon color="warning" />;
      default:
        return <SearchIcon color="action" />;
    }
  };

  const getSuggestionColor = (type: string) => {
    switch (type) {
      case 'mentor':
        return 'primary';
      case 'skill':
        return 'secondary';
      case 'industry':
        return 'info';
      case 'job_title':
        return 'success';
      case 'company':
        return 'warning';
      default:
        return 'default';
    }
  };

  const highlightQuery = (text: string, query: string) => {
    if (!query.trim()) return text;
    
    const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);
    
    return parts.map((part, index) => 
      regex.test(part) ? (
        <span key={index} style={{ backgroundColor: 'yellow', fontWeight: 'bold' }}>
          {part}
        </span>
      ) : part
    );
  };

  const handleKeyDown = (event: React.KeyboardEvent) => {
    const totalItems = suggestions.length + (showTrending ? trendingSearches.length : 0);
    
    switch (event.key) {
      case 'ArrowDown':
        event.preventDefault();
        setHighlightedIndex(prev => 
          prev < totalItems - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        event.preventDefault();
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : totalItems - 1
        );
        break;
      case 'Enter':
        event.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < suggestions.length) {
          onSuggestionClick(suggestions[highlightedIndex]);
        } else if (highlightedIndex >= suggestions.length && onTrendingClick) {
          const trendingIndex = highlightedIndex - suggestions.length;
          onTrendingClick(trendingSearches[trendingIndex]);
        }
        break;
      case 'Escape':
        setHighlightedIndex(-1);
        break;
    }
  };

  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.querySelectorAll('[data-suggestion-index]');
      const highlightedItem = items[highlightedIndex] as HTMLElement;
      if (highlightedItem) {
        highlightedItem.scrollIntoView({ block: 'nearest' });
      }
    }
  }, [highlightedIndex]);

  const renderSuggestion = (suggestion: SearchSuggestion, index: number, isTrending = false) => (
    <ListItem
      key={`${suggestion.id}-${isTrending ? 'trending' : 'suggestion'}`}
      button
      onClick={() => isTrending ? onTrendingClick?.(suggestion) : onSuggestionClick(suggestion)}
      sx={{
        backgroundColor: highlightedIndex === index ? 'action.hover' : 'transparent',
        '&:hover': {
          backgroundColor: 'action.hover',
        },
      }}
      data-suggestion-index={index}
    >
      <ListItemIcon>
        {isTrending ? <TrendingIcon color="warning" /> : getSuggestionIcon(suggestion.type)}
      </ListItemIcon>
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="body2">
              {highlightQuery(suggestion.text, query)}
            </Typography>
            <Chip
              label={suggestion.type}
              size="small"
              color={getSuggestionColor(suggestion.type) as any}
              variant="outlined"
            />
            {isTrending && (
              <Chip
                label="Trending"
                size="small"
                color="warning"
                variant="outlined"
              />
            )}
          </Box>
        }
        secondary={
          suggestion.metadata && (
            <Typography variant="caption" color="text.secondary">
              {suggestion.metadata.description || `${suggestion.relevance}% match`}
            </Typography>
          )
        }
      />
    </ListItem>
  );

  if (loading) {
    return (
      <Paper sx={{ p: 2, maxHeight: 400, overflow: 'auto' }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
          <CircularProgress size={24} />
        </Box>
      </Paper>
    );
  }

  const hasSuggestions = suggestions.length > 0;
  const hasTrending = showTrending && trendingSearches.length > 0;

  if (!hasSuggestions && !hasTrending) {
    return null;
  }

  return (
    <Paper 
      ref={listRef}
      sx={{ 
        maxHeight: 400, 
        overflow: 'auto',
        position: 'absolute',
        top: '100%',
        left: 0,
        right: 0,
        zIndex: 1000,
        boxShadow: 3,
      }}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      <List dense>
        {/* Search Suggestions */}
        {hasSuggestions && (
          <>
            <ListItem>
              <Typography variant="subtitle2" color="text.secondary">
                Search Suggestions
              </Typography>
            </ListItem>
            {suggestions.slice(0, maxSuggestions).map((suggestion, index) =>
              renderSuggestion(suggestion, index)
            )}
          </>
        )}

        {/* Trending Searches */}
        {hasTrending && (
          <>
            {hasSuggestions && <Divider />}
            <ListItem>
              <Typography variant="subtitle2" color="text.secondary">
                Trending Searches
              </Typography>
            </ListItem>
            {trendingSearches.slice(0, 5).map((suggestion, index) =>
              renderSuggestion(suggestion, suggestions.length + index, true)
            )}
          </>
        )}
      </List>
    </Paper>
  );
};

export default SearchSuggestions; 