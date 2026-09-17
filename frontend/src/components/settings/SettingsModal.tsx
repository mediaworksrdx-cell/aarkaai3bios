'use client';

import React, { useState, useEffect } from 'react';
import {
  X,
  Sliders,
  MessageSquare,
  Cpu,
  Sparkles,
  Globe,
  Shield,
  EyeOff,
  Bell,
  CheckCircle2,
  Sun,
  Server,
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';
import { fetchSettingsApi, updateSettingsApi } from '@/lib/api';
import { McpSettingsTab } from './McpSettingsTab';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: { name: string; email: string; picture?: string; id?: string } | null;
}

type TabId =
  | 'general'
  | 'chat'
  | 'models'
  | 'mcp'
  | 'web'
  | 'security'
  | 'notifications';

const SETTINGS_TABS: { id: TabId; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: 'general', label: 'General', icon: Sliders },
  { id: 'chat', label: 'Chat & Conversation', icon: MessageSquare },
  { id: 'models', label: 'Models & Reasoning', icon: Cpu },
  { id: 'mcp', label: 'MCP Servers', icon: Server },
  { id: 'web', label: 'Web & Research', icon: Globe },
  { id: 'security', label: 'Security', icon: Shield },
  { id: 'notifications', label: 'Notifications', icon: Bell },
];

