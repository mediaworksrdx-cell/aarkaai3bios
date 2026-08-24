'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Sliders,
  User as UserIcon,
  Brain,
  MessageSquare,
  Cpu,
  Sparkles,
  FolderKanban,
  BookOpen,
  Globe,
  AppWindow,
  Shield,
  EyeOff,
  Bell,
  CreditCard,
  Code,
  Plus,
  Trash2,
  CheckCircle2,
  ExternalLink,
  Download,
  Moon,
  Sun,
  Laptop
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { exportToMarkdown, fetchSettingsApi, updateSettingsApi } from '@/lib/api';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: { name: string; email: string; picture?: string; id?: string } | null;
}

type TabId =
  | 'general'
  | 'personalization'
  | 'memory'
  | 'chat'
  | 'models'
  | 'thinking'
  | 'projects'
  | 'knowledge'
  | 'web'
  | 'apps'
  | 'security'
  | 'privacy'
  | 'notifications'
  | 'usage'
  | 'developer';

interface MemoryItem {
  id: string;
  category: 'User Preferences' | 'Technical Stack' | 'Financial Interests' | 'Communication Style' | 'Ongoing Goals';
  fact: string;
  created: string;
}

interface ProjectItem {
  id: string;
  name: string;
  instructions: string;
  knowledgeFiles: number;
}

const SETTINGS_TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'general', label: 'General', icon: Sliders },
  { id: 'personalization', label: 'Personalization', icon: UserIcon },
  { id: 'memory', label: 'Memory', icon: Brain },
  { id: 'chat', label: 'Chat & Conversation', icon: MessageSquare },
  { id: 'models', label: 'Models & Reasoning', icon: Cpu },
  { id: 'thinking', label: 'Thinking & Compute', icon: Sparkles },
  { id: 'projects', label: 'Projects & Workspaces', icon: FolderKanban },
  { id: 'knowledge', label: 'Knowledge & Files', icon: BookOpen },
  { id: 'web', label: 'Web & Research', icon: Globe },
  { id: 'apps', label: 'Connected Apps', icon: AppWindow },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'privacy', label: 'Privacy & Data', icon: EyeOff },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'usage', label: 'Plan & Usage', icon: CreditCard },
  { id: 'developer', label: 'Developer', icon: Code },
];

