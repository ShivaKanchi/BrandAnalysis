import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'BrandAnalysis: Autonomous Lead Generation & Brand Intelligence Platform',
  description: 'High-intent lead generation, automated prospect farming, performance diagnostics, and client acquisition.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark overflow-x-clip">
      <body className="bg-paper text-ink min-h-screen antialiased overflow-x-clip selection:bg-accent/35 selection:text-ink">
        {children}
      </body>
    </html>
  );
}
