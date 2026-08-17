import type { Metadata } from 'next';
import { Plus_Jakarta_Sans, Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { ThemeProvider } from '@/context/ThemeContext';

const display = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-display',
  display: 'swap',
});

const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-sans',
  display: 'swap',
});

const mono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Aarka AI — Advanced Conversational Intelligence',
  description:
    'Aarka AI — High-precision conversational AI powered by multi-model reasoning, institutional finance, and live code synthesis.',
  icons: {
    icon: '/favicon.ico',
  },
  openGraph: {
    title: 'Aarka AI',
    description: 'High-precision conversational AI powered by multi-model reasoning.',
    siteName: 'Aarka AI',
    type: 'website',
  },
  twitter: {
    card: 'summary',
    title: 'Aarka AI',
    description: 'High-precision conversational AI powered by multi-model reasoning.',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`light ${display.variable} ${inter.variable} ${mono.variable}`} data-theme="light" suppressHydrationWarning>
      <body className="font-sans light bg-[var(--bg-primary)] text-[var(--text-primary)] antialiased min-h-screen overflow-hidden" data-theme="light" suppressHydrationWarning>
        {/* Pre-hydration script to permanently enforce light theme and reset any old dark cache */}
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{localStorage.setItem('aarka-theme','light');localStorage.setItem('aarkaa-theme','light');var d=document.documentElement;var b=document.body;d.classList.remove('dark');d.classList.add('light');d.setAttribute('data-theme','light');if(b){b.classList.remove('dark');b.classList.add('light');b.setAttribute('data-theme','light')}}catch(e){}})();`,
          }}
        />
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
