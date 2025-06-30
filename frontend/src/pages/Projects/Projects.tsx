import React from 'react';
import { Box, Typography, Card, CardContent, Grid, Chip } from '@mui/material';
import { Helmet } from 'react-helmet-async';
import { Folder } from '@mui/icons-material';

const Projects: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Projects - SEO Platform</title>
      </Helmet>
      
      <Box>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          Projects
        </Typography>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Manage your SEO projects and campaigns
        </Typography>

        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: 'center', py: 8 }}>
                <Folder sx={{ fontSize: 64, color: 'info.main', mb: 2 }} />
                <Typography variant="h5" fontWeight={600} gutterBottom>
                  Project Management
                </Typography>
                <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                  Project management features coming soon
                </Typography>
                <Chip label="In Development" color="info" />
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </>
  );
};

export default Projects;