import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Tabs,
  Tab,
  Button,
  Avatar,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  LinearProgress,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Analytics as AnalyticsIcon,
  Speed,
  Visibility,
  Traffic,
  Assessment,
  CompareArrows,
  MonetizationOn,
  Refresh,
  Download,
  InfoOutline,
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
  Title,
  Tooltip as ChartTooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { format, subDays } from 'date-fns';
import toast from 'react-hot-toast';

import { analyticsService, AnalyticsOverview, TrafficMetrics, KeywordPerformance, CompetitorAnalysis, ConversionMetrics } from '../../services/analyticsService';
import { projectsService, Project } from '../../services/projectsService';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  ChartTooltip,
  Legend,
  ArcElement
);

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
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const Analytics: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [dateRange, setDateRange] = useState(30);

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

  const { data: overview, isLoading: overviewLoading } = useQuery<AnalyticsOverview>(
    ['analytics-overview', selectedProject, dateRange],
    () => analyticsService.getOverview(selectedProject, dateRange),
    {
      enabled: !!selectedProject,
      refetchInterval: 300000, // Refetch every 5 minutes
    }
  );

  const { data: trafficData, isLoading: trafficLoading } = useQuery<TrafficMetrics[]>(
    ['analytics-traffic', selectedProject, dateRange],
    () => analyticsService.getTrafficAnalytics(selectedProject, dateRange),
    {
      enabled: !!selectedProject && selectedTab === 1,
    }
  );

  const { data: keywordPerformance, isLoading: keywordsLoading } = useQuery<KeywordPerformance[]>(
    ['analytics-keywords', selectedProject],
    () => analyticsService.getKeywordPerformance(selectedProject, 50, 'position_change'),
    {
      enabled: !!selectedProject && selectedTab === 2,
    }
  );

  const { data: competitorData, isLoading: competitorLoading } = useQuery<CompetitorAnalysis[]>(
    ['analytics-competitors', selectedProject],
    () => analyticsService.getCompetitorAnalysis(selectedProject),
    {
      enabled: !!selectedProject && selectedTab === 3,
    }
  );

  const { data: conversionData, isLoading: conversionLoading } = useQuery<ConversionMetrics[]>(
    ['analytics-conversions', selectedProject, dateRange],
    () => analyticsService.getConversionAnalytics(selectedProject, dateRange),
    {
      enabled: !!selectedProject && selectedTab === 4,
    }
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleRefreshData = async () => {
    if (!selectedProject) return;
    
    try {
      await analyticsService.refreshData(selectedProject);
      toast.success('Analytics data refresh initiated');
      // Invalidate all queries to refetch data
      // This would be done with queryClient.invalidateQueries in a real implementation
    } catch (error) {
      toast.error('Failed to refresh analytics data');
    }
  };

  // Chart configurations
  const trafficChartData = trafficData ? {
    labels: trafficData.map(d => format(new Date(d.date), 'MMM dd')),
    datasets: [
      {
        label: 'Organic Traffic',
        data: trafficData.map(d => d.organic_traffic),
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        tension: 0.1,
      },
      {
        label: 'Clicks',
        data: trafficData.map(d => d.organic_clicks),
        borderColor: 'rgb(75, 192, 192)',
        backgroundColor: 'rgba(75, 192, 192, 0.5)',
        tension: 0.1,
      },
    ],
  } : null;

  const positionDistributionData = overview ? {
    labels: ['Top 3', 'Top 10', 'Top 20', '20+'],
    datasets: [
      {
        data: [
          overview.top_10_count, // Simplified - would need actual position distribution data
          Math.max(0, overview.total_keywords - overview.top_10_count),
          0,
          0,
        ],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(59, 130, 246, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(59, 130, 246, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)',
        ],
        borderWidth: 1,
      },
    ],
  } : null;

  if (!projects || projects.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <Box textAlign="center">
          <Assessment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No projects found
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Create a project first to view analytics
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <>
      <Helmet>
        <title>Analytics - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="h4" fontWeight={700} gutterBottom>
              Analytics
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Comprehensive SEO analytics and performance insights
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
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={dateRange}
                onChange={(e) => setDateRange(Number(e.target.value))}
                label="Period"
              >
                <MenuItem value={7}>7 days</MenuItem>
                <MenuItem value={30}>30 days</MenuItem>
                <MenuItem value={90}>90 days</MenuItem>
                <MenuItem value={365}>1 year</MenuItem>
              </Select>
            </FormControl>
            <Tooltip title="Refresh data">
              <IconButton onClick={handleRefreshData} color="primary">
                <Refresh />
              </IconButton>
            </Tooltip>
            <Button variant="outlined" startIcon={<Download />}>
              Export
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
                      <AnalyticsIcon />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.total_keywords}
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
                        {overview.avg_position}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Position
                      </Typography>
                      {overview.position_change !== 0 && (
                        <Typography 
                          variant="caption" 
                          color={overview.position_change > 0 ? 'success.main' : 'error.main'}
                          sx={{ display: 'flex', alignItems: 'center' }}
                        >
                          {overview.position_change > 0 ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />}
                          {Math.abs(overview.position_change)}
                        </Typography>
                      )}
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
                      <Traffic />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.organic_traffic.toLocaleString()}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Est. Traffic
                      </Typography>
                      {overview.traffic_change !== 0 && (
                        <Typography 
                          variant="caption" 
                          color={overview.traffic_change > 0 ? 'success.main' : 'error.main'}
                          sx={{ display: 'flex', alignItems: 'center' }}
                        >
                          {overview.traffic_change > 0 ? <TrendingUp fontSize="small" /> : <TrendingDown fontSize="small" />}
                          {Math.abs(overview.traffic_change)}%
                        </Typography>
                      )}
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
                      <Visibility />
                    </Avatar>
                    <Box>
                      <Typography variant="h5" fontWeight={700}>
                        {overview.visibility_score}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Visibility Score
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

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={selectedTab} onChange={handleTabChange} aria-label="analytics tabs">
            <Tab label="Overview" />
            <Tab label="Traffic" />
            <Tab label="Keywords" />
            <Tab label="Competitors" />
            <Tab label="Conversions" />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={selectedTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Position Distribution
                  </Typography>
                  {positionDistributionData ? (
                    <Box sx={{ height: 300, display: 'flex', justifyContent: 'center' }}>
                      <Doughnut data={positionDistributionData} />
                    </Box>
                  ) : (
                    <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                      <CircularProgress />
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Quick Stats
                  </Typography>
                  {overview && (
                    <Box sx={{ space: 2 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                        <Typography variant="body2">Top 10 Keywords:</Typography>
                        <Typography variant="body2" fontWeight={600}>{overview.top_10_count}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                        <Typography variant="body2">Opportunities:</Typography>
                        <Typography variant="body2" fontWeight={600}>{overview.keyword_opportunities}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 1 }}>
                        <Typography variant="body2">Total Keywords:</Typography>
                        <Typography variant="body2" fontWeight={600}>{overview.total_keywords}</Typography>
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={1}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Traffic Trends
              </Typography>
              {trafficLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : trafficChartData ? (
                <Box sx={{ height: 400 }}>
                  <Line
                    data={trafficChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: 'top' as const,
                        },
                      },
                    }}
                  />
                </Box>
              ) : (
                <Alert severity="info">No traffic data available for the selected period.</Alert>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Keyword Performance
              </Typography>
              {keywordsLoading ? (
                <LinearProgress />
              ) : keywordPerformance && keywordPerformance.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Keyword</TableCell>
                        <TableCell align="center">Position</TableCell>
                        <TableCell align="center">Change</TableCell>
                        <TableCell align="right">Volume</TableCell>
                        <TableCell align="right">Traffic</TableCell>
                        <TableCell align="right">Difficulty</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {keywordPerformance.slice(0, 20).map((keyword, index) => (
                        <TableRow key={index}>
                          <TableCell>{keyword.keyword}</TableCell>
                          <TableCell align="center">{keyword.current_position}</TableCell>
                          <TableCell align="center">
                            {keyword.position_change !== 0 && (
                              <Chip
                                label={keyword.position_change > 0 ? `+${keyword.position_change}` : keyword.position_change}
                                color={keyword.position_change > 0 ? 'success' : 'error'}
                                size="small"
                                icon={keyword.position_change > 0 ? <TrendingUp /> : <TrendingDown />}
                              />
                            )}
                          </TableCell>
                          <TableCell align="right">{keyword.search_volume.toLocaleString()}</TableCell>
                          <TableCell align="right">{keyword.estimated_traffic.toLocaleString()}</TableCell>
                          <TableCell align="right">{keyword.difficulty}%</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">No keyword performance data available.</Alert>
              )}
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={3}>
          <Grid container spacing={3}>
            {competitorLoading ? (
              <Grid item xs={12}>
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              </Grid>
            ) : competitorData && competitorData.length > 0 ? (
              competitorData.map((competitor, index) => (
                <Grid item xs={12} md={6} lg={4} key={index}>
                  <Card>
                    <CardContent>
                      <Typography variant="h6" fontWeight={600} gutterBottom>
                        {competitor.domain}
                      </Typography>
                      <Box sx={{ space: 1 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Total Keywords:</Typography>
                          <Typography variant="body2" fontWeight={600}>{competitor.total_keywords.toLocaleString()}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Top 10:</Typography>
                          <Typography variant="body2" fontWeight={600}>{competitor.top_10_keywords}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Est. Traffic:</Typography>
                          <Typography variant="body2" fontWeight={600}>{competitor.estimated_traffic.toLocaleString()}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', py: 0.5 }}>
                          <Typography variant="body2">Avg Position:</Typography>
                          <Typography variant="body2" fontWeight={600}>{competitor.avg_position}</Typography>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            ) : (
              <Grid item xs={12}>
                <Alert severity="info">No competitor data available.</Alert>
              </Grid>
            )}
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Conversion Metrics
              </Typography>
              {conversionLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress />
                </Box>
              ) : conversionData && conversionData.length > 0 ? (
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Date</TableCell>
                        <TableCell align="right">Sessions</TableCell>
                        <TableCell align="right">Conversions</TableCell>
                        <TableCell align="right">Conv. Rate</TableCell>
                        <TableCell align="right">Revenue</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {conversionData.slice(-10).map((conversion, index) => (
                        <TableRow key={index}>
                          <TableCell>{format(new Date(conversion.date), 'MMM dd, yyyy')}</TableCell>
                          <TableCell align="right">{conversion.sessions.toLocaleString()}</TableCell>
                          <TableCell align="right">{conversion.conversions}</TableCell>
                          <TableCell align="right">{conversion.conversion_rate}%</TableCell>
                          <TableCell align="right">${conversion.revenue}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Alert severity="info">No conversion data available for the selected period.</Alert>
              )}
            </CardContent>
          </Card>
        </TabPanel>
      </Box>
    </>
  );
};

export default Analytics;