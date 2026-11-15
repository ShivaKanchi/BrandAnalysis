import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'BrandAnalysis: Autonomous Agency Intelligence and Shopify Revamp Platform',
  description: 'Workflow DAG engine for automated store audits, speed diagnostics, console error interception, and revamp pitch generation.',
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
