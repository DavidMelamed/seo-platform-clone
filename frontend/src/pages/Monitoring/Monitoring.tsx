import React, { useState, useEffect, useCallback } from 'react';
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
  Badge,
  LinearProgress,
  Alert,
  AlertTitle,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  ListItemSecondaryAction,
  Divider,
  Tabs,
  Tab,
  Paper,
  Tooltip,
  CircularProgress,
} from '@mui/material';
import {
  MonitorHeart,
  NotificationsActive,
  Add,
  Edit,
  Delete,
  Refresh,
  CheckCircle,
  Warning,
  Error,
  Info,
  Timeline,
  Settings,
  Close,
  MarkEmailRead,
  Archive,
  Speed,
  Security,
  Storage,
  Cloud,
  Wifi,
  WifiOff,
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import {
  monitoringService,
  Alert as AlertType,
  AlertCreate,
  AlertUpdate,
  Notification,
  MonitoringOverview,
  SystemHealth,
  AlertType as AlertTypeEnum,
  AlertSeverity,
  NotificationStatus,
  RealTimeUpdate,
} from '../../services/monitoringService';
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
      id={`monitoring-tabpanel-${index}`}
      aria-labelledby={`monitoring-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const Monitoring: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [createAlertDialogOpen, setCreateAlertDialogOpen] = useState(false);
  const [editAlertDialogOpen, setEditAlertDialogOpen] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState<AlertType | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [realtimeUpdates, setRealtimeUpdates] = useState<RealTimeUpdate[]>([]);
  const [webSocket, setWebSocket] = useState<WebSocket | null>(null);
  
  const [alertFormData, setAlertFormData] = useState<AlertCreate>({
    name: '',
    project_id: '',
    alert_type: AlertTypeEnum.RANKING_DROP,
    threshold_value: 5,
    comparison_operator: '>',
    is_active: true,
    email_notifications: true,
    slack_notifications: false,
    webhook_url: '',
  });

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

  const { data: overview, isLoading: overviewLoading } = useQuery<MonitoringOverview>(
    ['monitoring-overview', selectedProject],
    () => monitoringService.getOverview(selectedProject),
    {
      enabled: !!selectedProject,
      refetchInterval: 30000, // Refetch every 30 seconds
    }
  );

  const { data: alerts, isLoading: alertsLoading } = useQuery<AlertType[]>(
    ['monitoring-alerts', selectedProject],
    () => monitoringService.getAlerts(selectedProject),
    {
      enabled: !!selectedProject,
    }
  );

  const { data: notifications, isLoading: notificationsLoading } = useQuery<Notification[]>(
    ['monitoring-notifications', selectedProject],
    () => monitoringService.getNotifications(selectedProject),
    {
      enabled: !!selectedProject,
    }
  );

  const { data: systemHealth } = useQuery<SystemHealth>(
    ['system-health'],
    () => monitoringService.getSystemHealth(),
    {
      refetchInterval: 60000, // Refetch every minute
    }
  );

  // Mutations
  const createAlertMutation = useMutation(
    (data: AlertCreate) => monitoringService.createAlert(data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['monitoring-alerts']);
        setCreateAlertDialogOpen(false);
        resetAlertForm();
        toast.success('Alert created successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to create alert');
      },
    }
  );

  const updateAlertMutation = useMutation(
    ({ id, data }: { id: string; data: AlertUpdate }) =>
      monitoringService.updateAlert(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['monitoring-alerts']);
        setEditAlertDialogOpen(false);
        setSelectedAlert(null);
        resetAlertForm();
        toast.success('Alert updated successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to update alert');
      },
    }
  );

  const deleteAlertMutation = useMutation(
    (id: string) => monitoringService.deleteAlert(id),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['monitoring-alerts']);
        toast.success('Alert deleted successfully!');
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Failed to delete alert');
      },
    }
  );

  const updateNotificationMutation = useMutation(
    ({ id, status }: { id: string; status: NotificationStatus }) =>
      monitoringService.updateNotificationStatus(id, status),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['monitoring-notifications']);
      },
    }
  );

  const triggerAlertCheckMutation = useMutation(
    (projectId: string) => monitoringService.triggerAlertCheck(projectId),
    {
      onSuccess: () => {
        toast.success('Alert check initiated');
      },
      onError: (error: any) => {
        toast.error('Failed to trigger alert check');
      },
    }
  );

  // WebSocket setup
  const handleRealtimeMessage = useCallback((data: RealTimeUpdate) => {
    setRealtimeUpdates(prev => [data, ...prev.slice(0, 49)]); // Keep last 50 updates
    
    // Handle specific update types
    if (data.type === 'new_alert') {
      queryClient.invalidateQueries(['monitoring-alerts']);
      queryClient.invalidateQueries(['monitoring-notifications']);
      toast.info('New alert triggered!');
    }
  }, [queryClient]);

  useEffect(() => {
    if (selectedProject) {
      // Connect to WebSocket for real-time updates
      const ws = monitoringService.connectWebSocket(selectedProject, handleRealtimeMessage);
      setWebSocket(ws);
      
      ws.onopen = () => setIsConnected(true);
      ws.onclose = () => setIsConnected(false);
      ws.onerror = () => setIsConnected(false);

      return () => {
        ws.close();
        setWebSocket(null);
        setIsConnected(false);
      };
    }
  }, [selectedProject, handleRealtimeMessage]);

  const resetAlertForm = () => {
    setAlertFormData({
      name: '',
      project_id: selectedProject,
      alert_type: AlertTypeEnum.RANKING_DROP,
      threshold_value: 5,
      comparison_operator: '>',
      is_active: true,
      email_notifications: true,
      slack_notifications: false,
      webhook_url: '',
    });
  };

  const handleCreateAlert = () => {
    if (!alertFormData.name || !alertFormData.project_id) {
      toast.error('Please fill in all required fields');
      return;
    }

    createAlertMutation.mutate(alertFormData);
  };

  const handleEditAlert = () => {
    if (!selectedAlert) return;

    const updateData: AlertUpdate = {
      name: alertFormData.name,
      threshold_value: alertFormData.threshold_value,
      comparison_operator: alertFormData.comparison_operator,
      is_active: alertFormData.is_active,
      email_notifications: alertFormData.email_notifications,
      slack_notifications: alertFormData.slack_notifications,
      webhook_url: alertFormData.webhook_url || undefined,
    };

    updateAlertMutation.mutate({ id: selectedAlert.id, data: updateData });
  };

  const handleDeleteAlert = (alert: AlertType) => {
    if (window.confirm(`Are you sure you want to delete the alert "${alert.name}"?`)) {
      deleteAlertMutation.mutate(alert.id);
    }
  };

  const openEditDialog = (alert: AlertType) => {
    setSelectedAlert(alert);
    setAlertFormData({
      name: alert.name,
      project_id: alert.project_id,
      alert_type: alert.alert_type,
      threshold_value: alert.threshold_value,
      comparison_operator: alert.comparison_operator,
      is_active: alert.is_active,
      email_notifications: alert.email_notifications,
      slack_notifications: alert.slack_notifications,
      webhook_url: alert.webhook_url || '',
    });
    setEditAlertDialogOpen(true);
  };

  const handleMarkNotificationRead = (notification: Notification) => {
    updateNotificationMutation.mutate({
      id: notification.id,
      status: NotificationStatus.READ,
    });
  };

  const getHealthStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle color="success" />;
      case 'degraded':
        return <Warning color="warning" />;
      case 'unhealthy':
        return <Error color="error" />;
      default:
        return <Info color="info" />;
    }
  };

  const getHealthStatusColor = (status: string): 'success' | 'warning' | 'error' | 'info' => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'unhealthy':
        return 'error';
      default:
        return 'info';
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  useEffect(() => {
    setAlertFormData(prev => ({ ...prev, project_id: selectedProject }));
  }, [selectedProject]);

  if (!projects || projects.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <MonitorHeart sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create a project first to set up monitoring
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <>
      <Helmet>
        <title>Monitoring - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Typography variant="h4" fontWeight={700} gutterBottom>
                Real-time Monitoring
              </Typography>
              <Tooltip title={isConnected ? 'Connected' : 'Disconnected'}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {isConnected ? (
                    <Wifi color="success" />
                  ) : (
                    <WifiOff color="error" />
                  )}
                </Box>
              </Tooltip>
            </Box>
            <Typography variant="body1" color="text.secondary">
              Monitor your SEO performance with real-time alerts and notifications
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
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => triggerAlertCheckMutation.mutate(selectedProject)}
              disabled={!selectedProject}
            >
              Check Alerts
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateAlertDialogOpen(true)}
              disabled={!selectedProject}
            >
              Create Alert
            </Button>
          </Box>
        </Box>

        {/* Overview Cards */}
        {overview && (
          <Grid container spacing={3} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                      <Timeline />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.total_alerts}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Alerts
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
                      <CheckCircle />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.active_alerts}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Active Alerts
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
                      <NotificationsActive />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.triggered_today}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Triggered Today
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
                    <Avatar sx={{ bgcolor: getHealthStatusColor(overview.system_health), mr: 2 }}>
                      {getHealthStatusIcon(overview.system_health)}
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.uptime_percentage}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Uptime
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Loading state for overview */}
        {overviewLoading && <LinearProgress sx={{ mb: 3 }} />}

        {/* System Health Alert */}
        {systemHealth && systemHealth.status !== 'healthy' && (
          <Alert severity={getHealthStatusColor(systemHealth.status)} sx={{ mb: 3 }}>
            <AlertTitle>System Health Warning</AlertTitle>
            System status: {systemHealth.status} - Some services may be experiencing issues.
          </Alert>
        )}

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={selectedTab} onChange={handleTabChange} aria-label="monitoring tabs">
            <Tab label="Alerts" />
            <Tab label={`Notifications ${overview?.unread_notifications ? `(${overview.unread_notifications})` : ''}`} />
            <Tab label="System Health" />
            <Tab label="Real-time Updates" />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={selectedTab} index={0}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Alert Configuration
              </Typography>
              {alertsLoading ? (
                <LinearProgress />
              ) : alerts && alerts.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Type</TableCell>
                        <TableCell>Threshold</TableCell>
                        <TableCell>Severity</TableCell>
                        <TableCell align="center">Status</TableCell>
                        <TableCell align="center">Notifications</TableCell>
                        <TableCell align="right">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {alerts.map((alert) => (
                        <TableRow key={alert.id}>
                          <TableCell>
                            <Typography variant="body2" fontWeight={600}>
                              {alert.name}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={monitoringService.getAlertTypeLabel(alert.alert_type)}
                              size="small"
                              variant="outlined"
                            />
                          </TableCell>
                          <TableCell>
                            {alert.comparison_operator} {alert.threshold_value}
                          </TableCell>
                          <TableCell>
                            <Chip
                              label={alert.severity}
                              color={monitoringService.getSeverityColor(alert.severity)}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              label={alert.is_active ? 'Active' : 'Inactive'}
                              color={alert.is_active ? 'success' : 'default'}
                              size="small"
                            />
                          </TableCell>
                          <TableCell align="center">
                            <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1 }}>
                              {alert.email_notifications && (
                                <Tooltip title="Email notifications enabled">
                                  <CheckCircle color="success" fontSize="small" />
                                </Tooltip>
                              )}
                              {alert.slack_notifications && (
                                <Tooltip title="Slack notifications enabled">
                                  <CheckCircle color="info" fontSize="small" />
                                </Tooltip>
                              )}
                            </Box>
                          </TableCell>
                          <TableCell align="right">
                            <IconButton
                              size="small"
                              onClick={() => openEditDialog(alert)}
                            >
                              <Edit />
                            </IconButton>
                            <IconButton
                              size="small"
                              onClick={() => handleDeleteAlert(alert)}
                              color="error"
                            >
                              <Delete />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Box textAlign="center" py={4}>
                  <Timeline sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No alerts configured
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Create your first alert to start monitoring
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setCreateAlertDialogOpen(true)}
                  >
                    Create Alert
                  </Button>
                </Box>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={1}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Recent Notifications
              </Typography>
              {notificationsLoading ? (
                <LinearProgress />
              ) : notifications && notifications.length > 0 ? (
                <List>
                  {notifications.map((notification, index) => (
                    <React.Fragment key={notification.id}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: monitoringService.getSeverityColor(notification.severity) }}>
                            {notification.severity === AlertSeverity.CRITICAL ? (
                              <Error />
                            ) : notification.severity === AlertSeverity.HIGH ? (
                              <Warning />
                            ) : (
                              <Info />
                            )}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="subtitle2">
                                {notification.title}
                              </Typography>
                              {notification.status === NotificationStatus.UNREAD && (
                                <Badge color="primary" variant="dot" />
                              )}
                            </Box>
                          }
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {notification.message}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {format(new Date(notification.created_at), 'MMM dd, yyyy HH:mm')}
                              </Typography>
                            </Box>
                          }
                        />
                        <ListItemSecondaryAction>
                          {notification.status === NotificationStatus.UNREAD && (
                            <IconButton
                              edge="end"
                              onClick={() => handleMarkNotificationRead(notification)}
                            >
                              <MarkEmailRead />
                            </IconButton>
                          )}
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < notifications.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box textAlign="center" py={4}>
                  <NotificationsActive sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No notifications
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    You're all caught up! Notifications will appear here when alerts are triggered.
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={2}>
          <Grid container spacing={3}>
            {systemHealth && (
              <>
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        System Status
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        {getHealthStatusIcon(systemHealth.status)}
                        <Typography variant="h5" sx={{ ml: 1 }}>
                          {systemHealth.status.charAt(0).toUpperCase() + systemHealth.status.slice(1)}
                        </Typography>
                      </Box>
                      <Typography variant="body2" color="text.secondary">
                        Response Time: {systemHealth.response_time.toFixed(2)}ms
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Last Check: {format(new Date(systemHealth.last_check), 'MMM dd, yyyy HH:mm:ss')}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        Service Health
                      </Typography>
                      <Box sx={{ space: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Storage sx={{ mr: 1 }} />
                            <Typography variant="body2">Database</Typography>
                          </Box>
                          <Chip
                            label={systemHealth.database_status}
                            color={getHealthStatusColor(systemHealth.database_status)}
                            size="small"
                          />
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Speed sx={{ mr: 1 }} />
                            <Typography variant="body2">Redis Cache</Typography>
                          </Box>
                          <Chip
                            label={systemHealth.redis_status}
                            color={getHealthStatusColor(systemHealth.redis_status)}
                            size="small"
                          />
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', py: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Cloud sx={{ mr: 1 }} />
                            <Typography variant="body2">DataForSEO API</Typography>
                          </Box>
                          <Chip
                            label={systemHealth.dataforseo_status}
                            color={getHealthStatusColor(systemHealth.dataforseo_status)}
                            size="small"
                          />
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              </>
            )}
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6" fontWeight={600}>
                  Real-time Updates
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {isConnected ? (
                    <>
                      <Wifi color="success" />
                      <Typography variant="body2" color="success.main">
                        Connected
                      </Typography>
                    </>
                  ) : (
                    <>
                      <WifiOff color="error" />
                      <Typography variant="body2" color="error.main">
                        Disconnected
                      </Typography>
                    </>
                  )}
                </Box>
              </Box>
              
              {realtimeUpdates.length > 0 ? (
                <List sx={{ maxHeight: 400, overflow: 'auto' }}>
                  {realtimeUpdates.map((update, index) => (
                    <React.Fragment key={index}>
                      <ListItem>
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: 'info.main' }}>
                            <Timeline />
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={update.type.replace(/_/g, ' ').toUpperCase()}
                          secondary={
                            <Box>
                              <Typography variant="body2" color="text.secondary">
                                {JSON.stringify(update.data, null, 2)}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {format(new Date(update.timestamp), 'HH:mm:ss')}
                              </Typography>
                            </Box>
                          }
                        />
                      </ListItem>
                      {index < realtimeUpdates.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              ) : (
                <Box textAlign="center" py={4}>
                  <Timeline sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No real-time updates
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Real-time updates will appear here when monitoring is active
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        {/* Create Alert Dialog */}
        <Dialog open={createAlertDialogOpen} onClose={() => setCreateAlertDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create New Alert</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Alert Name"
                    value={alertFormData.name}
                    onChange={(e) => setAlertFormData({ ...alertFormData, name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Alert Type</InputLabel>
                    <Select
                      value={alertFormData.alert_type}
                      onChange={(e) => setAlertFormData({ ...alertFormData, alert_type: e.target.value as AlertTypeEnum })}
                      label="Alert Type"
                    >
                      {Object.values(AlertTypeEnum).map((type) => (
                        <MenuItem key={type} value={type}>
                          {monitoringService.getAlertTypeLabel(type)}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth>
                    <InputLabel>Operator</InputLabel>
                    <Select
                      value={alertFormData.comparison_operator}
                      onChange={(e) => setAlertFormData({ ...alertFormData, comparison_operator: e.target.value })}
                      label="Operator"
                    >
                      <MenuItem value=">">Greater than</MenuItem>
                      <MenuItem value=">=">Greater than or equal</MenuItem>
                      <MenuItem value="<">Less than</MenuItem>
                      <MenuItem value="<=">Less than or equal</MenuItem>
                      <MenuItem value="=">Equal to</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Threshold Value"
                    type="number"
                    value={alertFormData.threshold_value}
                    onChange={(e) => setAlertFormData({ ...alertFormData, threshold_value: Number(e.target.value) })}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Webhook URL (Optional)"
                    value={alertFormData.webhook_url}
                    onChange={(e) => setAlertFormData({ ...alertFormData, webhook_url: e.target.value })}
                    placeholder="https://hooks.slack.com/..."
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFormData.is_active}
                        onChange={(e) => setAlertFormData({ ...alertFormData, is_active: e.target.checked })}
                      />
                    }
                    label="Active"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFormData.email_notifications}
                        onChange={(e) => setAlertFormData({ ...alertFormData, email_notifications: e.target.checked })}
                      />
                    }
                    label="Email Notifications"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFormData.slack_notifications}
                        onChange={(e) => setAlertFormData({ ...alertFormData, slack_notifications: e.target.checked })}
                      />
                    }
                    label="Slack Notifications"
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setCreateAlertDialogOpen(false); resetAlertForm(); }}>
              Cancel
            </Button>
            <Button
              onClick={handleCreateAlert}
              variant="contained"
              disabled={createAlertMutation.isLoading}
            >
              {createAlertMutation.isLoading ? 'Creating...' : 'Create Alert'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Edit Alert Dialog */}
        <Dialog open={editAlertDialogOpen} onClose={() => setEditAlertDialogOpen(false)} maxWidth="md" fullWidth>
          <DialogTitle>Edit Alert</DialogTitle>
          <DialogContent>
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Alert Name"
                    value={alertFormData.name}
                    onChange={(e) => setAlertFormData({ ...alertFormData, name: e.target.value })}
                    required
                  />
                </Grid>
                <Grid item xs={12} sm={3}>
                  <FormControl fullWidth>
                    <InputLabel>Operator</InputLabel>
                    <Select
                      value={alertFormData.comparison_operator}
                      onChange={(e) => setAlertFormData({ ...alertFormData, comparison_operator: e.target.value })}
                      label="Operator"
                    >
                      <MenuItem value=">">Greater than</MenuItem>
                      <MenuItem value=">=">Greater than or equal</MenuItem>
                      <MenuItem value="<">Less than</MenuItem>
                      <MenuItem value="<=">Less than or equal</MenuItem>
                      <MenuItem value="=">Equal to</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={3}>
                  <TextField
                    fullWidth
                    label="Threshold Value"
                    type="number"
                    value={alertFormData.threshold_value}
                    onChange={(e) => setAlertFormData({ ...alertFormData, threshold_value: Number(e.target.value) })}
                    required
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Webhook URL (Optional)"
                    value={alertFormData.webhook_url}
                    onChange={(e) => setAlertFormData({ ...alertFormData, webhook_url: e.target.value })}
                    placeholder="https://hooks.slack.com/..."
                  />
                </Grid>
                <Grid item xs={12}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFormData.is_active}
                        onChange={(e) => setAlertFormData({ ...alertFormData, is_active: e.target.checked })}
                      />
                    }
                    label="Active"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFormData.email_notifications}
                        onChange={(e) => setAlertFormData({ ...alertFormData, email_notifications: e.target.checked })}
                      />
                    }
                    label="Email Notifications"
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={alertFormData.slack_notifications}
                        onChange={(e) => setAlertFormData({ ...alertFormData, slack_notifications: e.target.checked })}
                      />
                    }
                    label="Slack Notifications"
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => { setEditAlertDialogOpen(false); resetAlertForm(); }}>
              Cancel
            </Button>
            <Button
              onClick={handleEditAlert}
              variant="contained"
              disabled={updateAlertMutation.isLoading}
            >
              {updateAlertMutation.isLoading ? 'Updating...' : 'Update Alert'}
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </>
  );
};

export default Monitoring;