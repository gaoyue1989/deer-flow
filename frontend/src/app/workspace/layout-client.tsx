'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useState } from 'react';

import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';
import { CommandPalette } from '@/components/workspace/command-palette';
import { WorkspaceSidebar } from '@/components/workspace/workspace-sidebar';
import { AuthProvider } from '@/core/auth/context';

// Initialize queryClient at module level
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
    },
  },
});

export default function WorkspaceLayoutClient({ children }: { children: React.ReactNode }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SidebarProvider
          className="h-screen"
          open={sidebarOpen}
          onOpenChange={setSidebarOpen}
        >
          <WorkspaceSidebar />
          <SidebarInset className="min-w-0">{children}</SidebarInset>
        </SidebarProvider>
        <CommandPalette />
      </AuthProvider>
    </QueryClientProvider>
  );
}