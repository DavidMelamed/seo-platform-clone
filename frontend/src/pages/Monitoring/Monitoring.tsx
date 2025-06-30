import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { MonitorHeart } from '@mui/icons-material';

const Monitoring: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Monitoring - SEO Platform</title>
      </Helmet>
      
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Real-time Monitoring
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Monitor your SEO performance in real-time
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <MonitorHeart sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  Real-time Monitoring
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Live monitoring dashboard coming soon
                </Typography>
                <Chip label="In Development" color="success" />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};

export default Monitoring;