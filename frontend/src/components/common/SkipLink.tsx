import React from 'react';
import { Box } from '@mui/material';

interface SkipLinkProps {
  /** id of the element to jump to. Must exist and be focusable (tabIndex={-1}). */
  targetId?: string;
  label?: string;
}

/**
 * Lets keyboard and screen-reader users bypass the navigation and jump
 * straight to page content (WCAG 2.4.1 Bypass Blocks).
 *
 * Positioned off-screen rather than `display: none` so it stays in the tab
 * order — it becomes visible only once focused, which is the whole point.
 */
const SkipLink: React.FC<SkipLinkProps> = ({
  targetId = 'main-content',
  label = 'Skip to main content',
}) => (
  <Box
    component="a"
    href={`#${targetId}`}
    sx={{
      position: 'absolute',
      left: 8,
      top: -100,
      px: 2,
      py: 1.25,
      borderRadius: 1,
      bgcolor: '#ffffff',
      // 8.6:1 against white — well clear of the 4.5:1 AA threshold.
      color: '#0d47a1',
      fontWeight: 700,
      fontSize: '0.875rem',
      textDecoration: 'none',
      boxShadow: 3,
      transition: 'top 0.15s ease-in',
      zIndex: (theme) => theme.zIndex.tooltip + 1,
      '&:focus': {
        top: 8,
        outline: '3px solid #0d47a1',
        outlineOffset: 2,
      },
    }}
  >
    {label}
  </Box>
);

export default SkipLink;
