import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Paper,
  TextField,
  Button,
  Box,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

interface Problem {
  id: number;
  title: string;
  description: string;
  background?: string;
  user_email?: string;
  analysis_status: 'pending' | 'processing' | 'completed' | 'failed';
  analysis_result?: any;
  created_at: string;
  updated_at?: string;
}

interface AnalysisRequest {
  ai_provider: string;
  model?: string;
  include_hardware_analysis: boolean;
  custom_requirements?: string;
}

const App: React.FC = () => {
  const [problems, setProblems] = useState<Problem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [background, setBackground] = useState('');
  const [userEmail, setUserEmail] = useState('');
  
  // Analysis state
  const [selectedProblem, setSelectedProblem] = useState<Problem | null>(null);
  const [analysisRequest, setAnalysisRequest] = useState<AnalysisRequest>({
    ai_provider: 'openai',
    model: 'gpt-4',
    include_hardware_analysis: true,
    custom_requirements: ''
  });
  const [availableProviders, setAvailableProviders] = useState<string[]>([]);

  useEffect(() => {
    fetchProblems();
    fetchAvailableProviders();
  }, []);

  const fetchProblems = async () => {
    try {
      const response = await axios.get('/api/v1/problems/');
      setProblems(response.data);
    } catch (err) {
      setError('Failed to fetch problems');
    }
  };

  const fetchAvailableProviders = async () => {
    try {
      const response = await axios.get('/api/v1/problems/providers/available');
      setAvailableProviders(response.data.providers);
      if (response.data.default) {
        setAnalysisRequest(prev => ({ ...prev, ai_provider: response.data.default }));
      }
    } catch (err) {
      console.error('Failed to fetch providers');
    }
  };

  const handleSubmitProblem = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const problemData = {
        title,
        description,
        background: background || undefined,
        user_email: userEmail || undefined
      };

      const response = await axios.post('/api/v1/problems/', problemData);
      setProblems(prev => [response.data, ...prev]);
      
      // Reset form
      setTitle('');
      setDescription('');
      setBackground('');
      setUserEmail('');
      
      setSuccess('Problem submitted successfully!');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit problem');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeProblem = async (problemId: number) => {
    setLoading(true);
    setError(null);

    try {
      await axios.post(`/api/v1/problems/${problemId}/analyze`, analysisRequest);
      setSuccess('Analysis started! Check back in a few moments.');
      
      // Refresh problems to update status
      setTimeout(fetchProblems, 1000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to start analysis');
    } finally {
      setLoading(false);
    }
  };

  const handleViewAnalysis = async (problemId: number) => {
    try {
      const response = await axios.get(`/api/v1/problems/${problemId}/analysis`);
      const problem = problems.find(p => p.id === problemId);
      if (problem) {
        setSelectedProblem({ ...problem, analysis_result: response.data.analysis_result });
      }
    } catch (err: any) {
      setError('Failed to fetch analysis result');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'warning';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h3" component="h1" gutterBottom align="center">
        🚀 CodeForge Studio
      </Typography>
      <Typography variant="h6" color="text.secondary" align="center" sx={{ mb: 4 }}>
        AI-powered problem analysis and solution platform
      </Typography>

      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

      {/* Problem Submission Form */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h5" gutterBottom>
          Submit Your Problem
        </Typography>
        <Box component="form" onSubmit={handleSubmitProblem}>
          <TextField
            fullWidth
            label="Problem Title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Problem Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            required
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            multiline
            rows={3}
            label="Background Information (Optional)"
            value={background}
            onChange={(e) => setBackground(e.target.value)}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Your Email (Optional)"
            type="email"
            value={userEmail}
            onChange={(e) => setUserEmail(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !title || !description}
            startIcon={loading ? <CircularProgress size={20} /> : null}
          >
            Submit Problem
          </Button>
        </Box>
      </Paper>

      {/* Analysis Configuration */}
      {availableProviders.length > 0 && (
        <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
          <Typography variant="h6" gutterBottom>
            Analysis Settings
          </Typography>
          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
            <FormControl sx={{ minWidth: 150 }}>
              <InputLabel>AI Provider</InputLabel>
              <Select
                value={analysisRequest.ai_provider}
                onChange={(e) => setAnalysisRequest(prev => ({ ...prev, ai_provider: e.target.value }))}
                label="AI Provider"
              >
                {availableProviders.map(provider => (
                  <MenuItem key={provider} value={provider}>{provider}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Model (Optional)"
              value={analysisRequest.model}
              onChange={(e) => setAnalysisRequest(prev => ({ ...prev, model: e.target.value }))}
              sx={{ minWidth: 150 }}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={analysisRequest.include_hardware_analysis}
                  onChange={(e) => setAnalysisRequest(prev => ({ ...prev, include_hardware_analysis: e.target.checked }))}
                />
              }
              label="Include Hardware Analysis"
            />
          </Box>
        </Paper>
      )}

      {/* Problems List */}
      <Typography variant="h5" gutterBottom>
        Submitted Problems
      </Typography>
      
      {problems.length === 0 ? (
        <Paper elevation={1} sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">
            No problems submitted yet. Submit your first problem above!
          </Typography>
        </Paper>
      ) : (
        problems.map((problem) => (
          <Card key={problem.id} sx={{ mb: 2 }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                <Typography variant="h6" component="h3">
                  {problem.title}
                </Typography>
                <Chip
                  label={problem.analysis_status}
                  color={getStatusColor(problem.analysis_status) as any}
                  size="small"
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                {problem.description.length > 200
                  ? `${problem.description.substring(0, 200)}...`
                  : problem.description}
              </Typography>

              {problem.background && (
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
                  Background: {problem.background}
                </Typography>
              )}

              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                {problem.analysis_status === 'pending' && availableProviders.length > 0 && (
                  <Button
                    variant="outlined"
                    onClick={() => handleAnalyzeProblem(problem.id)}
                    disabled={loading}
                    size="small"
                  >
                    Start Analysis
                  </Button>
                )}
                
                {problem.analysis_status === 'processing' && (
                  <Button
                    variant="outlined"
                    disabled
                    startIcon={<CircularProgress size={16} />}
                    size="small"
                  >
                    Analyzing...
                  </Button>
                )}
                
                {problem.analysis_status === 'completed' && (
                  <Button
                    variant="contained"
                    onClick={() => handleViewAnalysis(problem.id)}
                    size="small"
                  >
                    View Analysis
                  </Button>
                )}
                
                {problem.analysis_status === 'failed' && (
                  <Button
                    variant="outlined"
                    color="error"
                    onClick={() => handleAnalyzeProblem(problem.id)}
                    disabled={loading}
                    size="small"
                  >
                    Retry Analysis
                  </Button>
                )}
              </Box>

              <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
                Submitted: {new Date(problem.created_at).toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        ))
      )}

      {/* Analysis Result Modal/View */}
      {selectedProblem && selectedProblem.analysis_result && (
        <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h5">
              Analysis Result: {selectedProblem.title}
            </Typography>
            <Button onClick={() => setSelectedProblem(null)}>Close</Button>
          </Box>
          
          <Divider sx={{ mb: 2 }} />
          
          {selectedProblem.analysis_result.raw_response ? (
            <Box sx={{ maxHeight: '70vh', overflow: 'auto' }}>
              <ReactMarkdown>{selectedProblem.analysis_result.raw_response}</ReactMarkdown>
            </Box>
          ) : (
            <Typography color="text.secondary">
              Analysis result is not in the expected format.
            </Typography>
          )}
        </Paper>
      )}

      {availableProviders.length === 0 && (
        <Alert severity="warning" sx={{ mt: 2 }}>
          No AI providers are configured. Please set up your API keys in the backend configuration to enable analysis features.
        </Alert>
      )}
    </Container>
  );
};

export default App;