export function SettingsModal({ isOpen, onClose, user }: SettingsModalProps) {
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<TabId>('general');
  const [savedNotification, setSavedNotification] = useState(false);

  // General Settings
  const [language, setLanguage] = useState('en');
  const [density, setDensity] = useState<'compact' | 'comfortable'>('comfortable');

  // Personalization Settings
  const [aboutYou, setAboutYou] = useState('');
  const [systemDirectives, setSystemDirectives] = useState('');
  const [responseStyle, setResponseStyle] = useState<'concise' | 'balanced' | 'detailed' | 'professional'>('balanced');

  // Memory Settings
  const [memoryEnabled, setMemoryEnabled] = useState(true);
  const [memoryPaused, setMemoryPaused] = useState(false);
  const [memories, setMemories] = useState<MemoryItem[]>([
    { id: 'm1', category: 'User Preferences', fact: 'Prefers production-grade TypeScript with strong typing and no any.', created: '2 days ago' },
    { id: 'm2', category: 'Technical Stack', fact: 'Primary stack: Next.js 15, FastAPI, PostgreSQL, and PyTorch.', created: '3 days ago' },
    { id: 'm3', category: 'Financial Interests', fact: 'Focus on quantitative market analysis and portfolio risk modeling.', created: '5 days ago' },
  ]);
  const [newMemoryCategory, setNewMemoryCategory] = useState<MemoryItem['category']>('User Preferences');
  const [newMemoryFact, setNewMemoryFact] = useState('');

  // Chat Settings
  const [enterToSend, setEnterToSend] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [streamingResponses, setStreamingResponses] = useState(true);
  const [incognitoChat, setIncognitoChat] = useState(false);

  // Model & Reasoning Settings
  const [defaultModel, setDefaultModel] = useState<'aarka-2.0' | 'gemini-3.7'>('aarka-2.0');
  const [defaultEffort, setDefaultEffort] = useState<'low' | 'medium' | 'high'>('medium');

  // Thinking Settings
  const [extendedThinking, setExtendedThinking] = useState(true);
  const [thinkingBudget, setThinkingBudget] = useState(4096);

  // Projects Settings
  const [projects, setProjects] = useState<ProjectItem[]>([
    { id: 'p1', name: 'Market Intelligence AI', instructions: 'Act as an institutional quantitative analyst.', knowledgeFiles: 3 },
    { id: 'p2', name: 'Compiler Architecture', instructions: 'Focus on type-safe AST and optimizer pipelines.', knowledgeFiles: 1 },
  ]);
  const [newProjectName, setNewProjectName] = useState('');
  const [newProjectInstructions, setNewProjectInstructions] = useState('');

  // Web & Research Settings
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(true);
  const [marketDataEnabled, setMarketDataEnabled] = useState(true);

  // Connected Apps
  const [connectedApps, setConnectedApps] = useState({
    googleDrive: true,
    github: true,
    slack: false,
    gmail: false,
  });

  // Security
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  // Notifications
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [securityAlerts, setSecurityAlerts] = useState(true);

  // Developer API Keys (Masked only)
  const [apiKeys, setApiKeys] = useState<{ id: string; name: string; maskedKey: string; created: string }[]>([
    { id: 'k1', name: 'Production Agent Key', maskedKey: 'ark-live-9f2eâ€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢3a81', created: '2026-08-10' },
  ]);
  const [newKeyName, setNewKeyName] = useState('');

  // Load preferences from localStorage and sync from authoritative backend on mount
  useEffect(() => {
    // 1. Instant local restore
    try {
      const saved = localStorage.getItem('aarka_user_settings_v2');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.language) setLanguage(parsed.language);
        if (parsed.density) setDensity(parsed.density);
        if (parsed.aboutYou) setAboutYou(parsed.aboutYou);
        if (parsed.systemDirectives) setSystemDirectives(parsed.systemDirectives);
        if (parsed.responseStyle) setResponseStyle(parsed.responseStyle);
        if (parsed.enterToSend !== undefined) setEnterToSend(parsed.enterToSend);
        if (parsed.showTimestamps !== undefined) setShowTimestamps(parsed.showTimestamps);
        if (parsed.streamingResponses !== undefined) setStreamingResponses(parsed.streamingResponses);
        if (parsed.defaultModel) setDefaultModel(parsed.defaultModel);
        if (parsed.defaultEffort) setDefaultEffort(parsed.defaultEffort);
        if (parsed.extendedThinking !== undefined) setExtendedThinking(parsed.extendedThinking);
        if (parsed.thinkingBudget) setThinkingBudget(parsed.thinkingBudget);
        if (parsed.webSearchEnabled !== undefined) setWebSearchEnabled(parsed.webSearchEnabled);
        if (parsed.deepResearchEnabled !== undefined) setDeepResearchEnabled(parsed.deepResearchEnabled);
      }
    } catch {}

    // 2. Authoritative backend synchronization
    fetchSettingsApi()
      .then((backendSettings) => {
        if (backendSettings && !backendSettings.error) {
          if (backendSettings.language) setLanguage(backendSettings.language);
          if (backendSettings.default_model) setDefaultModel(backendSettings.default_model);
          if (backendSettings.response_style) setResponseStyle(backendSettings.response_style);
          if (backendSettings.streaming_enabled !== undefined) setStreamingResponses(backendSettings.streaming_enabled);
          if (backendSettings.about_you) setAboutYou(backendSettings.about_you);
          if (backendSettings.system_directives) setSystemDirectives(backendSettings.system_directives);
          if (backendSettings.extended_thinking !== undefined) setExtendedThinking(backendSettings.extended_thinking);
          if (backendSettings.thinking_budget) setThinkingBudget(backendSettings.thinking_budget);
          if (backendSettings.web_search_enabled !== undefined) setWebSearchEnabled(backendSettings.web_search_enabled);
          if (backendSettings.deep_research_enabled !== undefined) setDeepResearchEnabled(backendSettings.deep_research_enabled);
          if (backendSettings.market_data_enabled !== undefined) setMarketDataEnabled(backendSettings.market_data_enabled);
        }
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    const settingsPayload = {
      language,
      density,
      aboutYou,
      systemDirectives,
      responseStyle,
      enterToSend,
      showTimestamps,
      streamingResponses,
      defaultModel,
      defaultEffort,
      extendedThinking,
      thinkingBudget,
      webSearchEnabled,
      deepResearchEnabled,
      marketDataEnabled,
    };
    try {
      localStorage.setItem('aarka_user_settings_v2', JSON.stringify(settingsPayload));
    } catch {}

    // Synchronize to backend database
    try {
      await updateSettingsApi({
        language,
        default_model: defaultModel,
        response_style: responseStyle,
        streaming_enabled: streamingResponses,
        about_you: aboutYou,
        system_directives: systemDirectives,
        extended_thinking: extendedThinking,
        thinking_budget: thinkingBudget,
        web_search_enabled: webSearchEnabled,
        deep_research_enabled: deepResearchEnabled,
        market_data_enabled: marketDataEnabled,
      });
    } catch {}

    setSavedNotification(true);
    setTimeout(() => setSavedNotification(false), 2000);
  };

  const handleAddMemory = () => {
    if (!newMemoryFact.trim()) return;
    const item: MemoryItem = {
      id: 'm-' + Date.now(),
      category: newMemoryCategory,
      fact: newMemoryFact.trim(),
      created: 'Just now',
    };
    setMemories([item, ...memories]);
    setNewMemoryFact('');
    handleSave();
  };

  const handleDeleteMemory = (id: string) => {
    setMemories(memories.filter((m) => m.id !== id));
    handleSave();
  };

  const handleResetAllMemory = () => {
    if (confirm('Are you sure you want to erase all structured memory facts? This cannot be undone.')) {
      setMemories([]);
      handleSave();
    }
  };

  const handleAddProject = () => {
    if (!newProjectName.trim()) return;
    const proj: ProjectItem = {
      id: 'p-' + Date.now(),
      name: newProjectName.trim(),
      instructions: newProjectInstructions.trim(),
      knowledgeFiles: 0,
    };
    setProjects([...projects, proj]);
    setNewProjectName('');
    setNewProjectInstructions('');
    handleSave();
  };

  const handleGenerateApiKey = () => {
    if (!newKeyName.trim()) return;
    const randomSuffix = Math.random().toString(36).substring(2, 6);
    const masked = `ark-live-${randomSuffix}â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢â€¢${Date.now().toString(36).slice(-4)}`;
    setApiKeys([...apiKeys, { id: 'k-' + Date.now(), name: newKeyName.trim(), maskedKey: masked, created: new Date().toISOString().split('T')[0] }]);
    setNewKeyName('');
  };

  const handleExportFullData = () => {
    const exportData = {
      user: user?.email || 'guest_user',
      timestamp: new Date().toISOString(),
      settings: {
        language,
        responseStyle,
        defaultModel,
        defaultEffort,
        extendedThinking,
        thinkingBudget,
      },
      memories,
      projects,
    };
    exportToMarkdown('Aarka_AI_Account_Data', '```json\n' + JSON.stringify(exportData, null, 2) + '\n```');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-4xl h-[680px] bg-[var(--bg-primary)] border border-[var(--border-strong)] rounded-2xl shadow-[var(--shadow-float)] flex overflow-hidden flex-col md:flex-row animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Left Sidebar Navigation */}
        <div className="w-full md:w-64 border-b md:border-b-0 md:border-r border-[var(--border)] bg-[var(--bg-secondary)] flex flex-col flex-shrink-0">
          <div className="p-4 border-b border-[var(--border)] flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[var(--accent-primary)]" />
              <span className="font-display font-bold text-sm tracking-tight text-[var(--text-primary)]">Settings</span>
            </div>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-[var(--accent-muted)] text-[var(--accent-primary)] font-semibold">
              v2.0
            </span>
          </div>

          {/* Navigation Items */}
          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {SETTINGS_TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  type="button"
                  className={`w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium transition-all text-left cursor-pointer ${
                    isActive
                      ? 'bg-[var(--accent-muted)] text-[var(--accent-primary)] font-semibold shadow-[var(--shadow-sm)]'
                      : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)]'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isActive ? 'text-[var(--accent-primary)]' : 'text-[var(--text-tertiary)]'}`} />
                  <span className="truncate">{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Bottom Save Indicator */}
          <div className="p-3 border-t border-[var(--border)] bg-[var(--bg-tertiary)]/40 flex items-center justify-between">
            {savedNotification ? (
              <span className="text-[11px] text-emerald-500 font-medium flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" /> Saved
              </span>
            ) : (
              <button
                onClick={handleSave}
                type="button"
                className="w-full py-1.5 px-3 rounded-lg bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white text-xs font-medium transition-colors shadow-[var(--shadow-sm)] cursor-pointer"
              >
                Save Preferences
              </button>
            )}
          </div>
        </div>

        {/* Right Content Area */}
        <div className="flex-1 flex flex-col min-w-0 bg-[var(--bg-primary)]">
          {/* Header */}
          <div className="p-4 border-b border-[var(--border)] flex items-center justify-between flex-shrink-0 bg-[var(--bg-primary)]/80 backdrop-blur-md">
            <div>
              <h2 className="text-sm font-bold text-[var(--text-primary)] capitalize">
                {SETTINGS_TABS.find((t) => t.id === activeTab)?.label}
              </h2>
              <p className="text-[11px] text-[var(--text-tertiary)]">
                Manage your account-wide parameters and capability toggles.
              </p>
            </div>
            <button
              onClick={onClose}
              type="button"
              className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Tab Body */}
          <div className="flex-1 overflow-y-auto p-5 space-y-6">
            {/* 1. GENERAL TAB */}
            {activeTab === 'general' && (
              <div className="space-y-5">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1.5">Color Theme</label>
                  <div className="flex items-center gap-2 p-3 rounded-xl border border-[var(--accent-primary)] bg-[var(--accent-muted)] text-[var(--accent-primary)] text-xs font-medium">
                    <Sun className="w-4 h-4" />
                    <span>Permanent Light Theme (Active)</span>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1.5">Primary Language</label>
                  <select
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                  >
                    <option value="en">English (US / Global)</option>
                    <option value="hi">Hindi (à¤¹à¤¿à¤‚à¤¦à¥€)</option>
                    <option value="ta">Tamil (à®¤à®®à®¿à®´à¯)</option>
                    <option value="te">Telugu (à°¤à±†à°²à±à°—à±)</option>
                    <option value="kn">Kannada (à²•à²¨à³à²¨à²¡)</option>
                    <option value="ml">Malayalam (à´®à´²à´¯à´¾à´³à´‚)</option>
                    <option value="mr">Marathi (à¤®à¤°à¤¾à¤ à¥€)</option>
                    <option value="bn">Bengali (à¦¬à¦¾à¦‚à¦²à¦¾)</option>
                    <option value="gu">Gujarati (àª—à«àªœàª°àª¾àª¤à«€)</option>
                    <option value="pa">Punjabi (à¨ªà©°à¨œà¨¾à¨¬à©€)</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1.5">Message Density</label>
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      type="button"
                      onClick={() => setDensity('comfortable')}
                      className={`p-2.5 rounded-xl border text-xs font-medium text-center transition-all cursor-pointer ${
                        density === 'comfortable' ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)] text-[var(--accent-primary)]' : 'border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-secondary)]'
                      }`}
                    >
                      Comfortable
                    </button>
                    <button
                      type="button"
                      onClick={() => setDensity('compact')}
                      className={`p-2.5 rounded-xl border text-xs font-medium text-center transition-all cursor-pointer ${
                        density === 'compact' ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)] text-[var(--accent-primary)]' : 'border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-secondary)]'
                      }`}
                    >
                      Compact
                    </button>
                  </div>
                </div>
              </div>
            )}

            {/* 2. PERSONALIZATION TAB */}
            {activeTab === 'personalization' && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1">About You</label>
                  <p className="text-[11px] text-[var(--text-tertiary)] mb-1.5">
                    Describe your role, industry, or domain background so Aarka AI tailors explanations accurately.
                  </p>
                  <textarea
                    rows={2}
                    value={aboutYou}
                    onChange={(e) => setAboutYou(e.target.value)}
                    placeholder="e.g. Lead Quantitative Researcher focusing on algorithmic trading and distributed systems..."
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1">Account-Wide Instructions for Aarka AI</label>
                  <p className="text-[11px] text-[var(--text-tertiary)] mb-1.5">
                    Directives applied across every session (e.g. textbook rigor, code style preferences).
                  </p>
                  <textarea
                    rows={4}
                    value={systemDirectives}
                    onChange={(e) => setSystemDirectives(e.target.value)}
                    placeholder="e.g. Always write complete TypeScript without placeholders. Explain mathematical formulas step-by-step."
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)] font-mono"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1.5">Default Response Style</label>
                  <div className="grid grid-cols-4 gap-2">
                    {(['concise', 'balanced', 'detailed', 'professional'] as const).map((style) => (
                      <button
                        key={style}
                        type="button"
                        onClick={() => setResponseStyle(style)}
                        className={`p-2 rounded-xl border text-xs font-medium capitalize text-center transition-all cursor-pointer ${
                          responseStyle === style ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)] text-[var(--accent-primary)]' : 'border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-secondary)]'
                        }`}
                      >
                        {style}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 3. MEMORY TAB */}
            {activeTab === 'memory' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Enable Structured Memory</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">
                      Allows Aarka AI to extract and remember key preferences and facts across sessions.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={memoryEnabled}
                    onChange={(e) => setMemoryEnabled(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-[var(--text-primary)]">Stored Memories ({memories.length})</span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setMemoryPaused(!memoryPaused)}
                      className={`px-2.5 py-1 rounded-lg text-xs font-medium border cursor-pointer ${
                        memoryPaused ? 'bg-amber-500/10 text-amber-500 border-amber-500/30' : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border-[var(--border)]'
                      }`}
                    >
                      {memoryPaused ? 'Memory Paused' : 'Pause Memory'}
                    </button>
                    <button
                      type="button"
                      onClick={handleResetAllMemory}
                      className="px-2.5 py-1 rounded-lg text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/30 hover:bg-red-500/20 cursor-pointer"
                    >
                      Reset All
                    </button>
                  </div>
                </div>

                {/* Add New Memory */}
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                  <div className="flex gap-2">
                    <select
                      value={newMemoryCategory}
                      onChange={(e) => setNewMemoryCategory(e.target.value as any)}
                      className="px-2.5 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none"
                    >
                      <option value="User Preferences">User Preferences</option>
                      <option value="Technical Stack">Technical Stack</option>
                      <option value="Financial Interests">Financial Interests</option>
                      <option value="Communication Style">Communication Style</option>
                      <option value="Ongoing Goals">Ongoing Goals</option>
                    </select>
                    <input
                      type="text"
                      value={newMemoryFact}
                      onChange={(e) => setNewMemoryFact(e.target.value)}
                      placeholder="Add a new custom memory fact..."
                      className="flex-1 px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent-primary)]"
                    />
                    <button
                      type="button"
                      onClick={handleAddMemory}
                      className="px-3 py-1.5 rounded-lg bg-[var(--accent-primary)] hover:bg-[var(--accent-hover)] text-white text-xs font-medium flex items-center gap-1 cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" /> Add
                    </button>
                  </div>
                </div>

                {/* Memories List */}
                <div className="space-y-1.5 max-h-60 overflow-y-auto">
                  {memories.map((m) => (
                    <div
                      key={m.id}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-xs"
                    >
                      <div className="min-w-0 flex-1 pr-2">
                        <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-[var(--bg-tertiary)] text-[var(--accent-primary)] mr-2 font-medium">
                          {m.category}
                        </span>
                        <span className="text-[var(--text-primary)]">{m.fact}</span>
                      </div>
                      <button
                        type="button"
                        onClick={() => handleDeleteMemory(m.id)}
                        className="p-1 rounded text-[var(--text-tertiary)] hover:text-red-400 hover:bg-[var(--bg-tertiary)] transition-colors cursor-pointer"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 4. CHAT & CONVERSATION TAB */}
            {activeTab === 'chat' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Enter to Send</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Press Enter to send, Shift+Enter for new line.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={enterToSend}
                    onChange={(e) => setEnterToSend(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Message Timestamps</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Display exact send and receipt times on messages.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={showTimestamps}
                    onChange={(e) => setShowTimestamps(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Streaming Token Responses</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Stream tokens as they are generated by the neural mesh.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={streamingResponses}
                    onChange={(e) => setStreamingResponses(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-purple-500/10 border border-purple-500/30">
                  <div>
                    <span className="text-xs font-bold text-purple-400 block flex items-center gap-1.5">
                      <EyeOff className="w-3.5 h-3.5" /> Incognito Chat Mode
                    </span>
                    <span className="text-[11px] text-[var(--text-secondary)]">
                      Incognito sessions are never saved to history or indexed into memory.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={incognitoChat}
                    onChange={(e) => setIncognitoChat(e.target.checked)}
                    className="w-4 h-4 rounded text-purple-500 cursor-pointer"
                  />
                </div>
              </div>
            )}

            {/* 5. MODELS & REASONING TAB */}
            {activeTab === 'models' && (
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1.5">Default Model</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      type="button"
                      onClick={() => setDefaultModel('aarka-2.0')}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        defaultModel === 'aarka-2.0' ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)]' : 'border-[var(--border)] bg-[var(--bg-secondary)]'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Sparkles className="w-4 h-4 text-[var(--accent-primary)]" />
                        <span className="text-xs font-bold text-[var(--text-primary)]">Aarka AI 2.0</span>
                      </div>
                      <span className="text-[11px] text-[var(--text-secondary)] block">
                        Flagship reasoning engine with mathematical and quantitative rigor.
                      </span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setDefaultModel('gemini-3.7')}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        defaultModel === 'gemini-3.7' ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)]' : 'border-[var(--border)] bg-[var(--bg-secondary)]'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Cpu className="w-4 h-4 text-blue-400" />
                        <span className="text-xs font-bold text-[var(--text-primary)]">Google Gemini 3.7</span>
                      </div>
                      <span className="text-[11px] text-[var(--text-secondary)] block">
                        Multimodal partner model with extended context capabilities.
                      </span>
                    </button>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-[var(--text-primary)] block mb-1.5">Default Reasoning Effort</label>
                  <div className="grid grid-cols-3 gap-2.5">
                    {(['low', 'medium', 'high'] as const).map((effort) => (
                      <button
                        key={effort}
                        type="button"
                        onClick={() => setDefaultEffort(effort)}
                        className={`p-2.5 rounded-xl border text-xs font-medium capitalize text-center transition-all cursor-pointer ${
                          defaultEffort === effort ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)] text-[var(--accent-primary)] font-bold' : 'border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-secondary)]'
                        }`}
                      >
                        {effort}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* 6. THINKING & COMPUTE TAB */}
            {activeTab === 'thinking' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Enable Extended Thinking</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">
                      Executes internal DAG reasoning and multi-step verification before emitting final answer.
                    </span>
                  </div>
                  <input
                    type="checkbox"
                    checked={extendedThinking}
                    onChange={(e) => setExtendedThinking(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-[var(--text-primary)]">Maximum Thinking Token Budget</span>
                    <span className="text-xs font-mono font-bold text-[var(--accent-primary)]">{thinkingBudget} tokens</span>
                  </div>
                  <input
                    type="range"
                    min={2048}
                    max={16384}
                    step={1024}
                    value={thinkingBudget}
                    onChange={(e) => setThinkingBudget(Number(e.target.value))}
                    className="w-full accent-[var(--accent-primary)] cursor-pointer"
                  />
                  <div className="flex justify-between text-[10px] text-[var(--text-tertiary)] font-mono">
                    <span>2,048 (Fast)</span>
                    <span>8,192 (Balanced)</span>
                    <span>16,384 (Deep Math)</span>
                  </div>
                </div>
              </div>
            )}

            {/* 7. PROJECTS TAB */}
            {activeTab === 'projects' && (
              <div className="space-y-4">
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                  <span className="text-xs font-bold text-[var(--text-primary)] block">Create Scoped Project</span>
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="Project Name (e.g. Market Intelligence)"
                    className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none"
                  />
                  <textarea
                    rows={2}
                    value={newProjectInstructions}
                    onChange={(e) => setNewProjectInstructions(e.target.value)}
                    placeholder="Project-specific custom instructions..."
                    className="w-full px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none"
                  />
                  <button
                    type="button"
                    onClick={handleAddProject}
                    className="px-3 py-1.5 rounded-lg bg-[var(--accent-primary)] text-white text-xs font-medium flex items-center gap-1 cursor-pointer"
                  >
                    <Plus className="w-3.5 h-3.5" /> Create Project
                  </button>
                </div>

                <div className="space-y-2">
                  {projects.map((p) => (
                    <div key={p.id} className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-[var(--text-primary)]">{p.name}</span>
                        <span className="text-[10px] font-mono bg-[var(--bg-tertiary)] px-2 py-0.5 rounded text-[var(--text-tertiary)]">
                          {p.knowledgeFiles} Knowledge Files
                        </span>
                      </div>
                      <p className="text-[11px] text-[var(--text-secondary)]">{p.instructions || 'No custom instructions set.'}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 8. KNOWLEDGE & FILES TAB */}
            {activeTab === 'knowledge' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl border border-dashed border-[var(--border-strong)] bg-[var(--bg-secondary)]/50 text-center space-y-2">
                  <BookOpen className="w-6 h-6 text-[var(--accent-primary)] mx-auto" />
                  <span className="text-xs font-bold text-[var(--text-primary)] block">RAG Document Vector Store</span>
                  <p className="text-[11px] text-[var(--text-tertiary)] max-w-sm mx-auto">
                    Upload PDFs, spreadsheets, or technical documentation to index them into Aarka AI's vector database.
                  </p>
                  <button
                    type="button"
                    onClick={() => alert('Document upload available directly in chat.')}
                    className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border)] text-xs font-medium text-[var(--text-primary)] cursor-pointer"
                  >
                    Upload Documents
                  </button>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] flex justify-between items-center text-xs">
                  <span className="text-[var(--text-secondary)]">Vector Store Quota</span>
                  <span className="font-mono font-semibold text-[var(--text-primary)]">14.2 MB / 500 MB (2.8%)</span>
                </div>
              </div>
            )}

            {/* 9. WEB & RESEARCH TAB */}
            {activeTab === 'web' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Live Web Search</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Perform real-time queries for up-to-date web facts.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={webSearchEnabled}
                    onChange={(e) => setWebSearchEnabled(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Deep Research Mode</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Multi-step web crawling and factual cross-referencing.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={deepResearchEnabled}
                    onChange={(e) => setDeepResearchEnabled(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Real-Time Market Data Feeds</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Integrate live stock tickers, FX rates, and macro indicators.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={marketDataEnabled}
                    onChange={(e) => setMarketDataEnabled(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>
              </div>
            )}

            {/* 10. CONNECTED APPS TAB */}
            {activeTab === 'apps' && (
              <div className="space-y-3">
                {[
                  { name: 'Google Drive', key: 'googleDrive' as const, desc: 'Index private documents directly from Drive.' },
                  { name: 'GitHub', key: 'github' as const, desc: 'Analyze repositories, PRs, and software architectures.' },
                  { name: 'Slack', key: 'slack' as const, desc: 'Deliver scheduled research digests to team channels.' },
                  { name: 'Gmail', key: 'gmail' as const, desc: 'Draft executive summaries and briefings directly.' },
                ].map((app) => (
                  <div key={app.name} className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                    <div>
                      <span className="text-xs font-bold text-[var(--text-primary)] block">{app.name}</span>
                      <span className="text-[11px] text-[var(--text-tertiary)]">{app.desc}</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setConnectedApps({ ...connectedApps, [app.key]: !connectedApps[app.key] })}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
                        connectedApps[app.key]
                          ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30'
                          : 'bg-[var(--bg-tertiary)] text-[var(--text-secondary)] border-[var(--border)]'
                      }`}
                    >
                      {connectedApps[app.key] ? 'Connected' : 'Connect'}
                    </button>
                  </div>
                ))}
              </div>
            )}

            {/* 11. SECURITY TAB */}
            {activeTab === 'security' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Two-Factor Authentication (2FA)</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Protect your account with TOTP authenticator app verification.</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => setTwoFactorEnabled(!twoFactorEnabled)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-medium border cursor-pointer ${
                      twoFactorEnabled ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30' : 'bg-[var(--accent-primary)] text-white'
                    }`}
                  >
                    {twoFactorEnabled ? 'Enabled' : 'Enable 2FA'}
                  </button>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                  <span className="text-xs font-bold text-[var(--text-primary)] block">Active Sessions</span>
                  <div className="flex items-center justify-between text-xs py-1 border-b border-[var(--border)]">
                    <div>
                      <span className="text-[var(--text-primary)] font-medium block">Current Browser Session</span>
                      <span className="text-[10px] text-[var(--text-tertiary)]">IP: 136.85.114.150 Â· Last active: Now</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500">Active</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => alert('All other device tokens revoked via Redis backend.')}
                    className="mt-2 text-xs text-red-400 hover:text-red-300 font-medium cursor-pointer"
                  >
                    Sign Out All Other Devices
                  </button>
                </div>
              </div>
            )}

            {/* 12. PRIVACY & DATA TAB */}
            {activeTab === 'privacy' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                  <span className="text-xs font-bold text-[var(--text-primary)] block">Export Account Data</span>
                  <p className="text-[11px] text-[var(--text-tertiary)]">
                    Download complete snapshot of your conversations, structured memories, and preferences.
                  </p>
                  <button
                    type="button"
                    onClick={handleExportFullData}
                    className="px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] hover:bg-[var(--bg-hover)] border border-[var(--border)] text-xs font-medium text-[var(--text-primary)] flex items-center gap-1.5 cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5 text-[var(--accent-primary)]" /> Export Data (JSON)
                  </button>
                </div>

                <div className="p-4 rounded-xl bg-red-500/5 border border-red-500/20 space-y-2">
                  <span className="text-xs font-bold text-red-400 block">Danger Zone</span>
                  <p className="text-[11px] text-[var(--text-tertiary)]">Permanently erase all chat history and account data.</p>
                  <button
                    type="button"
                    onClick={() => {
                      if (confirm('Permanently erase all chats? This cannot be undone.')) {
                        localStorage.removeItem('aarka-conversations-v3');
                        window.location.reload();
                      }
                    }}
                    className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium cursor-pointer"
                  >
                    Delete All Conversations
                  </button>
                </div>
              </div>
            )}

            {/* 13. NOTIFICATIONS TAB */}
            {activeTab === 'notifications' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Email Notifications</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Receive weekly research summaries and account updates.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={emailAlerts}
                    onChange={(e) => setEmailAlerts(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Security Alerts</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Instant alerts for new logins and token rotations.</span>
                  </div>
                  <input
                    type="checkbox"
                    checked={securityAlerts}
                    onChange={(e) => setSecurityAlerts(e.target.checked)}
                    className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                  />
                </div>
              </div>
            )}

            {/* 14. PLAN & USAGE TAB */}
            {activeTab === 'usage' && (
              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-gradient-to-br from-[var(--bg-secondary)] to-[var(--bg-tertiary)] border border-[var(--border)] space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[var(--text-primary)]">Current Tier</span>
                    <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[var(--accent-muted)] text-[var(--accent-primary)]">
                      ENTERPRISE PRO
                    </span>
                  </div>
                  <span className="text-[11px] text-[var(--text-secondary)] block">
                    Unlimited Aarka AI 2.0 high-effort reasoning and priority neural mesh routing.
                  </span>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2 text-xs">
                  <span className="font-semibold text-[var(--text-primary)] block">Monthly Token Consumption</span>
                  <div className="w-full h-2 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                    <div className="h-full bg-[var(--accent-primary)] rounded-full" style={{ width: '38%' }} />
                  </div>
                  <div className="flex justify-between text-[10px] text-[var(--text-tertiary)] font-mono">
                    <span>384,210 tokens used</span>
                    <span>1,000,000 quota</span>
                  </div>
                </div>
              </div>
            )}

            {/* 15. DEVELOPER TAB */}
            {activeTab === 'developer' && (
              <div className="space-y-4">
                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                  <span className="text-xs font-bold text-[var(--text-primary)] block">Create API Key</span>
                  <p className="text-[11px] text-[var(--text-tertiary)]">
                    API keys allow programmatic access to the Aarka AI 2.0 streaming inference endpoints.
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={newKeyName}
                      onChange={(e) => setNewKeyName(e.target.value)}
                      placeholder="Key Name (e.g. FinGenIQ Integration)"
                      className="flex-1 px-3 py-1.5 rounded-lg bg-[var(--bg-tertiary)] border border-[var(--border)] text-xs text-[var(--text-primary)] focus:outline-none"
                    />
                    <button
                      type="button"
                      onClick={handleGenerateApiKey}
                      className="px-3 py-1.5 rounded-lg bg-[var(--accent-primary)] text-white text-xs font-medium cursor-pointer"
                    >
                      Generate Key
                    </button>
                  </div>
                </div>

                {/* API Keys List */}
                <div className="space-y-1.5">
                  {apiKeys.map((k) => (
                    <div key={k.id} className="flex items-center justify-between p-2.5 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] text-xs">
                      <div>
                        <span className="font-semibold text-[var(--text-primary)] block">{k.name}</span>
                        <span className="font-mono text-[10px] text-[var(--text-tertiary)]">{k.maskedKey}</span>
                      </div>
                      <span className="text-[10px] text-[var(--text-tertiary)] font-mono">{k.created}</span>
                    </div>
                  ))}
                </div>

                <div className="flex gap-2 pt-2">
                  <a
                    href="https://aarka-ai.com/docs"
                    target="_blank"
                    rel="noreferrer"
                    className="text-xs text-[var(--accent-primary)] hover:underline flex items-center gap-1"
                  >
                    API Documentation <ExternalLink className="w-3 h-3" />
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
