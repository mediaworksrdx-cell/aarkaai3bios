export interface ThemeColors {
  bgPrimary: string;
  bgSecondary: string;
  bgTertiary: string;
  bgHover: string;
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  accentPrimary: string;
  accentHover: string;
  accentMuted: string;
  border: string;
  borderStrong: string;
  borderAccent: string;
  codeBg: string;
  userMsgBg: string;
  assistantMsgBg: string;
  shadowSm: string;
  shadowMd: string;
  shadowLg: string;
  shadowFloat: string;
}

export type EffortLevel = 'low' | 'medium' | 'high';

export interface ModelOption {
  id: string;
  label: string;
  icon: string;
}

export interface EffortOption {
  id: EffortLevel;
  label: string;
  icon: string;
}

export const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'aarka-2.0',
    label: 'Aarka AI',
    icon: '⚡',
  },
  {
    id: 'gemini-3.7',
    label: 'Google Gemini 3.7',
    icon: '✨',
  },
];

export const EFFORT_OPTIONS: EffortOption[] = [
  {
    id: 'low',
    label: 'Low',
    icon: '⚡',
  },
  {
    id: 'medium',
    label: 'Medium',
    icon: '🎯',
  },
  {
    id: 'high',
    label: 'High',
    icon: '🧠',
  },
];
