import type { NextConfig } from 'next';
import createNextIntlPlugin from 'next-intl/plugin';

const withNextIntl = createNextIntlPlugin('./src/i18n/request.ts');

const nextConfig: NextConfig = {
  // Enable static export for Capacitor mobile builds
  // Set NEXT_OUTPUT=export in env to generate static files
  ...(process.env.NEXT_OUTPUT === "export" ? { output: "export" } : {}),
};

export default withNextIntl(nextConfig);
