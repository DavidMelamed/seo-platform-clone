import React, { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Avatar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Tabs,
  Tab,
  Divider,
  LinearProgress,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  InputAdornment,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  Psychology,
  AutoFixHigh,
  Chat,
  ImageSearch,
  RecordVoiceOver,
  Assessment,
  Create,
  Send,
  CloudUpload,
  ContentCopy,
  Download,
  Refresh,
  ExpandMore,
  Tune,
  Search,
  Visibility,
  Speed,
  VoiceChat,
  SmartToy,
  Article,
  CameraAlt,
  Analytics,
} from '@mui/icons-material';
import { Helmet } from 'react-helmet-async';
import { useQuery, useMutation } from 'react-query';
import { format } from 'date-fns';
import toast from 'react-hot-toast';

import {
  aiService,
  ContentType,
  ToneType,
  ContentGenerationRequest,
  ContentGenerationResponse,
  ChatMessage,
  ChatResponse,
  ChatSession,
  SessionMessage,
  VoiceOptimizationRequest,
  ContentOptimizationRequest,
} from '../../services/aiService';

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
      id={`ai-services-tabpanel-${index}`}
      aria-labelledby={`ai-services-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const AIServices: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [contentForm, setContentForm] = useState<ContentGenerationRequest>({
    content_type: ContentType.BLOG,
    topic: '',
    keywords: [],
    tone: ToneType.PROFESSIONAL,
    length: 1000,
    additional_instructions: '',
  });
  const [keywordInput, setKeywordInput] = useState('');
  const [generatedContent, setGeneratedContent] = useState<ContentGenerationResponse | null>(null);
  const [chatMessages, setChatMessages] = useState<SessionMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [serpScreenshot, setSerpScreenshot] = useState<File | null>(null);
  const [serpKeyword, setSerpKeyword] = useState('');
  const [voiceOptimization, setVoiceOptimization] = useState<VoiceOptimizationRequest>({
    content: '',
    target_queries: [],
    language: 'en',
  });
  const [contentOptimization, setContentOptimization] = useState<ContentOptimizationRequest>({
    content: '',
    target_keywords: [],
    content_type: 'blog',
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Queries
  const { data: chatSessions } = useQuery<{ sessions: ChatSession[] }>(
    ['ai-chat-sessions'],
    () => aiService.getChatSessions(),
    {
      refetchInterval: 30000,
    }
  );

  // Mutations
  const generateContentMutation = useMutation(
    (request: ContentGenerationRequest) => aiService.generateContent(request),
    {
      onSuccess: (data) => {
        setGeneratedContent(data);
        toast.success('Content generated successfully!');
      },
      onError: () => {
        toast.error('Failed to generate content');
      },
    }
  );

  const sendMessageMutation = useMutation(
    (message: ChatMessage) => aiService.sendChatMessage(message),
    {
      onSuccess: (data) => {
        const newMessages = [
          ...chatMessages,
          { role: 'user' as const, content: currentMessage, created_at: new Date().toISOString() },
          { role: 'assistant' as const, content: data.response, created_at: new Date().toISOString() },
        ];
        setChatMessages(newMessages);
        setCurrentSessionId(data.session_id);
        setCurrentMessage('');
      },
      onError: () => {
        toast.error('Failed to send message');
      },
    }
  );

  const analyzeSerpMutation = useMutation(
    ({ file, keyword }: { file: File; keyword?: string }) =>
      aiService.analyzeSerpScreenshot(file, keyword),
    {
      onSuccess: (data) => {
        toast.success('SERP analysis completed!');
      },
      onError: () => {
        toast.error('Failed to analyze SERP screenshot');
      },
    }
  );

  const optimizeVoiceMutation = useMutation(
    (request: VoiceOptimizationRequest) => aiService.optimizeForVoiceSearch(request),
    {
      onSuccess: () => {
        toast.success('Voice optimization completed!');
      },
      onError: () => {
        toast.error('Failed to optimize for voice search');
      },
    }
  );

  const optimizeContentMutation = useMutation(
    (request: ContentOptimizationRequest) => aiService.optimizeContent(request),
    {
      onSuccess: () => {
        toast.success('Content optimization completed!');
      },
      onError: () => {
        toast.error('Failed to optimize content');
      },
    }
  );

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setSelectedTab(newValue);
  };

  const handleAddKeyword = () => {
    if (keywordInput.trim() && !contentForm.keywords.includes(keywordInput.trim())) {
      setContentForm({
        ...contentForm,
        keywords: [...contentForm.keywords, keywordInput.trim()],
      });
      setKeywordInput('');
    }
  };

  const handleRemoveKeyword = (keyword: string) => {
    setContentForm({
      ...contentForm,
      keywords: contentForm.keywords.filter((k) => k !== keyword),
    });
  };

  const handleGenerateContent = () => {
    if (!contentForm.topic || contentForm.keywords.length === 0) {
      toast.error('Please enter a topic and at least one keyword');
      return;
    }
    generateContentMutation.mutate(contentForm);
  };

  const handleSendMessage = () => {
    if (!currentMessage.trim()) return;

    const message: ChatMessage = {
      message: currentMessage,
      session_id: currentSessionId || undefined,
    };

    sendMessageMutation.mutate(message);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSerpScreenshot(file);
    }
  };

  const handleAnalyzeSerp = () => {
    if (!serpScreenshot) {
      toast.error('Please upload a screenshot');
      return;
    }
    analyzeSerpMutation.mutate({ file: serpScreenshot, keyword: serpKeyword });
  };

  const handleOptimizeVoice = () => {
    if (!voiceOptimization.content || voiceOptimization.target_queries.length === 0) {
      toast.error('Please enter content and target queries');
      return;
    }
    optimizeVoiceMutation.mutate(voiceOptimization);
  };

  const handleOptimizeContent = () => {
    if (!contentOptimization.content || contentOptimization.target_keywords.length === 0) {
      toast.error('Please enter content and target keywords');
      return;
    }
    optimizeContentMutation.mutate(contentOptimization);
  };

  return (
    <>
      <Helmet>
        <title>AI Services - SEO Platform</title>
      </Helmet>

      <Box>
        {/* Header */}
        <Box sx={{ mb: 3 }}>
          <Typography variant="h4" fontWeight={700} gutterBottom>
            AI-Powered SEO Tools
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Advanced AI services for content generation, analysis, and optimization
          </Typography>
        </Box>

        {/* Service Overview Cards */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <AutoFixHigh />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight={600}>
                      Content Generation
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      AI-powered content creation
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
                    <ImageSearch />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight={600}>
                      SERP Analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Visual SERP insights
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
                    <VoiceChat />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight={600}>
                      Voice Optimization
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Voice search ready content
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
                    <SmartToy />
                  </Avatar>
                  <Box>
                    <Typography variant="h6" fontWeight={600}>
                      AI Assistant
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      SEO strategy chat bot
                    </Typography>
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs value={selectedTab} onChange={handleTabChange} aria-label="ai services tabs">
            <Tab label="Content Generation" icon={<AutoFixHigh />} />
            <Tab label="SERP Analysis" icon={<ImageSearch />} />
            <Tab label="Voice Optimization" icon={<RecordVoiceOver />} />
            <Tab label="Content Optimization" icon={<Tune />} />
            <Tab label="AI Chat" icon={<Chat />} />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={selectedTab} index={0}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Content Settings
                  </Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        label="Topic"
                        value={contentForm.topic}
                        onChange={(e) => setContentForm({ ...contentForm, topic: e.target.value })}
                        fullWidth
                        placeholder="Enter your content topic..."
                      />
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Content Type</InputLabel>
                        <Select
                          value={contentForm.content_type}
                          onChange={(e) => setContentForm({ ...contentForm, content_type: e.target.value as ContentType })}
                          label="Content Type"
                        >
                          {Object.values(ContentType).map((type) => (
                            <MenuItem key={type} value={type}>
                              {aiService.getContentTypeLabel(type)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12} sm={6}>
                      <FormControl fullWidth>
                        <InputLabel>Tone</InputLabel>
                        <Select
                          value={contentForm.tone}
                          onChange={(e) => setContentForm({ ...contentForm, tone: e.target.value as ToneType })}
                          label="Tone"
                        >
                          {Object.values(ToneType).map((tone) => (
                            <MenuItem key={tone} value={tone}>
                              {aiService.getToneLabel(tone)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <TextField
                        label="Target Word Count"
                        type="number"
                        value={contentForm.length}
                        onChange={(e) => setContentForm({ ...contentForm, length: Number(e.target.value) })}
                        fullWidth
                        inputProps={{ min: 100, max: 5000 }}
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                        <TextField
                          label="Add Keywords"
                          value={keywordInput}
                          onChange={(e) => setKeywordInput(e.target.value)}
                          onKeyPress={(e) => e.key === 'Enter' && handleAddKeyword()}
                          size="small"
                          sx={{ flexGrow: 1 }}
                        />
                        <Button
                          variant="outlined"
                          onClick={handleAddKeyword}
                          disabled={!keywordInput.trim()}
                        >
                          Add
                        </Button>
                      </Box>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {contentForm.keywords.map((keyword) => (
                          <Chip
                            key={keyword}
                            label={keyword}
                            onDelete={() => handleRemoveKeyword(keyword)}
                            size="small"
                          />
                        ))}
                      </Box>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <TextField
                        label="Additional Instructions"
                        value={contentForm.additional_instructions}
                        onChange={(e) => setContentForm({ ...contentForm, additional_instructions: e.target.value })}
                        multiline
                        rows={3}
                        fullWidth
                        placeholder="Any specific requirements or instructions..."
                      />
                    </Grid>
                    
                    <Grid item xs={12}>
                      <Button
                        variant="contained"
                        startIcon={<AutoFixHigh />}
                        onClick={handleGenerateContent}
                        disabled={generateContentMutation.isLoading}
                        fullWidth
                        size="large"
                      >
                        {generateContentMutation.isLoading ? (
                          <CircularProgress size={20} />
                        ) : (
                          'Generate Content'
                        )}
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              {generatedContent ? (
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                      <Typography variant="h6" fontWeight={600}>
                        Generated Content
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Tooltip title="Copy to clipboard">
                          <IconButton
                            size="small"
                            onClick={() => {
                              navigator.clipboard.writeText(generatedContent.content);
                              toast.success('Copied to clipboard!');
                            }}
                          >
                            <ContentCopy />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Download as text">
                          <IconButton size="small">
                            <Download />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </Box>
                    
                    <Box sx={{ mb: 2 }}>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Word Count: {generatedContent.word_count}
                          </Typography>
                        </Grid>
                        <Grid item xs={6}>
                          <Typography variant="caption" color="text.secondary">
                            Reading Time: {generatedContent.reading_time} min
                          </Typography>
                        </Grid>
                        <Grid item xs={12}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="caption" color="text.secondary">
                              SEO Score:
                            </Typography>
                            <Chip
                              label={`${generatedContent.seo_score}/100`}
                              color={aiService.getSEOScoreColor(generatedContent.seo_score)}
                              size="small"
                            />
                          </Box>
                        </Grid>
                      </Grid>
                    </Box>
                    
                    {generatedContent.meta_title && (
                      <Accordion sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Typography variant="subtitle2">Meta Title</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography variant="body2">{generatedContent.meta_title}</Typography>
                        </AccordionDetails>
                      </Accordion>
                    )}
                    
                    {generatedContent.meta_description && (
                      <Accordion sx={{ mb: 1 }}>
                        <AccordionSummary expandIcon={<ExpandMore />}>
                          <Typography variant="subtitle2">Meta Description</Typography>
                        </AccordionSummary>
                        <AccordionDetails>
                          <Typography variant="body2">{generatedContent.meta_description}</Typography>
                        </AccordionDetails>
                      </Accordion>
                    )}
                    
                    <Paper sx={{ p: 2, bgcolor: 'grey.50', maxHeight: 400, overflow: 'auto' }}>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                        {generatedContent.content}
                      </Typography>
                    </Paper>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent sx={{ textAlign: 'center', py: 8 }}>
                    <Article sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      No content generated yet
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Fill in the form and click "Generate Content" to get started
                    </Typography>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        </TabPanel>

        <TabPanel value={selectedTab} index={1}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                SERP Screenshot Analysis
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Box sx={{ mb: 2 }}>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      style={{ display: 'none' }}
                      ref={fileInputRef}
                    />
                    <Button
                      variant="outlined"
                      startIcon={<CloudUpload />}
                      onClick={() => fileInputRef.current?.click()}
                      fullWidth
                      sx={{ mb: 2 }}
                    >
                      Upload SERP Screenshot
                    </Button>
                    
                    {serpScreenshot && (
                      <Alert severity="success" sx={{ mb: 2 }}>
                        File uploaded: {serpScreenshot.name}
                      </Alert>
                    )}
                  </Box>
                  
                  <TextField
                    label="Target Keyword (Optional)"
                    value={serpKeyword}
                    onChange={(e) => setSerpKeyword(e.target.value)}
                    fullWidth
                    sx={{ mb: 2 }}
                    placeholder="Enter the keyword you searched for..."
                  />
                  
                  <Button
                    variant="contained"
                    startIcon={<ImageSearch />}
                    onClick={handleAnalyzeSerp}
                    disabled={!serpScreenshot || analyzeSerpMutation.isLoading}
                    fullWidth
                  >
                    {analyzeSerpMutation.isLoading ? (
                      <CircularProgress size={20} />
                    ) : (
                      'Analyze SERP'
                    )}
                  </Button>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', textAlign: 'center', minHeight: 200 }}>
                    <CameraAlt sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      AI Vision Analysis
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Upload a SERP screenshot to get detailed AI-powered insights about:
                    </Typography>
                    <Box component="ul" sx={{ textAlign: 'left', mt: 2 }}>
                      <Typography component="li" variant="body2">Competitor analysis</Typography>
                      <Typography component="li" variant="body2">SERP features detection</Typography>
                      <Typography component="li" variant="body2">Ranking opportunities</Typography>
                      <Typography component="li" variant="body2">Content gaps analysis</Typography>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={2}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Voice Search Optimization
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Content to Optimize"
                    value={voiceOptimization.content}
                    onChange={(e) => setVoiceOptimization({ ...voiceOptimization, content: e.target.value })}
                    multiline
                    rows={6}
                    fullWidth
                    sx={{ mb: 2 }}
                    placeholder="Paste your content here to optimize for voice search..."
                  />
                  
                  <TextField
                    label="Target Voice Queries"
                    value={voiceOptimization.target_queries.join(', ')}
                    onChange={(e) => setVoiceOptimization({
                      ...voiceOptimization,
                      target_queries: e.target.value.split(',').map(q => q.trim()).filter(q => q)
                    })}
                    fullWidth
                    sx={{ mb: 2 }}
                    placeholder="How do I..., What is the best..., Where can I find..."
                    helperText="Enter voice search queries separated by commas"
                  />
                  
                  <Button
                    variant="contained"
                    startIcon={<RecordVoiceOver />}
                    onClick={handleOptimizeVoice}
                    disabled={optimizeVoiceMutation.isLoading}
                    fullWidth
                  >
                    {optimizeVoiceMutation.isLoading ? (
                      <CircularProgress size={20} />
                    ) : (
                      'Optimize for Voice Search'
                    )}
                  </Button>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', minHeight: 300 }}>
                    <VoiceChat sx={{ fontSize: 64, color: 'text.secondary', mb: 2, display: 'block', mx: 'auto' }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom textAlign="center">
                      Voice Search Features
                    </Typography>
                    <Box component="ul" sx={{ pl: 2 }}>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Natural language optimization
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        FAQ schema generation
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Voice snippet optimization
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Conversational keyword variations
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>
                Content Optimization
              </Typography>
              
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <TextField
                    label="Content to Optimize"
                    value={contentOptimization.content}
                    onChange={(e) => setContentOptimization({ ...contentOptimization, content: e.target.value })}
                    multiline
                    rows={8}
                    fullWidth
                    sx={{ mb: 2 }}
                    placeholder="Paste your existing content here for SEO optimization..."
                  />
                  
                  <TextField
                    label="Target Keywords"
                    value={contentOptimization.target_keywords.join(', ')}
                    onChange={(e) => setContentOptimization({
                      ...contentOptimization,
                      target_keywords: e.target.value.split(',').map(k => k.trim()).filter(k => k)
                    })}
                    fullWidth
                    sx={{ mb: 2 }}
                    placeholder="keyword1, keyword2, keyword3"
                    helperText="Enter target keywords separated by commas"
                  />
                  
                  <Button
                    variant="contained"
                    startIcon={<Tune />}
                    onClick={handleOptimizeContent}
                    disabled={optimizeContentMutation.isLoading}
                    fullWidth
                  >
                    {optimizeContentMutation.isLoading ? (
                      <CircularProgress size={20} />
                    ) : (
                      'Optimize Content'
                    )}
                  </Button>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', minHeight: 350 }}>
                    <Analytics sx={{ fontSize: 64, color: 'text.secondary', mb: 2, display: 'block', mx: 'auto' }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom textAlign="center">
                      Optimization Features
                    </Typography>
                    <Box component="ul" sx={{ pl: 2 }}>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Keyword density analysis
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Readability score improvement
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Heading structure optimization
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        Internal linking suggestions
                      </Typography>
                      <Typography component="li" variant="body2" sx={{ mb: 1 }}>
                        SEO best practices recommendations
                      </Typography>
                    </Box>
                  </Paper>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </TabPanel>

        <TabPanel value={selectedTab} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card sx={{ height: 600, display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    AI SEO Assistant
                  </Typography>
                  
                  <Paper
                    sx={{
                      flexGrow: 1,
                      p: 2,
                      mb: 2,
                      overflow: 'auto',
                      bgcolor: 'grey.50',
                      minHeight: 400,
                    }}
                  >
                    {chatMessages.length === 0 ? (
                      <Box sx={{ textAlign: 'center', py: 4 }}>
                        <SmartToy sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                          AI SEO Assistant
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Ask me anything about SEO strategy, keyword research, content optimization, or technical SEO!
                        </Typography>
                      </Box>
                    ) : (
                      <List>
                        {chatMessages.map((message, index) => (
                          <ListItem key={index} sx={{ flexDirection: 'column', alignItems: 'flex-start' }}>
                            <Box
                              sx={{
                                display: 'flex',
                                alignItems: 'center',
                                mb: 1,
                                alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                              }}
                            >
                              {message.role === 'assistant' && (
                                <Avatar sx={{ bgcolor: 'primary.main', mr: 1, width: 32, height: 32 }}>
                                  <SmartToy fontSize="small" />
                                </Avatar>
                              )}
                              <Paper
                                sx={{
                                  p: 2,
                                  maxWidth: '70%',
                                  bgcolor: message.role === 'user' ? 'primary.main' : 'background.paper',
                                  color: message.role === 'user' ? 'primary.contrastText' : 'text.primary',
                                }}
                              >
                                <Typography variant="body2">{message.content}</Typography>
                              </Paper>
                              {message.role === 'user' && (
                                <Avatar sx={{ bgcolor: 'secondary.main', ml: 1, width: 32, height: 32 }}>
                                  <Typography variant="caption">You</Typography>
                                </Avatar>
                              )}
                            </Box>
                          </ListItem>
                        ))}
                      </List>
                    )}
                  </Paper>
                  
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <TextField
                      label="Ask the AI assistant..."
                      value={currentMessage}
                      onChange={(e) => setCurrentMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                      fullWidth
                      multiline
                      maxRows={3}
                      placeholder="How can I improve my keyword rankings?"
                    />
                    <Button
                      variant="contained"
                      onClick={handleSendMessage}
                      disabled={!currentMessage.trim() || sendMessageMutation.isLoading}
                      sx={{ minWidth: 'auto', px: 2 }}
                    >
                      {sendMessageMutation.isLoading ? (
                        <CircularProgress size={20} />
                      ) : (
                        <Send />
                      )}
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Chat History
                  </Typography>
                  
                  {chatSessions && chatSessions.sessions.length > 0 ? (
                    <List>
                      {chatSessions.sessions.slice(0, 5).map((session) => (
                        <ListItem key={session.id} button>
                          <ListItemAvatar>
                            <Avatar sx={{ bgcolor: 'info.main' }}>
                              <Chat />
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText
                            primary={`Session ${session.id.slice(-6)}`}
                            secondary={`${session.message_count} messages • ${format(new Date(session.created_at), 'MMM dd')}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ py: 4 }}>
                      No chat history yet
                    </Typography>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Box>
    </>
  );
};

export default AIServices;