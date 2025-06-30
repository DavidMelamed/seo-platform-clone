import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Divider,
  Tabs,
  Tab,
  Paper,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Tooltip,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  AutoAwesome,
  Add,
  Edit,
  Delete,
  PlayArrow,
  Stop,
  Schedule,
  History,
  Settings,
  CheckCircle,
  Error,
  Warning,
  Refresh,
  Speed,
  Timeline,
  Description,
  Build,
  ExpandMore,
  FileCopy,
  Tune,
  Assessment,
  AccessTime,
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import {
  automationService,
  Workflow,
  WorkflowCreate,
  WorkflowUpdate,
  WorkflowExecution,
  WorkflowTemplate,
  AutomationStats,
  ActionType,
  WorkflowStatus,
  WorkflowStep,
} from '../../services/automationService';
import { projectsService, Project } from '../../services/projectsService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`automation-tabpanel-${index}`}
      aria-labelledby={`automation-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const Automation: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editingWorkflow, setEditingWorkflow] = useState<Workflow | null>(null);
  const [newWorkflow, setNewWorkflow] = useState<WorkflowCreate>({
    name: '',
    description: '',
    project_id: '',
    steps: [],
    enabled: true,
    tags: [],
  });
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedTemplate, setSelectedTemplate] = useState<WorkflowTemplate | null>(null);

  const queryClient = useQueryClient();

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

  const { data: workflows, isLoading: workflowsLoading } = useQuery<Workflow[]>(
    ['automation-workflows', selectedProject],
    () => automationService.getWorkflows(selectedProject),
    {
      enabled: !!selectedProject,
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const { data: executions, isLoading: executionsLoading } = useQuery<WorkflowExecution[]>(
    ['automation-executions', selectedProject],
    () => automationService.getWorkflowExecutions(selectedProject, 100),
    {
      enabled: !!selectedProject && selectedTab === 1,
      refetchInterval: 10000, // Refetch every 10 seconds for real-time updates
    }
  );

  const { data: templates } = useQuery<{ templates: WorkflowTemplate[] }>(
    ['automation-templates'],
    () => automationService.getWorkflowTemplates()
  );

  const { data: stats } = useQuery<AutomationStats>(
    ['automation-stats', selectedProject],
    () => automationService.getAutomationStats(selectedProject),
    {
      enabled: !!selectedProject,
      refetchInterval: 60000, // Refetch every minute
    }
  );

  // Mutations
  const createWorkflowMutation = useMutation(
    (workflowData: WorkflowCreate) => automationService.createWorkflow(workflowData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['automation-workflows', selectedProject]);
        queryClient.invalidateQueries(['automation-stats', selectedProject]);
        setCreateDialogOpen(false);
        setNewWorkflow({
          name: '',
          description: '',
          project_id: selectedProject,
          steps: [],
          enabled: true,
          tags: [],
        });
        toast.success('Workflow created successfully');
      },
      onError: () => {
        toast.error('Failed to create workflow');
      },
    }
  );

  const executeWorkflowMutation = useMutation(
    ({ projectId, workflowId }: { projectId: string; workflowId: string }) =>
      automationService.executeWorkflow(projectId, workflowId),
    {
      onSuccess: (data) => {
        queryClient.invalidateQueries(['automation-executions', selectedProject]);
        toast.success(`Workflow execution started: ${data.execution_id}`);
      },
      onError: () => {
        toast.error('Failed to execute workflow');
      },
    }
  );

  const deleteWorkflowMutation = useMutation(
    ({ projectId, workflowId }: { projectId: string; workflowId: string }) =>
      automationService.deleteWorkflow(projectId, workflowId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['automation-workflows', selectedProject]);
        queryClient.invalidateQueries(['automation-stats', selectedProject]);
        toast.success('Workflow deleted successfully');
      },
      onError: () => {
        toast.error('Failed to delete workflow');
      },
    }
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleCreateWorkflow = () => {
    setCreateDialogOpen(true);
    setNewWorkflow({
      name: '',
      description: '',
      project_id: selectedProject,
      steps: [],
      enabled: true,
      tags: [],
    });
  };

  const handleSaveWorkflow = () => {
    if (!newWorkflow.name || !newWorkflow.description || newWorkflow.steps.length === 0) {
      toast.error('Please fill in all required fields and add at least one step');
      return;
    }

    createWorkflowMutation.mutate(newWorkflow);
  };

  const handleExecuteWorkflow = (workflowId: string) => {
    executeWorkflowMutation.mutate({ projectId: selectedProject, workflowId });
  };

  const handleDeleteWorkflow = (workflowId: string) => {
    if (window.confirm('Are you sure you want to delete this workflow?')) {
      deleteWorkflowMutation.mutate({ projectId: selectedProject, workflowId });
    }
  };

  const handleUseTemplate = (template: WorkflowTemplate) => {
    setSelectedTemplate(template);
    setNewWorkflow({
      name: template.name,
      description: template.description,
      project_id: selectedProject,
      steps: template.steps,
      schedule: template.schedule,
      enabled: true,
      tags: [template.category],
    });
    setCreateDialogOpen(true);
  };

  const addWorkflowStep = () => {
    const newStep: WorkflowStep = {
      name: '',
      action: ActionType.KEYWORD_RESEARCH,
      parameters: {},
      retry_count: 0,
      timeout_seconds: 300,
    };
    setNewWorkflow({
      ...newWorkflow,
      steps: [...newWorkflow.steps, newStep],
    });
  };

  const updateWorkflowStep = (index: number, step: WorkflowStep) => {
    const updatedSteps = [...newWorkflow.steps];
    updatedSteps[index] = step;
    setNewWorkflow({
      ...newWorkflow,
      steps: updatedSteps,
    });
  };

  const removeWorkflowStep = (index: number) => {
    setNewWorkflow({
      ...newWorkflow,
      steps: newWorkflow.steps.filter((_, i) => i !== index),
    });
  };

  if (!projects || projects.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <AutoAwesome sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create a project first to set up automation workflows
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <>
      <Helmet>
        <title>Automation - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              SEO Automation
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Automate your SEO workflows and tasks with intelligent scheduling
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
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
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={handleCreateWorkflow}
              disabled={!selectedProject}
            >
              Create Workflow
            </Button>
          </Box>
        </Box>

        {/* Stats Cards */}
        {stats && (
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                      <Build />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {stats.total_workflows}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Workflows
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
                      <PlayArrow />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {stats.active_workflows}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Active Workflows
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
                      <Timeline />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {stats.executions_today}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Executions Today
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
                      <Assessment />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {stats.success_rate}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Success Rate
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={selectedTab} onChange={handleTabChange} aria-label="automation tabs">
            <Tab label="Workflows" icon={<Build />} />
            <Tab label="Executions" icon={<History />} />
            <Tab label="Templates" icon={<Description />} />
            <Tab label="Schedule" icon={<Schedule />} />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={selectedTab} index={0}>
          {workflowsLoading ? (
            <LinearProgress />
          ) : workflows && workflows.length > 0 ? (
            <Grid container spacing={3}>
              {workflows.map((workflow) => (
                <Grid item xs={12} md={6} lg={4} key={workflow.id}>
                  <Card>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', mb: 2 }}>
                        <Box>
                          <Typography variant="h6" fontWeight={600} gutterBottom>
                            {workflow.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            {workflow.description}
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Tooltip title="Execute workflow">
                            <IconButton
                              size="small"
                              onClick={() => handleExecuteWorkflow(workflow.id)}
                              disabled={executeWorkflowMutation.isLoading}
                            >
                              <PlayArrow />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit workflow">
                            <IconButton size="small" onClick={() => setEditingWorkflow(workflow)}>
                              <Edit />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Delete workflow">
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteWorkflow(workflow.id)}
                              disabled={deleteWorkflowMutation.isLoading}
                            >
                              <Delete />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </Box>
                      
                      <Box sx={{ mb: 2 }}>
                        <Chip
                          label={workflow.enabled ? 'Enabled' : 'Disabled'}
                          color={workflow.enabled ? 'success' : 'default'}
                          size="small"
                          sx={{ mr: 1 }}
                        />
                        {workflow.schedule && (
                          <Chip
                            label="Scheduled"
                            color="info"
                            size="small"
                            icon={<Schedule />}
                          />
                        )}
                      </Box>
                      
                      <Box sx={{ space: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Steps:</Typography>
                          <Typography variant="body2" fontWeight={600}>{workflow.steps.length}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Executions:</Typography>
                          <Typography variant="body2" fontWeight={600}>{workflow.execution_count}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Success Rate:</Typography>
                          <Typography variant="body2" fontWeight={600}>{workflow.success_rate}%</Typography>
                        </Box>
                        {workflow.last_executed && (
                          <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                            <Typography variant="body2">Last Run:</Typography>
                            <Typography variant="body2" fontWeight={600}>
                              {format(new Date(workflow.last_executed), 'MMM dd, HH:mm')}
                            </Typography>
                          </Box>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Build sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No workflows found
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Create your first workflow to automate SEO tasks
                </Typography>
                <Button variant="contained" startIcon={<Add />} onClick={handleCreateWorkflow}>
                  Create Workflow
                </Button>
              </CardContent>
            </Card>
          )}
        </TabPanel>

        <TabPanel value={selectedTab} index={1}>
          {executionsLoading ? (
            <LinearProgress />
          ) : executions && executions.length > 0 ? (
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Recent Executions
                </Typography>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Workflow</TableCell>
                        <TableCell align="center">Status</TableCell>
                        <TableCell align="center">Progress</TableCell>
                        <TableCell align="right">Started</TableCell>
                        <TableCell align="right">Duration</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {executions.slice(0, 20).map((execution) => (
                        <TableRow key={execution.id}>
                          <TableCell>{execution.workflow_name}</TableCell>
                          <TableCell align="center">
                            <Chip
                              label={execution.status}
                              color={automationService.getStatusColor(execution.status)}
                              size="small"
                              icon={
                                execution.status === WorkflowStatus.COMPLETED ? <CheckCircle /> :
                                execution.status === WorkflowStatus.FAILED ? <Error /> :
                                execution.status === WorkflowStatus.RUNNING ? <PlayArrow /> :
                                <AccessTime />
                              }
                            />
                          </TableCell>
                          <TableCell align="center">
                            {execution.status === WorkflowStatus.RUNNING ? (
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                <LinearProgress
                                  variant="determinate"
                                  value={execution.progress}
                                  sx={{ width: 60 }}
                                />
                                <Typography variant="caption">{execution.progress}%</Typography>
                              </Box>
                            ) : (
                              <Typography variant="body2">-</Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            {format(new Date(execution.started_at), 'MMM dd, HH:mm')}
                          </TableCell>
                          <TableCell align="right">
                            {execution.duration_seconds ? `${execution.duration_seconds}s` : '-'}
                          </TableCell>
                          <TableCell align="center">
                            <Tooltip title="View details">
                              <IconButton size="small">
                                <Assessment />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <History sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No executions found
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Workflow executions will appear here once you run them
                </Typography>
              </CardContent>
            </Card>
          )}
        </TabPanel>

        <TabPanel value={selectedTab} index={2}>
          {templates && templates.templates.length > 0 ? (
            <Grid container spacing={3}>
              {templates.templates.map((template) => (
                <Grid item xs={12} md={6} lg={4} key={template.id}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        {template.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {template.description}
                      </Typography>
                      
                      <Box sx={{ mb: 2 }}>
                        <Chip label={template.category} color="primary" size="small" />
                        {template.schedule && (
                          <Chip
                            label={automationService.parseCronExpression(template.schedule)}
                            color="info"
                            size="small"
                            sx={{ ml: 1 }}
                          />
                        )}
                      </Box>
                      
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        Steps: {template.steps.length}
                      </Typography>
                      
                      <Button
                        variant="outlined"
                        startIcon={<FileCopy />}
                        onClick={() => handleUseTemplate(template)}
                        fullWidth
                      >
                        Use Template
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Description sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary" gutterBottom>
                  No templates available
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Workflow templates will be added soon
                </Typography>
              </CardContent>
            </Card>
          )}
        </TabPanel>

        <TabPanel value={selectedTab} index={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Scheduled Workflows
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Workflow scheduling feature coming soon
              </Typography>
            </CardContent>
          </Card>
        </TabPanel>

        {/* Create Workflow Dialog */}
        <Dialog
          open={createDialogOpen}
          onClose={() => setCreateDialogOpen(false)}
          maxWidth="md"
          fullWidth
        >
          <DialogTitle>
            {editingWorkflow ? 'Edit Workflow' : 'Create New Workflow'}
          </DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  label="Workflow Name"
                  value={newWorkflow.name}
                  onChange={(e) => setNewWorkflow({ ...newWorkflow, name: e.target.value })}
                  fullWidth
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Description"
                  value={newWorkflow.description}
                  onChange={(e) => setNewWorkflow({ ...newWorkflow, description: e.target.value })}
                  multiline
                  rows={3}
                  fullWidth
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  label="Schedule (Cron)"
                  value={newWorkflow.schedule || ''}
                  onChange={(e) => setNewWorkflow({ ...newWorkflow, schedule: e.target.value })}
                  fullWidth
                  placeholder="0 6 * * * (Daily at 6 AM)"
                  helperText="Optional: Use cron expression for scheduling"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={newWorkflow.enabled}
                      onChange={(e) => setNewWorkflow({ ...newWorkflow, enabled: e.target.checked })}
                    />
                  }
                  label="Enabled"
                />
              </Grid>
              
              {/* Workflow Steps */}
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6">Workflow Steps</Typography>
                  <Button startIcon={<Add />} onClick={addWorkflowStep}>
                    Add Step
                  </Button>
                </Box>
                
                {newWorkflow.steps.map((step, index) => (
                  <Accordion key={index} sx={{ mb: 1 }}>
                    <AccordionSummary expandIcon={<ExpandMore />}>
                      <Typography>
                        {step.name || `Step ${index + 1}`} - {automationService.getActionTypeLabel(step.action)}
                      </Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <TextField
                            label="Step Name"
                            value={step.name}
                            onChange={(e) => updateWorkflowStep(index, { ...step, name: e.target.value })}
                            fullWidth
                            required
                          />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth>
                            <InputLabel>Action Type</InputLabel>
                            <Select
                              value={step.action}
                              onChange={(e) => updateWorkflowStep(index, { ...step, action: e.target.value as ActionType })}
                              label="Action Type"
                            >
                              {Object.values(ActionType).map((action) => (
                                <MenuItem key={action} value={action}>
                                  {automationService.getActionTypeLabel(action)}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <TextField
                            label="Timeout (seconds)"
                            type="number"
                            value={step.timeout_seconds}
                            onChange={(e) => updateWorkflowStep(index, { ...step, timeout_seconds: Number(e.target.value) })}
                            fullWidth
                          />
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <TextField
                            label="Retry Count"
                            type="number"
                            value={step.retry_count}
                            onChange={(e) => updateWorkflowStep(index, { ...step, retry_count: Number(e.target.value) })}
                            fullWidth
                          />
                        </Grid>
                        <Grid item xs={12}>
                          <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                            <Button
                              color="error"
                              startIcon={<Delete />}
                              onClick={() => removeWorkflowStep(index)}
                            >
                              Remove Step
                            </Button>
                          </Box>
                        </Grid>
                      </Grid>
                    </AccordionDetails>
                  </Accordion>
                ))}
                
                {newWorkflow.steps.length === 0 && (
                  <Alert severity="info">
                    Add at least one step to create the workflow
                  </Alert>
                )}
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
            <Button
              onClick={handleSaveWorkflow}
              variant="contained"
              disabled={createWorkflowMutation.isLoading}
            >
              {createWorkflowMutation.isLoading ? <CircularProgress size={20} /> : 'Create Workflow'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </>
  );
};

export default Automation;