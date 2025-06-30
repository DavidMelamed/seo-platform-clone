import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { TrendingUp, Analytics as AnalyticsIcon, Speed, Visibility } from '@mui/icons-material';

const Analytics: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Analytics - SEO Platform</title>
      </Helmet>
      
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Analytics
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Comprehensive SEO analytics and reporting
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <AnalyticsIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  Analytics Dashboard
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Advanced analytics features coming soon
                </Typography>
                <Chip label="In Development" color="primary" />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};

export default Analytics;