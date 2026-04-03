import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Box,
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Paper,
  Alert,
  Chip,
  Button,
  CircularProgress,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  LinearProgress,
  Divider,
  Stack,
} from '@mui/material';
import {
  ArrowBack,
  WorkspacePremium,
  WarningAmber,
  TipsAndUpdates,
  Stars,
  Refresh,
  Analytics,
} from '@mui/icons-material';
import { AppDispatch, RootState } from '../../store';
import { fetchResumes } from '../../store/slices/resumeSlice';
import apiClient from '../../services/api/client';

// ── Types ─────────────────────────────────────────────────────────────────────

interface HardGap   { issue: string; reason: string; }
interface SoftGap   { issue: string; suggestion: string; }
interface Strength  { point: string; why: string; }
interface Rec       { action: string; priority: 'high' | 'medium' | 'low'; }

interface MatchAnalysis {
  match_score: number;
  hard_gaps:       HardGap[];
  soft_gaps:       SoftGap[];
  strengths:       Strength[];
  recommendations: Rec[];
}

interface MatchResult {
  resume_id:    number;
  resume_title: string;
  analysis:     MatchAnalysis;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const scoreColor = (score: number) =>
  score >= 70 ? '#22c55e' : score >= 40 ? '#f59e0b' : '#ef4444';

const scoreLabel = (score: number) =>
  score >= 70 ? 'Strong Match' : score >= 40 ? 'Partial Match' : 'Weak Match';

const priorityColor = (p: string): 'error' | 'warning' | 'success' =>
  p === 'high' ? 'error' : p === 'medium' ? 'warning' : 'success';

// ── Component ─────────────────────────────────────────────────────────────────

const JDMatchPage: React.FC = () => {
  const dispatch    = useDispatch<AppDispatch>();
  const navigate    = useNavigate();
  const [params]    = useSearchParams();
  const { resumes } = useSelector((state: RootState) => state.resumes);

  const [resumeId,  setResumeId]  = useState<number | ''>('');
  const [jd,        setJd]        = useState('');
  const [loading,   setLoading]   = useState(false);
  const [result,    setResult]    = useState<MatchResult | null>(null);
  const [error,     setError]     = useState<string | null>(null);

  // Load resumes on mount; pre-select from URL param
  useEffect(() => {
    dispatch(fetchResumes());
  }, [dispatch]);

  useEffect(() => {
    const id = params.get('resume_id');
    if (id) setResumeId(Number(id));
  }, [params]);

  const canSubmit = resumeId !== '' && jd.trim().length >= 50 && !loading;

  const handleAnalyze = async () => {
    if (!canSubmit) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await apiClient.post('/ats-signals/jd-match/', {
        resume_id:       resumeId,
        job_description: jd.trim(),
      });
      setResult(res.data);
    } catch (e: any) {
      const msg =
        e?.response?.data?.error ||
        e?.response?.data?.detail ||
        e?.message ||
        'Analysis failed. Make sure AI Bus is ON and try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setJd('');
  };

  // ── Result view ─────────────────────────────────────────────────────────────

  if (result) {
    const { analysis, resume_title } = result;
    const sc = analysis.match_score;
    const color = scoreColor(sc);

    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>

        {/* Toolbar */}
        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 3 }}>
          <Button
            startIcon={<ArrowBack />}
            onClick={() => navigate('/student/resumes')}
            size="small"
          >
            My Resumes
          </Button>
          <Button
            startIcon={<Refresh />}
            onClick={handleReset}
            variant="outlined"
            size="small"
          >
            Analyze Another
          </Button>
        </Stack>

