import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  Avatar,
  LinearProgress,
  IconButton,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Divider,
  Paper,
  useTheme,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Search,
  Visibility,
  Speed,
  AutoAwesome,
  MonitorHeart,
  Psychology,
  MoreVert,
  Launch,
  Refresh,
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import { useQuery } from 'react-query';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { dashboardService, DashboardData } from '../../services/dashboardService';
import { useAuthStore } from '../../store/authStore';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);


const MetricCard: React.FC<{
  title: string;
  value: string | number;
  change?: number;
  icon: React.ReactElement;
  color?: string;
}> = ({ title, value, change, icon, color = 'primary' }) => {
  const theme = useTheme();
  
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Avatar
            sx={{
              bgcolor: `${color}.main`,
              width: 48,
              height: 48,
              mr: 2,
            }}
          >
            {icon}
          </Avatar>
          <Box sx={{ flex: 1 }}>
            <Typography variant="h4" fontWeight={700}>
              {typeof value === 'number' ? value.toLocaleString() : value}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {title}
            </Typography>
          </Box>
        </Box>
        {change !== undefined && (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {change > 0 ? (
              <TrendingUp sx={{ color: 'success.main', mr: 0.5 }} />
            ) : (
              <TrendingDown sx={{ color: 'error.main', mr: 0.5 }} />
            )}
            <Typography
              variant="body2"
              color={change > 0 ? 'success.main' : 'error.main'}
              fontWeight={600}
            >
              {change > 0 ? '+' : ''}{change}%
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ ml: 0.5 }}>
              vs last month
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const { user } = useAuthStore();
  const [selectedProject, setSelectedProject] = useState<string | undefined>(undefined);

  // Real API query for dashboard data
  const { data: dashboardData, isLoading, refetch } = useQuery<DashboardData>(
    ['dashboard-data', selectedProject],
    () => dashboardService.getCompleteDashboard(selectedProject),
    {
      refetchInterval: 60000, // Refetch every minute
      enabled: !!user, // Only fetch when user is authenticated
    }
  );

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        grid: {
          color: theme.palette.divider,
        },
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  return (
    <>
      <Helmet>
        <title>Dashboard - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Good morning{user?.full_name ? `, ${user.full_name.split(' ')[0]}` : ''}! 👋
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Here's what's happening with your SEO performance today.
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={() => refetch()}
            >
              Refresh
            </Button>
            <Button
              variant="contained"
              startIcon={<AutoAwesome />}
            >
              AI Insights
            </Button>
          </Box>
        </Box>

        {/* Key Metrics */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Total Keywords"
              value={dashboardData?.metrics.total_keywords || 0}
              change={8.2}
              icon={<Search />}
              color="primary"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Average Position"
              value={dashboardData?.metrics.avg_position || 0}
              change={-2.1}
              icon={<TrendingUp />}
              color="success"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Top 10 Keywords"
              value={dashboardData?.metrics.top_ten_keywords || 0}
              change={12.5}
              icon={<Visibility />}
              color="warning"
            />
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <MetricCard
              title="Organic Traffic"
              value={dashboardData?.metrics.organic_traffic || 0}
              change={15.3}
              icon={<Speed />}
              color="info"
            />
          </Grid>
        </Grid>

        {/* Charts and Analytics */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          {/* Traffic Trend */}
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" fontWeight={600}>
                    Organic Traffic Trend
                  </Typography>
                  <IconButton size="small">
                    <MoreVert />
                  </IconButton>
                </Box>
                <Box sx={{ height: 300 }}>
                  {dashboardData?.traffic_data ? (
                    <Line data={dashboardData.traffic_data} options={chartOptions} />
                  ) : (
                    <Box display="flex" justifyContent="center" alignItems="center" height="100%">
                      <Typography color="text.secondary">No traffic data available</Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Position Distribution */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Position Distribution
                </Typography>
                <Box sx={{ height: 300 }}>
                  {dashboardData?.position_data ? (
                    <Doughnut data={dashboardData.position_data} options={doughnutOptions} />
                  ) : (
                    <Box display="flex" justifyContent="center" alignItems="center" height="100%">
                      <Typography color="text.secondary">No position data available</Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Recent Activity and Quick Actions */}
        <Grid container spacing={3}>
          {/* Recent Activity */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Recent Activity
                </Typography>
                <List>
                  {dashboardData?.recent_activities && dashboardData.recent_activities.length > 0 ? (
                    dashboardData.recent_activities.map((activity, index) => (
                      <React.Fragment key={activity.id}>
                        <ListItem>
                          <ListItemAvatar>
                            <Avatar sx={{ 
                              bgcolor: activity.type === 'alert' ? 'primary.main' : 
                                       activity.type === 'keyword' ? 'success.main' : 'warning.main'
                            }}>
                              {activity.type === 'alert' ? <MonitorHeart /> : 
                               activity.type === 'keyword' ? <Search /> : <Psychology />}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={activity.title}
                            secondary={new Date(activity.timestamp).toLocaleDateString()}
                          />
                          <Chip 
                            label={activity.status} 
                            color={activity.status === 'new' ? 'success' : 'primary'} 
                            size="small" 
                          />
                        </ListItem>
                        {index < dashboardData.recent_activities.length - 1 && (
                          <Divider variant="inset" component="li" />
                        )}
                      </React.Fragment>
                    ))
                  ) : (
                    <ListItem>
                      <ListItemText
                        primary="No recent activities"
                        secondary="Start tracking keywords to see activity"
                      />
                    </ListItem>
                  )}
                </List>
              </CardContent>
            </Card>
          </Grid>

          {/* Quick Actions */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={600} gutterBottom>
                  Quick Actions
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Paper
                      sx={{
                        p: 2,
                        textAlign: 'center',
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <Search sx={{ fontSize: 32, color: 'primary.main', mb: 1 }} />
                      <Typography variant="body2" fontWeight={600}>
                        Add Keywords
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper
                      sx={{
                        p: 2,
                        textAlign: 'center',
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <AutoAwesome sx={{ fontSize: 32, color: 'warning.main', mb: 1 }} />
                      <Typography variant="body2" fontWeight={600}>
                        Run Automation
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper
                      sx={{
                        p: 2,
                        textAlign: 'center',
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <Psychology sx={{ fontSize: 32, color: 'success.main', mb: 1 }} />
                      <Typography variant="body2" fontWeight={600}>
                        AI Analysis
                      </Typography>
                    </Paper>
                  </Grid>
                  <Grid item xs={6}>
                    <Paper
                      sx={{
                        p: 2,
                        textAlign: 'center',
                        cursor: 'pointer',
                        '&:hover': { bgcolor: 'action.hover' },
                      }}
                    >
                      <Launch sx={{ fontSize: 32, color: 'info.main', mb: 1 }} />
                      <Typography variant="body2" fontWeight={600}>
                        Export Report
                      </Typography>
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};

export default Dashboard;