import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { Psychology } from '@mui/icons-material';

const AIServices: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>AI Services - SEO Platform</title>
      </Helmet>
      
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          AI Services
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          AI-powered SEO tools and insights
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Psychology sx={{ fontSize: 64, color: 'secondary.main', mb: 2 }} />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  AI-Powered SEO Tools
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Advanced AI features and content generation
                </Typography>
                <Chip label="Beta" color="secondary" />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};

export default AIServices;