import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { AutoAwesome } from '@mui/icons-material';

const Automation: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Automation - SEO Platform</title>
      </Helmet>
      
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          SEO Automation
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Automate your SEO workflows and tasks
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <AutoAwesome sx={{ fontSize: 64, color: 'warning.main', mb: 2 }} />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  SEO Automation
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Workflow automation features coming soon
                </Typography>
                <Chip label="In Development" color="warning" />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};

export default Automation;