        {/* Score hero */}
        <Paper
          elevation={0}
          sx={{
            p: 4,
            mb: 3,
            border: '1px solid',
            borderColor: 'divider',
            borderRadius: 2,
          }}
        >
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4} sx={{ textAlign: 'center' }}>
              {/* Big score circle */}
              <Box
                sx={{
                  width: 140,
                  height: 140,
                  borderRadius: '50%',
                  border: `6px solid ${color}`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  mx: 'auto',
                  mb: 1,
                }}
              >
                <Typography
                  variant="h3"
                  sx={{ fontWeight: 800, color, lineHeight: 1 }}
                >
                  {sc}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  / 100
                </Typography>
              </Box>
              <Chip
                label={scoreLabel(sc)}
                size="small"
                sx={{
                  bgcolor: color,
                  color: 'white',
                  fontWeight: 700,
                  fontSize: '0.75rem',
                }}
              />
            </Grid>

            <Grid item xs={12} md={8}>
              <Typography variant="h5" fontWeight={700} gutterBottom>
                {resume_title}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                AI match score based on GPT-4o-mini analysis
              </Typography>
              <LinearProgress
                variant="determinate"
                value={sc}
                sx={{
                  height: 10,
                  borderRadius: 5,
                  bgcolor: 'grey.200',
                  '& .MuiLinearProgress-bar': { bgcolor: color, borderRadius: 5 },
                }}
              />
              <Stack direction="row" spacing={3} sx={{ mt: 1.5 }}>
                <Typography variant="caption" color="text.secondary">
                  Hard gaps: <strong>{analysis.hard_gaps.length}</strong>
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Soft gaps: <strong>{analysis.soft_gaps.length}</strong>
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Strengths: <strong>{analysis.strengths.length}</strong>
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Actions: <strong>{analysis.recommendations.length}</strong>
                </Typography>
              </Stack>
            </Grid>
          </Grid>
        </Paper>

        <Grid container spacing={3}>

          {/* Hard Gaps */}
          {analysis.hard_gaps.length > 0 && (
            <Grid item xs={12} md={6}>
              <Typography
                variant="subtitle1"
                fontWeight={700}
                sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.75 }}
              >
                <WarningAmber sx={{ color: '#ef4444', fontSize: '1.1rem' }} />
                Hard Gaps ({analysis.hard_gaps.length})
              </Typography>
              <Stack spacing={1.5}>
                {analysis.hard_gaps.map((g, i) => (
                  <Card
                    key={i}
                    elevation={0}
                    sx={{ borderLeft: '4px solid #ef4444', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}
                  >
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        {g.issue}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {g.reason}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Grid>
          )}

          {/* Soft Gaps */}
          {analysis.soft_gaps.length > 0 && (
            <Grid item xs={12} md={6}>
              <Typography
                variant="subtitle1"
                fontWeight={700}
                sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.75 }}
              >
                <TipsAndUpdates sx={{ color: '#f59e0b', fontSize: '1.1rem' }} />
                Soft Gaps ({analysis.soft_gaps.length})
              </Typography>
              <Stack spacing={1.5}>
                {analysis.soft_gaps.map((g, i) => (
                  <Card
                    key={i}
                    elevation={0}
                    sx={{ borderLeft: '4px solid #f59e0b', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}
                  >
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        {g.issue}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        💡 {g.suggestion}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Grid>
          )}

          {/* Strengths */}
          {analysis.strengths.length > 0 && (
            <Grid item xs={12} md={6}>
              <Typography
                variant="subtitle1"
                fontWeight={700}
                sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.75 }}
              >
                <Stars sx={{ color: '#22c55e', fontSize: '1.1rem' }} />
                Strengths ({analysis.strengths.length})
              </Typography>
              <Stack spacing={1.5}>
                {analysis.strengths.map((s, i) => (
                  <Card
                    key={i}
                    elevation={0}
                    sx={{ borderLeft: '4px solid #22c55e', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}
                  >
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Typography variant="body2" fontWeight={600} gutterBottom>
                        {s.point}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {s.why}
                      </Typography>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Grid>
          )}

          {/* Recommendations */}
          {analysis.recommendations.length > 0 && (
            <Grid item xs={12} md={6}>
              <Typography
                variant="subtitle1"
                fontWeight={700}
                sx={{ mb: 1.5, display: 'flex', alignItems: 'center', gap: 0.75 }}
              >
                <WorkspacePremium sx={{ color: '#3b82f6', fontSize: '1.1rem' }} />
                Recommendations ({analysis.recommendations.length})
              </Typography>
              <Stack spacing={1.5}>
                {analysis.recommendations.map((r, i) => (
                  <Card
                    key={i}
                    elevation={0}
                    sx={{ borderLeft: '4px solid #3b82f6', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}
                  >
                    <CardContent sx={{ py: 1.5, '&:last-child': { pb: 1.5 } }}>
                      <Stack direction="row" spacing={1} alignItems="flex-start">
                        <Box sx={{ flex: 1 }}>
                          <Typography variant="body2" fontWeight={600}>
                            {r.action}
                          </Typography>
                        </Box>
                        <Chip
                          label={r.priority}
                          size="small"
                          color={priorityColor(r.priority)}
                          variant="outlined"
                          sx={{ fontWeight: 700, fontSize: '0.65rem', flexShrink: 0 }}
                        />
                      </Stack>
                    </CardContent>
                  </Card>
                ))}
              </Stack>
            </Grid>
          )}

        </Grid>

        <Alert severity="info" sx={{ mt: 4 }}>
          This analysis is generated by AI and is for guidance only. Results may vary based on recruiter preferences and company culture.
        </Alert>

      </Container>
    );
  }

  // ── Input form ───────────────────────────────────────────────────────────────

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>

      <Button
        startIcon={<ArrowBack />}
        onClick={() => navigate('/student/resumes')}
        size="small"
        sx={{ mb: 3 }}
      >
        My Resumes
      </Button>

      <Box sx={{ mb: 4 }}>
        <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 0.5 }}>
          <Analytics sx={{ color: 'primary.main', fontSize: '1.75rem' }} />
          <Typography variant="h4" fontWeight={700}>
            Resume × JD Match
          </Typography>
        </Stack>
        <Typography variant="body2" color="text.secondary">
          Select a resume and paste a job description to get an AI-powered gap analysis.
        </Typography>
      </Box>

      <Divider sx={{ mb: 4 }} />

      <Stack spacing={3}>

        {/* Resume selector */}
        <FormControl fullWidth>
          <InputLabel id="resume-select-label">Select Resume</InputLabel>
          <Select
            labelId="resume-select-label"
            value={resumeId}
            label="Select Resume"
            onChange={(e) => setResumeId(e.target.value as number)}
          >
            {resumes.length === 0 && (
              <MenuItem disabled value="">
                No resumes uploaded yet
              </MenuItem>
            )}
            {resumes.map((r) => (
              <MenuItem key={r.id} value={r.id}>
                <Stack direction="row" spacing={1.5} alignItems="center">
                  <Typography variant="body2">{r.title}</Typography>
                  <Chip
                    label={r.status}
                    size="small"
                    color={
                      r.status === 'analyzed'  ? 'success' :
                      r.status === 'analyzing' ? 'warning' :
                      r.status === 'failed'    ? 'error'   : 'default'
                    }
                    sx={{ height: 20, fontSize: '0.65rem' }}
                  />
                </Stack>
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* JD textarea */}
        <TextField
          label="Job Description"
          multiline
          minRows={6}
          fullWidth
          value={jd}
          onChange={(e) => setJd(e.target.value)}
          placeholder="Paste the full job description here (min 50 characters)..."
          helperText={
            jd.length > 0 && jd.length < 50
              ? `${50 - jd.length} more characters needed`
              : jd.length >= 50
              ? `${jd.length} characters`
              : undefined
          }
          error={jd.length > 0 && jd.length < 50}
        />

        {/* Error */}
        {error && (
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Submit */}
        <Box>
          <Button
            variant="contained"
            size="large"
            onClick={handleAnalyze}
            disabled={!canSubmit}
            startIcon={loading ? <CircularProgress size={18} color="inherit" /> : <Analytics />}
            sx={{ minWidth: 180 }}
          >
            {loading ? 'Analyzing…' : 'Analyze Match'}
          </Button>
          {loading && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              GPT-4o-mini is analyzing your resume against the job description…
            </Typography>
          )}
        </Box>

      </Stack>
    </Container>
  );
};

export default JDMatchPage;