export function SettingsModal({ isOpen, onClose, user }: SettingsModalProps) {
  const { theme, toggleTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<TabId>('general');
  const [savedNotification, setSavedNotification] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // General Settings
  // 1. General Settings
  const [language, setLanguage] = useState('en');
  const [density, setDensity] = useState<'compact' | 'comfortable'>('comfortable');

  // 2. Chat Settings
  const [enterToSend, setEnterToSend] = useState(true);
  const [showTimestamps, setShowTimestamps] = useState(true);
  const [streamingResponses, setStreamingResponses] = useState(true);
  const [incognitoChat, setIncognitoChat] = useState(false);

  // 3. Model & Reasoning Settings
  const [defaultModel, setDefaultModel] = useState<'aarka-2.0' | 'gemini-3.7' | 'claude-sonnet-5'>('aarka-2.0');
  const [defaultEffort, setDefaultEffort] = useState<'low' | 'medium' | 'high'>('medium');

  // 4. Web & Research Settings
  const [webSearchEnabled, setWebSearchEnabled] = useState(true);
  const [deepResearchEnabled, setDeepResearchEnabled] = useState(true);
  const [marketDataEnabled, setMarketDataEnabled] = useState(true);

  // 5. Security Settings
  const [twoFactorEnabled, setTwoFactorEnabled] = useState(false);

  // 6. Notification Settings
  const [emailAlerts, setEmailAlerts] = useState(true);
  const [securityAlerts, setSecurityAlerts] = useState(true);

  // Load preferences from localStorage and sync from authoritative backend on mount
  useEffect(() => {
    // 1. Instant local restore
    try {
      const saved = localStorage.getItem('aarka_user_settings_v2');
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.language) setLanguage(parsed.language);
        if (parsed.density) setDensity(parsed.density);
        if (parsed.enterToSend !== undefined) setEnterToSend(parsed.enterToSend);
        if (parsed.showTimestamps !== undefined) setShowTimestamps(parsed.showTimestamps);
        if (parsed.streamingResponses !== undefined) setStreamingResponses(parsed.streamingResponses);
        if (parsed.incognitoChat !== undefined) setIncognitoChat(parsed.incognitoChat);
        if (parsed.defaultModel) setDefaultModel(parsed.defaultModel);
        if (parsed.defaultEffort) setDefaultEffort(parsed.defaultEffort);
        if (parsed.webSearchEnabled !== undefined) setWebSearchEnabled(parsed.webSearchEnabled);
        if (parsed.deepResearchEnabled !== undefined) setDeepResearchEnabled(parsed.deepResearchEnabled);
        if (parsed.marketDataEnabled !== undefined) setMarketDataEnabled(parsed.marketDataEnabled);
        if (parsed.twoFactorEnabled !== undefined) setTwoFactorEnabled(parsed.twoFactorEnabled);
        if (parsed.emailAlerts !== undefined) setEmailAlerts(parsed.emailAlerts);
        if (parsed.securityAlerts !== undefined) setSecurityAlerts(parsed.securityAlerts);
      }
    } catch {}

    // 2. Authoritative backend synchronization
    fetchSettingsApi()
      .then((backendSettings) => {
        if (backendSettings && !backendSettings.error) {
          if (backendSettings.language) setLanguage(backendSettings.language);
          if (backendSettings.default_model) setDefaultModel(backendSettings.default_model);
          if (backendSettings.streaming_enabled !== undefined) setStreamingResponses(backendSettings.streaming_enabled);
          if (backendSettings.web_search_enabled !== undefined) setWebSearchEnabled(backendSettings.web_search_enabled);
          if (backendSettings.deep_research_enabled !== undefined) setDeepResearchEnabled(backendSettings.deep_research_enabled);
          if (backendSettings.market_data_enabled !== undefined) setMarketDataEnabled(backendSettings.market_data_enabled);
          if (backendSettings.reasoning_depth) {
            const d = backendSettings.reasoning_depth;
            if (d === 'low' || d === 'medium' || d === 'high') setDefaultEffort(d);
          }
          // UI preference fields synced from backend
          if (backendSettings.density === 'compact' || backendSettings.density === 'comfortable') {
            setDensity(backendSettings.density);
          }
          if (backendSettings.enter_to_send !== undefined) setEnterToSend(backendSettings.enter_to_send);
          if (backendSettings.show_timestamps !== undefined) setShowTimestamps(backendSettings.show_timestamps);
          if (backendSettings.incognito_chat !== undefined) setIncognitoChat(backendSettings.incognito_chat);
          if (backendSettings.two_factor_enabled !== undefined) setTwoFactorEnabled(backendSettings.two_factor_enabled);
          if (backendSettings.email_alerts !== undefined) setEmailAlerts(backendSettings.email_alerts);
          if (backendSettings.security_alerts !== undefined) setSecurityAlerts(backendSettings.security_alerts);
        }
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    const settingsPayload = {
      language,
      density,
      enterToSend,
      showTimestamps,
      streamingResponses,
      incognitoChat,
      defaultModel,
      defaultEffort,
      webSearchEnabled,
      deepResearchEnabled,
      marketDataEnabled,
      twoFactorEnabled,
      emailAlerts,
      securityAlerts,
    };
    try {
      localStorage.setItem('aarka_user_settings_v2', JSON.stringify(settingsPayload));
    } catch {}

    // Synchronize to backend database
    try {
      await updateSettingsApi({
        language,
        default_model: defaultModel,
        streaming_enabled: streamingResponses,
        web_search_enabled: webSearchEnabled,
        deep_research_enabled: deepResearchEnabled,
        market_data_enabled: marketDataEnabled,
        reasoning_depth: defaultEffort,
        density,
        enter_to_send: enterToSend,
        show_timestamps: showTimestamps,
        incognito_chat: incognitoChat,
        two_factor_enabled: twoFactorEnabled,
        email_alerts: emailAlerts,
        security_alerts: securityAlerts,
      });
      setSaveError(null);
    } catch (err: any) {
      const msg = err?.message || 'Failed to save settings to server. Changes saved locally only.';
      setSaveError(msg);
      setTimeout(() => setSaveError(null), 4000);
    }

    setSavedNotification(true);
    setTimeout(() => setSavedNotification(false), 2000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div
        className="relative w-full max-w-4xl h-[680px] bg-[var(--bg-primary)] border border-[var(--border-strong)] rounded-2xl shadow-[var(--shadow-float)] flex overflow-hidden flex-col md:flex-row animate-scale-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Save / Error notification bar */}
        {savedNotification && (
          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 rounded-xl bg-green-500/20 border border-green-500/40 text-green-600 text-xs font-semibold shadow-lg">
            <CheckCircle2 className="w-3.5 h-3.5" /> Settings saved
          </div>
        )}
        {saveError && (
          <div className="absolute top-2 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/20 border border-red-500/40 text-red-600 text-xs font-semibold shadow-lg max-w-sm text-center">
            ⚠ {saveError}
          </div>
        )}

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
                    <option value="hi">Hindi (हिंदी)</option>
                    <option value="ta">Tamil (தமிழ்)</option>
                    <option value="te">Telugu (తెలుగు)</option>
                    <option value="kn">Kannada (ಕನ್ನಡ)</option>
                    <option value="ml">Malayalam (മലയാളം)</option>
                    <option value="mr">Marathi (मराठी)</option>
                    <option value="bn">Bengali (বাংলা)</option>
                    <option value="gu">Gujarati (ગુજરાતી)</option>
                    <option value="pa">Punjabi (ਪੰਜਾਬੀ)</option>
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

            {/* 2. CHAT & CONVERSATION TAB */}
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
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
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
                        Flagship reasoning engine with mathematical rigor.
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

                    <button
                      type="button"
                      onClick={() => setDefaultModel('claude-sonnet-5')}
                      className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                        defaultModel === 'claude-sonnet-5' ? 'border-[var(--accent-primary)] bg-[var(--accent-muted)]' : 'border-[var(--border)] bg-[var(--bg-secondary)]'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <Sparkles className="w-4 h-4 text-purple-400" />
                        <span className="text-xs font-bold text-[var(--text-primary)]">Claude Sonnet 5</span>
                      </div>
                      <span className="text-[11px] text-[var(--text-secondary)] block">
                        Anthropic state-of-the-art hybrid reasoning & coding.
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

            {/* MCP MANAGEMENT TAB */}
            {activeTab === 'mcp' && <McpSettingsTab />}

            {/* 4. WEB & RESEARCH TAB */}
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

            {/* 5. SECURITY TAB */}
            {activeTab === 'security' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)]">
                  <div>
                    <span className="text-xs font-bold text-[var(--text-primary)] block">Two-Factor Authentication (2FA)</span>
                    <span className="text-[11px] text-[var(--text-tertiary)]">Protect your account with TOTP authenticator app verification.</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 border border-amber-500/20">Coming Soon</span>
                    <input
                      type="checkbox"
                      checked={twoFactorEnabled}
                      onChange={(e) => setTwoFactorEnabled(e.target.checked)}
                      className="w-4 h-4 rounded text-[var(--accent-primary)] cursor-pointer"
                      title="Preference saved — TOTP enrollment coming soon"
                    />
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-secondary)] border border-[var(--border)] space-y-2">
                  <span className="text-xs font-bold text-[var(--text-primary)] block">Active Sessions</span>
                  <div className="flex items-center justify-between text-xs py-1 border-b border-[var(--border)]">
                    <div>
                      <span className="text-[var(--text-primary)] font-medium block">Current Browser Session</span>
                      <span className="text-[10px] text-[var(--text-tertiary)]">Last active: Now</span>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500">Active</span>
                  </div>
                  <button
                    type="button"
                    disabled
                    className="mt-2 text-xs text-[var(--text-tertiary)] font-medium cursor-not-allowed opacity-50"
                  >
                    Sign Out All Other Devices (Coming Soon)
                  </button>
                </div>
              </div>
            )}

            {/* 6. NOTIFICATIONS TAB */}
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
          </div>
        </div>
      </div>
    </div>
  );
}
