import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Avatar,
  LinearProgress,
  Tooltip,
  Menu,
  MenuItem as MenuItemComponent,
  Alert,
  CircularProgress,
} from '@mui/material';
import {
  Add,
  MoreVert,
  Edit,
  Delete,
  Launch,
  Analytics,
  TrendingUp,
  TrendingDown,
  Search,
  Speed,
  Security,
  ErrorOutline,
  CheckCircle,
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import { projectsService, Project, ProjectCreate, ProjectUpdate, DomainAnalysis } from '../../services/projectsService';

interface ProjectFormData {
  name: string;
  domain: string;
  description: string;
}

const Projects: React.FC = () => {
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [formData, setFormData] = useState<ProjectFormData>({
    name: '',
    domain: '',
    description: '',
  });
  const [domainAnalysis, setDomainAnalysis] = useState<DomainAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Queries
  const { data: projects, isLoading } = useQuery<Project[]>(
    ['projects'],
    () => projectsService.getProjects(true),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  // Mutations
  const createProjectMutation = useMutation(
    (data: ProjectCreate) => projectsService.createProject(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['projects']);
        setCreateDialogOpen(false);
        resetForm();
        toast.success('Project created successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create project');
      },
    }
  );

  const updateProjectMutation = useMutation(
    ({ id, data }: { id: string; data: ProjectUpdate }) =>
      projectsService.updateProject(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['projects']);
        setEditDialogOpen(false);
        setSelectedProject(null);
        resetForm();
        toast.success('Project updated successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update project');
      },
    }
  );

  const deleteProjectMutation = useMutation(
    (id: string) => projectsService.deleteProject(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['projects']);
        toast.success('Project deleted successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to delete project');
      },
    }
  );

  const analyzeDomainMutation = useMutation(
    (projectId: string) => projectsService.analyzeDomain(projectId),
    {
      onSuccess: (data) => {
        setDomainAnalysis(data);
        setIsAnalyzing(false);
        toast.success('Domain analysis completed!');
      },
      onError: (error: any) => {
        setIsAnalyzing(false);
        toast.error('Failed to analyze domain');
      },
    }
  );

  const resetForm = () => {
    setFormData({
      name: '',
      domain: '',
      description: '',
    });
    setDomainAnalysis(null);
  };

  const handleCreateProject = () => {
    if (!formData.name || !formData.domain) {
      toast.error('Please fill in all required fields');
      return;
    }

    createProjectMutation.mutate({
      name: formData.name,
      domain: formData.domain,
      description: formData.description || undefined,
    });
  };

  const handleEditProject = () => {
    if (!selectedProject || !formData.name || !formData.domain) {
      toast.error('Please fill in all required fields');
      return;
    }

    updateProjectMutation.mutate({
      id: selectedProject.id,
      data: {
        name: formData.name,
        domain: formData.domain,
        description: formData.description || undefined,
      },
    });
  };

  const handleDeleteProject = (project: Project) => {
    if (window.confirm(`Are you sure you want to delete "${project.name}"?`)) {
      deleteProjectMutation.mutate(project.id);
    }
    setAnchorEl(null);
  };

  const handleAnalyzeDomain = () => {
    if (!formData.domain) {
      toast.error('Please enter a domain to analyze');
      return;
    }

    setIsAnalyzing(true);
    // For new projects, we'll just analyze the domain directly
    // For existing projects, we'd use the project ID
    toast.info('Domain analysis feature will be available once project is created');
    setIsAnalyzing(false);
  };

  const openEditDialog = (project: Project) => {
    setSelectedProject(project);
    setFormData({
      name: project.name,
      domain: project.domain,
      description: project.description || '',
    });
    setEditDialogOpen(true);
    setAnchorEl(null);
  };

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>, project: Project) => {
    setAnchorEl(event.currentTarget);
    setSelectedProject(project);
  };

  const getStatusColor = (project: Project) => {
    if (!project.stats) return 'default';
    if (project.stats.keywords_count === 0) return 'warning';
    if (project.stats.avg_position <= 10) return 'success';
    if (project.stats.avg_position <= 30) return 'info';
    return 'error';
  };

  const getStatusLabel = (project: Project) => {
    if (!project.stats || project.stats.keywords_count === 0) return 'No Keywords';
    if (project.stats.avg_position <= 10) return 'Excellent';
    if (project.stats.avg_position <= 30) return 'Good';
    return 'Needs Work';
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <>
      <Helmet>
        <title>Projects - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Projects
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Manage your SEO projects and track their performance
            </Typography>
          </Box>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Project
          </Button>
        </Box>

        {/* Projects Overview Cards */}
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
                      {projects?.length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Total Projects
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
                      {projects?.filter(p => p.is_active).length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Active Projects
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
                    <Analytics />
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {projects?.reduce((acc, p) => acc + (p.stats?.keywords_count || 0), 0) || 0}
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
                  <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                    <Speed />
                  </Avatar>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>
                      {projects?.filter(p => p.stats && p.stats.avg_position <= 10).length || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Top Performers
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Projects Table */}
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={600} gutterBottom>
              All Projects
            </Typography>
            
            {projects && projects.length > 0 ? (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Project</TableCell>
                      <TableCell>Domain</TableCell>
                      <TableCell>Keywords</TableCell>
                      <TableCell>Avg Position</TableCell>
                      <TableCell>Top 10</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Last Updated</TableCell>
                      <TableCell align="right">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {projects.map((project) => (
                      <TableRow key={project.id} hover>
                        <TableCell>
                          <Box>
                            <Typography variant="subtitle2" fontWeight={600}>
                              {project.name}
                            </Typography>
                            {project.description && (
                              <Typography variant="body2" color="text.secondary">
                                {project.description}
                              </Typography>
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="body2">
                              {project.domain}
                            </Typography>
                            <IconButton
                              size="small"
                              onClick={() => window.open(`https://${project.domain}`, '_blank')}
                              sx={{ ml: 1 }}
                            >
                              <Launch fontSize="small" />
                            </IconButton>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {project.stats?.keywords_count || 0}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Typography variant="body2">
                              {project.stats?.avg_position ? project.stats.avg_position.toFixed(1) : '-'}
                            </Typography>
                            {project.stats?.avg_position && (
                              project.stats.avg_position <= 10 ? (
                                <TrendingUp color="success" sx={{ ml: 1, fontSize: 16 }} />
                              ) : (
                                <TrendingDown color="error" sx={{ ml: 1, fontSize: 16 }} />
                              )
                            )}
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {project.stats?.top_10_count || 0}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={getStatusLabel(project)}
                            color={getStatusColor(project)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary">
                            {format(new Date(project.updated_at), 'MMM dd, yyyy')}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <IconButton
                            onClick={(e) => handleMenuClick(e, project)}
                            size="small"
                          >
                            <MoreVert />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Box textAlign="center" py={4}>
                <Search sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No projects yet
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create your first project to start tracking SEO performance
                </Typography>
                <Button
                  variant="contained"
                  startIcon={<Add />}
                  onClick={() => setCreateDialogOpen(true)}
                >
                  Create Project
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Actions Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
        >
          <MenuItemComponent onClick={() => openEditDialog(selectedProject!)}>
            <Edit sx={{ mr: 1 }} />
            Edit
          </MenuItemComponent>
          <MenuItemComponent onClick={() => selectedProject && analyzeDomainMutation.mutate(selectedProject.id)}>
            <Analytics sx={{ mr: 1 }} />
            Analyze Domain
          </MenuItemComponent>
          <MenuItemComponent 
            onClick={() => selectedProject && handleDeleteProject(selectedProject)}
            sx={{ color: 'error.main' }}
          >
            <Delete sx={{ mr: 1 }} />
            Delete
          </MenuItemComponent>
        </Menu>

        {/* Create Project Dialog */}
        <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create New Project</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Project Name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Domain"
                    placeholder="example.com"
                    value={formData.domain}
                    onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  />
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  onClick={handleAnalyzeDomain}
                  disabled={!formData.domain || isAnalyzing}
                  startIcon={isAnalyzing ? <CircularProgress size={20} /> : <Analytics />}
                >
                  {isAnalyzing ? 'Analyzing...' : 'Analyze Domain'}
                </Button>
              </Box>

              {domainAnalysis && (
                <Alert severity={domainAnalysis.is_accessible ? "success" : "warning"} sx={{ mt: 2 }}>
                  <Typography variant="subtitle2">
                    Domain Analysis Results
                  </Typography>
                  <Typography variant="body2">
                    Status: {domainAnalysis.is_accessible ? 'Accessible' : 'Not accessible'}
                    {domainAnalysis.has_ssl && ' • SSL Enabled'}
                    {domainAnalysis.response_time_ms && ` • ${domainAnalysis.response_time_ms}ms response time`}
                  </Typography>
                </Alert>
              )}
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setCreateDialogOpen(false); resetForm(); }}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateProject}
              variant="contained"
              disabled={createProjectMutation.isLoading}
            >
              {createProjectMutation.isLoading ? 'Creating...' : 'Create Project'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit Project Dialog */}
        <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Edit Project</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Project Name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Domain"
                    value={formData.domain}
                    onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Description"
                    multiline
                    rows={3}
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
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
              onClick={handleEditProject}
              variant="contained"
              disabled={updateProjectMutation.isLoading}
            >
              {updateProjectMutation.isLoading ? 'Updating...' : 'Update Project'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </>
  );
};

export default Projects;