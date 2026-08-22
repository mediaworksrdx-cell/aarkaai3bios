export type EffortLevel = 'low' | 'medium' | 'high';

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  modelUsed?: string;
  effort?: EffortLevel;
  isStreaming?: boolean;
  error?: string;
  feedback?: 'up' | 'down';
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
  model: string;
  effort?: EffortLevel;
}

export interface StreamChunk {
  type?: 'content' | 'token' | 'status' | 'metadata' | 'final' | 'final_response' | 'error' | string;
  token?: string;
  content?: string;
  text?: string;
  status?: string;
  detail?: string;
  response?: string;
  model_used?: string;
  processing_time?: number;
  sources?: string[];
  [key: string]: any;
}

export interface ModelOption {
  id: string;
  label: string;
  name?: string;
  description: string;
  icon?: string;
  badge?: string;
  provider?: string;
  tier?: 'standard' | 'premium' | 'flagship';
}

export interface User {
  id: string;
  email: string;
  name: string;
  picture?: string;
}
