import React from 'react';
import {
  Box,
  Toolbar,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Chip,
  alpha,
} from '@mui/material';
import {
  Dashboard,
  Search,
  Analytics,
  MonitorHeart,
  AutoAwesome,
  Psychology,
  Settings,
  Folder,
  TrendingUp,
  Speed,
  SmartToy,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';

interface SidebarProps {
  onItemClick?: () => void;
}

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactElement;
  description?: string;
  badge?: string;
  beta?: boolean;
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    icon: <Dashboard />,
    description: 'Overview & insights',
  },
  {
    label: 'Projects',
    path: '/projects',
    icon: <Folder />,
    description: 'Manage your SEO projects',
  },
  {
    label: 'Keywords',
    path: '/keywords',
    icon: <Search />,
    description: 'Research & track keywords',
  },
  {
    label: 'Analytics',
    path: '/analytics',
    icon: <Analytics />,
    description: 'Performance metrics',
  },
  {
    label: 'Monitoring',
    path: '/monitoring',
    icon: <MonitorHeart />,
    description: 'Real-time tracking',
    badge: 'Live',
  },
  {
    label: 'Automation',
    path: '/automation',
    icon: <AutoAwesome />,
    description: 'Workflows & scheduling',
  },
  {
    label: 'AI Services',
    path: '/ai-services',
    icon: <Psychology />,
    description: 'AI-powered SEO tools',
    beta: true,
  },
];

const secondaryItems: NavItem[] = [
  {
    label: 'Settings',
    path: '/settings',
    icon: <Settings />,
    description: 'Account & preferences',
  },
];

const Sidebar: React.FC<SidebarProps> = ({ onItemClick }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const theme = useTheme();

  const handleNavigation = (path: string) => {
    navigate(path);
    onItemClick?.();
  };

  const isActive = (path: string) => location.pathname === path;

  const renderNavItem = (item: NavItem) => (
    <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
      <ListItemButton
        onClick={() => handleNavigation(item.path)}
        selected={isActive(item.path)}
        sx={{
          mx: 1,
          borderRadius: 2,
          '&.Mui-selected': {
            bgcolor: alpha(theme.palette.primary.main, 0.12),
            color: 'primary.main',
            '&:hover': {
              bgcolor: alpha(theme.palette.primary.main, 0.16),
            },
          },
          '&:hover': {
            bgcolor: alpha(theme.palette.action.hover, 0.8),
          },
        }}
      >
        <ListItemIcon
          sx={{
            color: isActive(item.path) ? 'primary.main' : 'text.secondary',
            minWidth: 40,
          }}
        >
          {item.icon}
        </ListItemIcon>
        <ListItemText
          primary={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Typography
                variant="body2"
                fontWeight={isActive(item.path) ? 600 : 500}
              >
                {item.label}
              </Typography>
              {item.badge && (
                <Chip
                  label={item.badge}
                  size="small"
                  color="success"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
              {item.beta && (
                <Chip
                  label="Beta"
                  size="small"
                  color="primary"
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
            </Box>
          }
          secondary={
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ fontSize: '0.75rem' }}
            >
              {item.description}
            </Typography>
          }
        />
      </ListItemButton>
    </ListItem>
  );

  return (
    <Box
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.paper',
        borderRight: 1,
        borderColor: 'divider',
      }}
    >
      {/* Logo & Header */}
      <Toolbar sx={{ px: 3, borderBottom: 1, borderColor: 'divider' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 32,
              height: 32,
              borderRadius: 2,
              bgcolor: 'primary.main',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <TrendingUp sx={{ color: 'white', fontSize: 20 }} />
          </Box>
          <Box>
            <Typography variant="h6" fontWeight={700} color="primary">
              SEO Platform
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Intelligence Suite
            </Typography>
          </Box>
        </Box>
      </Toolbar>

      {/* Navigation */}
      <Box sx={{ flex: 1, overflow: 'auto', py: 2 }}>
        {/* Main Navigation */}
        <Box sx={{ px: 2, mb: 1 }}>
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ fontWeight: 600, fontSize: '0.7rem' }}
          >
            Main
          </Typography>
        </Box>
        <List dense>
          {navItems.map(renderNavItem)}
        </List>

        <Divider sx={{ my: 2 }} />

        {/* Secondary Navigation */}
        <Box sx={{ px: 2, mb: 1 }}>
          <Typography
            variant="overline"
            color="text.secondary"
            sx={{ fontWeight: 600, fontSize: '0.7rem' }}
          >
            Account
          </Typography>
        </Box>
        <List dense>
          {secondaryItems.map(renderNavItem)}
        </List>
      </Box>

      {/* Footer */}
      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: 'divider',
          bgcolor: alpha(theme.palette.background.default, 0.5),
        }}
      >
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: 2,
            p: 2,
            borderRadius: 2,
            bgcolor: 'background.paper',
            border: 1,
            borderColor: 'divider',
          }}
        >
          <Box
            sx={{
              width: 40,
              height: 40,
              borderRadius: 2,
              bgcolor: alpha(theme.palette.success.main, 0.1),
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SmartToy sx={{ color: 'success.main', fontSize: 20 }} />
          </Box>
          <Box sx={{ flex: 1 }}>
            <Typography variant="body2" fontWeight={600}>
              AI Assistant
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Ready to help
            </Typography>
          </Box>
          <Chip
            label="Pro"
            size="small"
            color="success"
            variant="filled"
            sx={{ fontSize: '0.7rem', height: 20 }}
          />
        </Box>
      </Box>
    </Box>
  );
};

export default Sidebar;