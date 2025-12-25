import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  Avatar,
  Typography,
  Box,
  Chip,
  Rating,
  Button,
  Divider,
} from '@mui/material';
import { alpha } from '@mui/material/styles';
import { Mentor } from '../../types';

interface MentorCardProps {
  mentor: Mentor;
  isVisitor?: boolean;
  activeTrack?: string;
}

const MentorCard: React.FC<MentorCardProps> = ({
  mentor,
  isVisitor = false,
  activeTrack,
}) => {
  const navigate = useNavigate();
  /* =========================
     Track prefix labels (P1)
  ========================= */
  const TRACK_PREFIX_LABELS: Record<string, string> = {
    resume_review: 'Resume-focused guidance',
    mock_interview: 'Interview preparation',
    career_switch: 'Career transition support',
    advanced_interview: 'Senior / system design coaching',
  };

  /* =========================
     Contract v1 derived values
  ========================= */
  const {
    display_name,
    badges = [],
    trust_label,
    job_title,
    industry,
    primary_focus,
    session_focus,
    expertise = [],
    rating,
    review_count,
    price_label,
    price_unit,
    cta_label,
  } = mentor;

  const displayExpertise = expertise.slice(0, 2);
  const remainingExpertise = expertise.length - displayExpertise.length;

  /* =========================
     Badge selection (max ONE, priority: top_pick > verified > new)
     Every mentor MUST have at most ONE badge
     New mentors MUST show "New mentor" badge (default if no badges)
  ========================= */
  const displayBadge = (() => {
    if (badges.includes('top_pick')) return { label: 'Top rated', type: 'top_pick' };
    if (badges.includes('verified')) return { label: 'Verified', type: 'verified' };
    if (badges.includes('new')) return { label: 'New mentor', type: 'new' };
    // Default to "New mentor" if no badges (ensures no empty state)
    return { label: 'New mentor', type: 'new' };
  })();

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 3,
        transition: 'all 0.2s ease',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: '0 12px 24px rgba(0,0,0,0.12)',
        },
      }}
    >
      <CardContent sx={{ pt: 4, px: 3, pb: 3, flexGrow: 1, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        {/* 1. Badge (identity mark, absolute positioned, not in layout flow) */}
        <Chip
          label={displayBadge.label}
          size="small"
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            fontSize: '0.7rem',
            height: 20,
            px:'2px',
            zIndex: 1,
            ...(displayBadge.type === 'top_pick' && {
              bgcolor: (theme) => alpha(theme.palette.primary.light, 0.15),
              '& .MuiChip-label': {
                color: 'primary.main',
                fontWeight: 600,
              },
            }),
            ...(displayBadge.type === 'verified' && {
              bgcolor: (theme) => alpha(theme.palette.success.light, 0.2),
              '& .MuiChip-label': {
                color: 'success.main',
                fontWeight: 500,
              },
            }),
            ...(displayBadge.type === 'new' && {
              bgcolor: (theme) => alpha(theme.palette.info.light, 0.2),
              '& .MuiChip-label': {
                color: 'info.main',
                fontWeight: 500,
              },
            }),
          }}
        />

        {/* =========================
            2. Name (single line, highest priority)
        ========================= */}
        <Box display="flex" gap={2} alignItems="flex-start">
          <Avatar
            src={mentor.user?.avatar}
            sx={{
              width: 64,
              height: 64,
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
              flexShrink: 0,
            }}
          >
            {display_name?.[0]}
          </Avatar>

          <Box minWidth={0} flex={1}>
            <Typography
              sx={{
                fontSize: '0.9375rem',
                fontWeight: 600,
                lineHeight: 1.4,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {display_name}
            </Typography>

            {/* 3. Job Title (one full line, directly under name) */}
            {job_title && (
              <Typography
                sx={{
                  fontSize: '0.8125rem',
                  color: 'text.secondary',
                  mt: 0.75,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {job_title}
              </Typography>
            )}

            {/* 4. Company (one full line, directly under job title) */}
            {industry && (
              <Typography
                sx={{
                  fontSize: '0.8125rem',
                  color: 'text.secondary',
                  mt: 0.5,
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {industry}
              </Typography>
            )}
          </Box>
        </Box>

        {/* =========================
            5. Value Proposition (max 2 lines total)
        ========================= */}
        {(mentor.mentor_card || primary_focus) && (
          <Box mt={1.5}>
            {mentor.mentor_card ? (
              <Box>
                {/* P1: Prefix label when activeTrack is set */}
                {activeTrack && TRACK_PREFIX_LABELS[activeTrack] && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      fontSize: '0.7rem',
                      mb: 0.5,
                      textTransform: 'uppercase',
                      letterSpacing: '0.5px',
                    }}
                  >
                    {TRACK_PREFIX_LABELS[activeTrack]}
                  </Typography>
                )}
                <Typography
                  variant="body2"
                  fontWeight={600}
                  sx={{
                    display: '-webkit-box',
                    WebkitLineClamp: 1,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {mentor.mentor_card.line1}
                </Typography>
                {mentor.mentor_card.line2 && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      display: '-webkit-box',
                      WebkitLineClamp: 1,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      mt: 0.5,
                    }}
                  >
                    {mentor.mentor_card.line2}
                  </Typography>
                )}
              </Box>
            ) : (
              <Box>
                <Typography
                  variant="body2"
                  fontWeight={600}
                  sx={{
                    display: '-webkit-box',
                    WebkitLineClamp: 1,
                    WebkitBoxOrient: 'vertical',
                    overflow: 'hidden',
                  }}
                >
                  {primary_focus}
                </Typography>
                {session_focus && (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{
                      display: '-webkit-box',
                      WebkitLineClamp: 1,
                      WebkitBoxOrient: 'vertical',
                      overflow: 'hidden',
                      mt: 0.5,
                    }}
                  >
                    {session_focus}
                  </Typography>
                )}
              </Box>
            )}
          </Box>
        )}

        {/* =========================
            6. Tags (max 2 tags + "+N", single row only)
        ========================= */}
        {expertise.length > 0 && (
          <Box mt={1.5} display="flex" gap={1} flexWrap="nowrap" overflow="hidden">
            {displayExpertise.map((exp) => (
              <Chip
                key={exp}
                label={exp}
                size="small"
                variant="outlined"
                sx={{
                  fontSize: '0.7rem',
                  height: 24,
                  flexShrink: 0,
                  '& .MuiChip-label': {
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    maxWidth: '100px',
                  },
                }}
              />
            ))}
            {remainingExpertise > 0 && (
              <Chip
                label={`+${remainingExpertise}`}
                size="small"
                sx={{
                  fontSize: '0.7rem',
                  height: 24,
                  bgcolor: 'action.hover',
                  flexShrink: 0,
                }}
              />
            )}
          </Box>
        )}

        {/* =========================
            7. Rating (fixed vertical position, one row)
        ========================= */}
        <Box 
          mt={1.5} 
          sx={{ minHeight: '24px' }}
          display="flex" 
          alignItems="center" 
          gap={1}
        >
          {rating !== null && review_count > 0 && (
            <>
              <Rating value={rating} precision={0.5} readOnly size="small" />
              <Typography variant="caption" color="text.secondary">
                {rating.toFixed(1)} ({review_count})
              </Typography>
            </>
          )}
        </Box>

        {/* Spacer to push footer down */}
        <Box flex={1} />
      </CardContent>

      <Divider />

      {/* =========================
          6. Footer (Price + CTA)
      ========================= */}
      <Box
        px={3}
        py={2}
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        sx={{ minHeight: '64px' }}
      >
        {/* Price */}
        <Typography fontWeight={800}>
          {price_label}
          <Typography
            component="span"
            variant="caption"
            color="text.secondary"
            sx={{ ml: 0.5 }}
          >
            / {price_unit}
          </Typography>
        </Typography>

        {/* 8. CTA Button (fixed size, max 2 lines, compact typography) */}
        <Button
          variant={isVisitor ? 'outlined' : 'contained'}
          size="small"
          onClick={() => {
            if (mentor.id) {
              navigate(`/student/mentors/${mentor.id}`);
            }
          }}
          sx={{
            borderRadius: 2,
            textTransform: 'none',
            fontWeight: 600,
            fontSize: '0.65rem',
            px: 2.5,
            width: '150px',
            height: '40px',
            '& .MuiButton-label': {
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              lineHeight: 1.15,
              textAlign: 'center',
            },
          }}
        >
          {cta_label}
        </Button>
      </Box>
    </Card>
  );
};

export default MentorCard;
