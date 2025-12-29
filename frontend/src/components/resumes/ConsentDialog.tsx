import React, { useEffect, useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Box,
  Typography,
  Checkbox,
  FormControlLabel,
  Alert,
} from '@mui/material';

interface ConsentDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void> | void;
  title?: string;
}

const ConsentDialog: React.FC<ConsentDialogProps> = ({ open, onClose, onConfirm, title }) => {
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setChecked(false);
      setError(null);
    }
  }, [open]);

  const handleConfirm = async () => {
    if (!checked) {
      setError('Please agree to the AI analysis terms to continue.');
      return;
    }
    try {
      await onConfirm();
    } catch (err: any) {
      setError(err?.message || 'Failed to record consent.');
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>{title || 'AI Resume Analysis Consent'}</DialogTitle>
      <DialogContent>
        <DialogContentText sx={{ mb: 2 }}>
          We use AI to analyze your resume and provide career guidance. Please confirm you understand:
        </DialogContentText>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary">
            - Your resume text will be processed by our AI service for analysis.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            - Results are informational only and not professional advice.
          </Typography>
          <Typography variant="body2" color="text.secondary">
            - You can delete your resume and analysis data at any time.
          </Typography>
        </Box>
        <FormControlLabel
          control={
            <Checkbox
              checked={checked}
              onChange={(event) => setChecked(event.target.checked)}
            />
          }
          label="I agree to the AI analysis terms and data processing."
        />
        {error && <Alert severity="error" sx={{ mt: 2 }}>{error}</Alert>}
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleConfirm} variant="contained">
          Continue
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ConsentDialog;
