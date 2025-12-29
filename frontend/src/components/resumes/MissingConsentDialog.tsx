import React from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
} from '@mui/material';

interface MissingConsentDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void | Promise<void>;
  items: any[];
  error?: string | null;
}

const MissingConsentDialog: React.FC<MissingConsentDialogProps> = ({
  open,
  onClose,
  onConfirm,
  items,
  error,
}) => {
  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Consent Required</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          We need your consent before running AI analysis. Please review the terms below.
        </DialogContentText>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {items.length === 0 ? (
          <Alert severity="warning">No consent details available.</Alert>
        ) : (
          items.map((item) => (
            <Box key={item.id || item.disclaimer_type} sx={{ mb: 2 }}>
              <Typography variant="subtitle1">
                {item.title} (v{item.version})
              </Typography>
              {item.content && (
                <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                  {item.content}
                </Typography>
              )}
            </Box>
          ))
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={onConfirm} variant="contained">
          Agree & Retry
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default MissingConsentDialog;
