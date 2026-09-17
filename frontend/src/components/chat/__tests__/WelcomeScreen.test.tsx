import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { WelcomeScreen } from '../WelcomeScreen';

describe('WelcomeScreen Component', () => {
  it('renders default welcome message for guest user', () => {
    render(<WelcomeScreen selectedModel="aarkaa-3b" isGuest={true} />);

    expect(screen.getByText(/Welcome to/i)).toBeInTheDocument();
    expect(screen.getByText('Aarka AI')).toBeInTheDocument();
    expect(
      screen.getByText(/How can Aarka assist your research, financial engineering, or architecture today\?/i)
    ).toBeInTheDocument();
  });

  it('renders personalized welcome message for authenticated user', () => {
    render(<WelcomeScreen selectedModel="aarkaa-3b" userName="Siddharth" isGuest={false} />);

    expect(screen.getByText(/Welcome,/i)).toBeInTheDocument();
    expect(screen.getByText('Siddharth')).toBeInTheDocument();
  });
});
