import React from 'react';
import {
  Box,
  Avatar,
  Typography,
  Chip,
  Rating,
  Button,
} from '@mui/material';
import { Mentor } from '../../types';
import { Tooltip } from '@mui/material';


interface MentorSidebarCardProps {
  mentor: Mentor;
  onViewServices?: () => void;
}

const MentorSidebarCard: React.FC<MentorSidebarCardProps> = ({
  mentor,
  onViewServices,
}) => {
  /**
   * =========================
   * Badge (SINGLE SOURCE: contract)
   * Only show badge if backend provides it
   * =========================
   */
  const badge = mentor.badges?.[0];
  const showBadge = badge === 'top_pick' || badge === 'verified' || badge === 'new';

  const badgeLabel =
    badge === 'top_pick'
      ? 'Top rated'
      : badge === 'verified'
      ? 'Verified Mentor'
      : badge === 'new'
      ? 'New mentor'
      : undefined;

  /**
   * =========================
   * Rating / Trust label
   * =========================
   */
  const showRating = mentor.rating !== null;

  return (
    <Box
      sx={{
        p: 3,
        borderRadius: 3,
        border: '1px solid',
        borderColor: 'divider',
        textAlign: 'center',
      }}
    >
      {/* =========================
          1. Badge (only if backend provides)
      ========================= */}
      {showBadge && (
        <Box mb={1}>
          {badge === 'verified' ? (
            <Tooltip title="Verified by CareerBridge">
              <Chip
                label="Verified Mentor"
                size="small"
                color="success"
              />
            </Tooltip>
          ) : badge === 'new' ? (
            <Chip
              label="New mentor"
              size="small"
              color="info"
            />
          ) : (
            <Chip
              label={badgeLabel}
              size="small"
              color="primary"
            />
          )}
        </Box>
      )}

      {/* =========================
          2. Avatar
      ========================= */}
      <Avatar
        src={mentor.user?.avatar}
        sx={{
          width: 72,
          height: 72,
          mx: 'auto',
          mb: 1.5,
        }}
      >
        {mentor.display_name?.[0]}
      </Avatar>

      {/* =========================
          3. Name
      ========================= */}
      <Typography
        fontWeight={700}
        sx={{
          fontSize: '1rem',
          mb: 0.5,
        }}
      >
        {mentor.display_name}
      </Typography>

      {/* =========================
          4. Rating OR Trust label
      ========================= */}
      <Box
        minHeight={24}
        display="flex"
        justifyContent="center"
        alignItems="center"
        mb={2}
      >
        {showRating ? (
          <>
            <Rating
              value={mentor.rating ?? 0}
              precision={0.5}
              readOnly
              size="small"
            />
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ ml: 0.5 }}
            >
              {mentor.rating?.toFixed(1)} ({mentor.review_count})
            </Typography>
          </>
        ) : mentor.trust_label ? (
          <Typography variant="caption" color="text.secondary">
            {mentor.trust_label}
          </Typography>
        ) : null}
      </Box>

      {/* =========================
          5. CTA
      ========================= */}
      <Button
        variant="outlined"
        fullWidth
        onClick={onViewServices}
        sx={{
          textTransform: 'none',
          fontWeight: 600,
        }}
      >
        View Services
      </Button>
    </Box>
  );
};

export default MentorSidebarCard;
