import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Chip,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  InputAdornment,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Menu,
  MenuItem as MenuItemComponent,
  Alert,
  CircularProgress,
  LinearProgress,
  Tooltip,
  Autocomplete,
} from '@mui/material';
import {
  Add,
  Search,
  TrendingUp,
  TrendingDown,
  Remove,
  MoreVert,
  FilterList,
  Download,
  Upload,
  Edit,
  Delete,
  Analytics,
  Timeline,
  Info,
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import { keywordsService, Keyword, KeywordCreate, KeywordUpdate, KeywordAnalysis } from '../../services/keywordsService';
import { projectsService, Project } from '../../services/projectsService';

interface KeywordFormData {
  keyword: string;
  project_id: string;
  target_position: number | '';
  priority: string;
  tags: string[];
}

const Keywords: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPriority, setSelectedPriority] = useState<string>('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [bulkDialogOpen, setBulkDialogOpen] = useState(false);
  const [analyzeDialogOpen, setAnalyzeDialogOpen] = useState(false);
  const [selectedKeyword, setSelectedKeyword] = useState<Keyword | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [formData, setFormData] = useState<KeywordFormData>({
    keyword: '',
    project_id: '',
    target_position: '',
    priority: 'medium',
    tags: [],
  });
  const [bulkKeywords, setBulkKeywords] = useState('');
  const [analysisKeyword, setAnalysisKeyword] = useState('');
  const [keywordAnalysis, setKeywordAnalysis] = useState<KeywordAnalysis | null>(null);

  // Queries
  const { data: projects } = useQuery<Project[]>(
    ['projects'],
    () => projectsService.getProjects(false),
    {
      onSuccess: (data) => {
        if (data.length > 0 && !selectedProject) {
          setSelectedProject(data[0].id);
        }
      },
    }
  );

  const { data: keywords, isLoading: keywordsLoading } = useQuery<Keyword[]>(
    ['keywords', selectedProject, searchTerm, selectedPriority],
    () => keywordsService.getKeywords(selectedProject, 0, 100, searchTerm || undefined, selectedPriority || undefined),
    {
      enabled: !!selectedProject,
      refetchInterval: 60000, // Refetch every minute
    }
  );

  // Mutations
  const createKeywordMutation = useMutation(
    (data: KeywordCreate) => keywordsService.createKeyword(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['keywords']);
        setCreateDialogOpen(false);
        resetForm();
        toast.success('Keyword added successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to add keyword');
      },
    }
  );

  const updateKeywordMutation = useMutation(
    ({ id, data }: { id: string; data: KeywordUpdate }) =>
      keywordsService.updateKeyword(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['keywords']);
        setEditDialogOpen(false);
        setSelectedKeyword(null);
        resetForm();
        toast.success('Keyword updated successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update keyword');
      },
    }
  );

  const deleteKeywordMutation = useMutation(
    (id: string) => keywordsService.deleteKeyword(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['keywords']);
        toast.success('Keyword deleted successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to delete keyword');
      },
    }
  );

  const bulkAddMutation = useMutation(
    (data: { keywords: string[]; project_id: string }) =>
      keywordsService.bulkAddKeywords(data),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['keywords']);
        setBulkDialogOpen(false);
        setBulkKeywords('');
        toast.success(`Added ${data.added} keywords successfully!`);
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to add keywords');
      },
    }
  );

  const analyzeKeywordMutation = useMutation(
    (keyword: string) => keywordsService.analyzeKeyword(keyword),
    {
      onSuccess: (data) => {
        setKeywordAnalysis(data);
        toast.success('Keyword analysis completed!');
      },
      onError: (error: any) => {
        toast.error('Failed to analyze keyword');
      },
    }
  );

  const resetForm = () => {
    setFormData({
      keyword: '',
      project_id: selectedProject,
      target_position: '',
      priority: 'medium',
      tags: [],
    });
  };

  const handleCreateKeyword = () => {
    if (!formData.keyword || !formData.project_id) {
      toast.error('Please fill in all required fields');
      return;
    }

    createKeywordMutation.mutate({
      keyword: formData.keyword,
      project_id: formData.project_id,
      target_position: formData.target_position ? Number(formData.target_position) : undefined,
      priority: formData.priority,
      tags: formData.tags,
    });
  };

  const handleEditKeyword = () => {
    if (!selectedKeyword) {
      toast.error('No keyword selected');
      return;
    }

    updateKeywordMutation.mutate({
      id: selectedKeyword.id,
      data: {
        target_position: formData.target_position ? Number(formData.target_position) : undefined,
        priority: formData.priority,
        tags: formData.tags,
      },
    });
  };

  const handleDeleteKeyword = (keyword: Keyword) => {
    if (window.confirm(`Are you sure you want to delete "${keyword.keyword}"?`)) {
      deleteKeywordMutation.mutate(keyword.id);
    }
    setAnchorEl(null);
  };

  const handleBulkAdd = () => {
    if (!bulkKeywords.trim() || !selectedProject) {
      toast.error('Please enter keywords and select a project');
      return;
    }

    const keywordList = bulkKeywords
      .split('\n')
      .map(k => k.trim())
      .filter(k => k.length > 0);

    if (keywordList.length === 0) {
      toast.error('Please enter at least one keyword');
      return;
    }

    bulkAddMutation.mutate({
      keywords: keywordList,
      project_id: selectedProject,
    });
  };

  const handleAnalyzeKeyword = () => {
    if (!analysisKeyword.trim()) {
      toast.error('Please enter a keyword to analyze');
      return;
    }

    analyzeKeywordMutation.mutate(analysisKeyword);
  };

  const openEditDialog = (keyword: Keyword) => {
    setSelectedKeyword(keyword);
    setFormData({
      keyword: keyword.keyword,
      project_id: keyword.project_id || selectedProject,
      target_position: keyword.target_position || '',
      priority: keyword.priority,
      tags: keyword.tags || [],
    });
    setEditDialogOpen(true);
    setAnchorEl(null);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, keyword: Keyword) => {
    setAnchorEl(event.currentTarget);
    setSelectedKeyword(keyword);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      case 'low':
        return 'success';
      default:
        return 'default';
    }
  };

  const getPositionChange = (current?: number, previous?: number) => {
    if (!current || !previous) return { value: 0, icon: <Remove />, color: 'text.secondary' };
    
    const change = previous - current;
    return {
      value: change,
      icon: change > 0 ? <TrendingUp /> : change < 0 ? <TrendingDown /> : <Remove />,
      color: change > 0 ? 'success.main' : change < 0 ? 'error.main' : 'text.secondary',
    };
  };

  // Calculate statistics
  const totalKeywords = keywords?.length || 0;
  const avgPosition = keywords?.length 
    ? keywords.filter(k => k.current_position).reduce((acc, k) => acc + (k.current_position || 0), 0) / keywords.filter(k => k.current_position).length
    : 0;
  const topTenCount = keywords?.filter(k => k.current_position && k.current_position <= 10).length || 0;
  const estimatedTraffic = keywords?.reduce((acc, k) => {
    if (!k.current_position || !k.search_volume) return acc;
    // Simplified traffic estimation based on position
    const ctr = k.current_position <= 3 ? 0.3 : k.current_position <= 10 ? 0.1 : 0.02;
    return acc + (k.search_volume * ctr);
  }, 0) || 0;

  useEffect(() => {
    setFormData(prev => ({ ...prev, project_id: selectedProject }));
  }, [selectedProject]);

  if (!projects || projects.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <Search sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create a project first to start tracking keywords
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <>
      <Helmet>
        <title>Keywords - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Keywords
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Track and analyze your keyword performance
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button variant="outlined" startIcon={<Analytics />} onClick={() => setAnalyzeDialogOpen(true)}>
              Analyze
            </Button>
            <Button variant="outlined" startIcon={<Upload />} onClick={() => setBulkDialogOpen(true)}>
              Bulk Add
            </Button>
            <Button variant="contained" startIcon={<Add />} onClick={() => setCreateDialogOpen(true)}>
              Add Keyword
            </Button>
          </Box>
        </Box>

        {/* Project Selector */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <FormControl sx={{ minWidth: 200 }}>
              <InputLabel>Project</InputLabel>
              <Select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                label="Project"
              >
                {projects.map((project) => (
                  <MenuItem key={project.id} value={project.id}>
                    {project.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </CardContent>
        </Card>

        {/* Summary Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <Search />
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {totalKeywords}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Keywords
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                    <TrendingUp />
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {avgPosition ? avgPosition.toFixed(1) : '-'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Avg Position
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                    <Search />
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {topTenCount}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Top 10
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                    <TrendingUp />
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {Math.round(estimatedTraffic)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Est. Traffic
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
              <TextField
                placeholder="Search keywords..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ flex: 1 }}
              />
              <FormControl sx={{ minWidth: 120 }}>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={selectedPriority}
                  onChange={(e) => setSelectedPriority(e.target.value)}
                  label="Priority"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="medium">Medium</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Box>
          </CardContent>
        </Card>

        {/* Keywords Table */}
        <Card>
          {keywordsLoading && <LinearProgress />}
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Keyword</TableCell>
                  <TableCell align="center">Position</TableCell>
                  <TableCell align="right">Search Volume</TableCell>
                  <TableCell align="right">Difficulty</TableCell>
                  <TableCell align="right">CPC</TableCell>
                  <TableCell align="center">Target</TableCell>
                  <TableCell align="center">Priority</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {keywords && keywords.length > 0 ? (
                  keywords.map((keyword) => (
                    <TableRow key={keyword.id} hover>
                      <TableCell>
                        <Box>
                          <Typography variant="body2" fontWeight={600}>
                            {keyword.keyword}
                          </Typography>
                          {keyword.tags && keyword.tags.length > 0 && (
                            <Box sx={{ mt: 0.5 }}>
                              {keyword.tags.slice(0, 2).map((tag, index) => (
                                <Chip
                                  key={index}
                                  label={tag}
                                  size="small"
                                  variant="outlined"
                                  sx={{ mr: 0.5, fontSize: '0.75rem' }}
                                />
                              ))}
                              {keyword.tags.length > 2 && (
                                <Chip
                                  label={`+${keyword.tags.length - 2}`}
                                  size="small"
                                  variant="outlined"
                                  sx={{ fontSize: '0.75rem' }}
                                />
                              )}
                            </Box>
                          )}
                        </Box>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" fontWeight={600}>
                          {keyword.current_position || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {keyword.search_volume ? keyword.search_volume.toLocaleString() : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {keyword.difficulty ? `${keyword.difficulty}%` : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {keyword.cpc ? `$${keyword.cpc.toFixed(2)}` : '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2">
                          {keyword.target_position || '-'}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Chip
                          label={keyword.priority}
                          size="small"
                          color={getPriorityColor(keyword.priority) as any}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell align="center">
                        <IconButton
                          size="small"
                          onClick={(e) => handleMenuClick(e, keyword)}
                        >
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={8} align="center" sx={{ py: 4 }}>
                      <Search sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                      <Typography variant="h6" color="text.secondary" gutterBottom>
                        No keywords found
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Add your first keyword to start tracking rankings
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>

        {/* Actions Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItemComponent onClick={() => openEditDialog(selectedKeyword!)}>
            <Edit sx={{ mr: 1 }} />
            Edit
          </MenuItemComponent>
          <MenuItemComponent onClick={() => setAnchorEl(null)}>
            <Timeline sx={{ mr: 1 }} />
            View Rankings
          </MenuItemComponent>
          <MenuItemComponent 
            onClick={() => selectedKeyword && handleDeleteKeyword(selectedKeyword)}
            sx={{ color: 'error.main' }}
          >
            <Delete sx={{ mr: 1 }} />
            Delete
          </MenuItemComponent>
        </Menu>

        {/* Create Keyword Dialog */}
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Add New Keyword</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Keyword"
                    value={formData.keyword}
                    onChange={(e) => setFormData({ ...formData, keyword: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Target Position"
                    type="number"
                    value={formData.target_position}
                    onChange={(e) => setFormData({ ...formData, target_position: e.target.value as any })}
                    inputProps={{ min: 1, max: 100 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Priority</InputLabel>
                    <Select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      label="Priority"
                    >
                      <MenuItem value="high">High</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="low">Low</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Autocomplete
                    multiple
                    options={[]}
                    freeSolo
                    value={formData.tags}
                    onChange={(event, newValue) => {
                      setFormData({ ...formData, tags: newValue });
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Tags"
                        placeholder="Add tags"
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setCreateDialogOpen(false); resetForm(); }}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateKeyword}
              variant="contained"
              disabled={createKeywordMutation.isLoading}
            >
              {createKeywordMutation.isLoading ? 'Adding...' : 'Add Keyword'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit Keyword Dialog */}
        <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Edit Keyword</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Keyword"
                    value={formData.keyword}
                    disabled
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Target Position"
                    type="number"
                    value={formData.target_position}
                    onChange={(e) => setFormData({ ...formData, target_position: e.target.value as any })}
                    inputProps={{ min: 1, max: 100 }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Priority</InputLabel>
                    <Select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      label="Priority"
                    >
                      <MenuItem value="high">High</MenuItem>
                      <MenuItem value="medium">Medium</MenuItem>
                      <MenuItem value="low">Low</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Autocomplete
                    multiple
                    options={[]}
                    freeSolo
                    value={formData.tags}
                    onChange={(event, newValue) => {
                      setFormData({ ...formData, tags: newValue });
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        label="Tags"
                        placeholder="Add tags"
                      />
                    )}
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setEditDialogOpen(false); resetForm(); }}>
              Cancel
            </Button>
            <Button
              onClick={handleEditKeyword}
              variant="contained"
              disabled={updateKeywordMutation.isLoading}
            >
              {updateKeywordMutation.isLoading ? 'Updating...' : 'Update Keyword'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Bulk Add Dialog */}
        <Dialog open={bulkDialogOpen} onClose={() => setBulkDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Bulk Add Keywords</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Enter one keyword per line:
              </Typography>
              <TextField
                fullWidth
                multiline
                rows={8}
                placeholder="keyword 1&#10;keyword 2&#10;keyword 3"
                value={bulkKeywords}
                onChange={(e) => setBulkKeywords(e.target.value)}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setBulkDialogOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleBulkAdd}
              variant="contained"
              disabled={bulkAddMutation.isLoading}
            >
              {bulkAddMutation.isLoading ? 'Adding...' : 'Add Keywords'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Analyze Keyword Dialog */}
        <Dialog open={analyzeDialogOpen} onClose={() => setAnalyzeDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Analyze Keyword</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <TextField
                fullWidth
                label="Keyword to Analyze"
                value={analysisKeyword}
                onChange={(e) => setAnalysisKeyword(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                variant="outlined"
                onClick={handleAnalyzeKeyword}
                disabled={analyzeKeywordMutation.isLoading}
                startIcon={analyzeKeywordMutation.isLoading ? <CircularProgress size={20} /> : <Analytics />}
                sx={{ mb: 2 }}
              >
                {analyzeKeywordMutation.isLoading ? 'Analyzing...' : 'Analyze'}
              </Button>

              {keywordAnalysis && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Analysis Results for "{keywordAnalysis.keyword}"
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>Search Volume:</strong> {keywordAnalysis.search_volume.toLocaleString()}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>Difficulty:</strong> {keywordAnalysis.difficulty}%
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>CPC:</strong> ${keywordAnalysis.cpc.toFixed(2)}
                      </Typography>
                    </Grid>
                    <Grid item xs={6} sm={3}>
                      <Typography variant="body2">
                        <strong>Competition:</strong> {keywordAnalysis.competition}%
                      </Typography>
                    </Grid>
                  </Grid>
                </Alert>
              )}
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAnalyzeDialogOpen(false)}>
              Close
            </Button>
            {keywordAnalysis && (
              <Button
                variant="contained"
                onClick={() => {
                  setFormData(prev => ({ ...prev, keyword: keywordAnalysis.keyword }));
                  setAnalyzeDialogOpen(false);
                  setCreateDialogOpen(true);
                }}
              >
                Add This Keyword
              </Button>
            )}
          </DialogActions>
        </Dialog>
      </Box>
    </>
  );
};

export default Keywords;