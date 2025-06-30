import React, { useState } from 'react';
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
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';

// Mock data
const mockKeywords = [
  {
    id: '1',
    keyword: 'SEO tools',
    position: 12,
    previousPosition: 15,
    searchVolume: 5000,
    difficulty: 65,
    cpc: 2.50,
    traffic: 150,
    priority: 'high',
  },
  {
    id: '2',
    keyword: 'keyword research',
    position: 8,
    previousPosition: 9,
    searchVolume: 3000,
    difficulty: 45,
    cpc: 1.80,
    traffic: 300,
    priority: 'medium',
  },
  {
    id: '3',
    keyword: 'backlink analysis',
    position: 22,
    previousPosition: 18,
    searchVolume: 1200,
    difficulty: 72,
    cpc: 3.20,
    traffic: 80,
    priority: 'low',
  },
];

const Keywords: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');

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

  const getPositionChange = (current: number, previous: number) => {
    const change = previous - current;
    return {
      value: change,
      icon: change > 0 ? <TrendingUp /> : change < 0 ? <TrendingDown /> : <Remove />,
      color: change > 0 ? 'success.main' : change < 0 ? 'error.main' : 'text.secondary',
    };
  };

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
            <Button variant="outlined" startIcon={<Upload />}>
              Import
            </Button>
            <Button variant="outlined" startIcon={<Download />}>
              Export
            </Button>
            <Button variant="contained" startIcon={<Add />}>
              Add Keywords
            </Button>
          </Box>
        </Box>

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
                      {mockKeywords.length}
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
                      14.2
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
                      1
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
                      530
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
              <Button variant="outlined" startIcon={<FilterList />}>
                Filters
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Keywords Table */}
        <Card>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Keyword</TableCell>
                  <TableCell align="center">Position</TableCell>
                  <TableCell align="center">Change</TableCell>
                  <TableCell align="right">Search Volume</TableCell>
                  <TableCell align="right">Difficulty</TableCell>
                  <TableCell align="right">CPC</TableCell>
                  <TableCell align="right">Traffic</TableCell>
                  <TableCell align="center">Priority</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {mockKeywords.map((keyword) => {
                  const positionChange = getPositionChange(keyword.position, keyword.previousPosition);
                  
                  return (
                    <TableRow key={keyword.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight={600}>
                          {keyword.keyword}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Typography variant="body2" fontWeight={600}>
                          {keyword.position}
                        </Typography>
                      </TableCell>
                      <TableCell align="center">
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Box sx={{ color: positionChange.color, mr: 0.5 }}>
                            {positionChange.icon}
                          </Box>
                          <Typography
                            variant="body2"
                            sx={{ color: positionChange.color }}
                            fontWeight={600}
                          >
                            {positionChange.value !== 0 && (positionChange.value > 0 ? '+' : '')}{positionChange.value}
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {keyword.searchVolume.toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {keyword.difficulty}%
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          ${keyword.cpc.toFixed(2)}
                        </Typography>
                      </TableCell>
                      <TableCell align="right">
                        <Typography variant="body2">
                          {keyword.traffic}
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
                        <IconButton size="small">
                          <MoreVert />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Card>
      </Box>
    </>
  );
};

export default Keywords;