import { cookies } from "next/headers";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "sonner";

import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { CommandPalette } from "@/components/workspace/command-palette";
import { WorkspaceSidebar } from "@/components/workspace/workspace-sidebar";
import { AuthProvider } from "@/core/auth/context";
import { getLocalSettings } from "@/core/settings";

function parseSidebarOpenCookie(
  value: string | undefined,
): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

// Initialize queryClient at module level
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
    },
  },
});

async function getInitialSidebarOpen() {
  try {
    const settings = await getLocalSettings();
    return settings.sidebarOpen ?? true;
  } catch {
    return true; // Default to open
  }
}

export default async function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const initialSidebarOpen = await getInitialSidebarOpen();
  const cookieStore = await cookies();

  // Allow cookie to override settings for this session
  const cookieOverride = parseSidebarOpenCookie(
    cookieStore.get("sidebar_state")?.value,
  );

  const effectiveOpen = cookieOverride ?? initialSidebarOpen;

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SidebarProvider
          className="h-screen"
          defaultOpen={effectiveOpen}
        >
          <WorkspaceSidebar />
          <SidebarInset className="min-w-0">{children}</SidebarInset>
        </SidebarProvider>
        <CommandPalette />
        <Toaster position="top-center" />
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default async function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = await cookies();
  const initialSidebarOpen = parseSidebarOpenCookie(
    cookieStore.get("sidebar_state")?.value,
  );

  return (
import { AuthProvider } from "@/core/auth/context";
import { getLocalSettings, useLocalSettings } from "@/core/settings";

// Initialize queryClient at module level
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
    },
  },
});

async function getInitialSidebarOpen() {
  try {
    const settings = await getLocalSettings();
    return settings.sidebarOpen ?? true;
  } catch {
    return true; // Default to open
  }
}

export default async function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const initialSidebarOpen = await getInitialSidebarOpen();
  const cookieStore = await cookies();

  // Allow cookie to override settings for this session
  const cookieOverride = parseSidebarOpenCookie(
    cookieStore.get("sidebar_state")?.value,
  );

  const effectiveOpen = cookieOverride ?? initialSidebarOpen;

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SidebarProvider
          className="h-screen"
          defaultOpen={effectiveOpen}
        >
          <WorkspaceSidebar />
          <SidebarInset className="min-w-0">{children}</SidebarInset>
        </SidebarProvider>
        <CommandPalette />
        <Toaster position="top-center" />
      </AuthProvider>
    </QueryClientProvider>
  );
}
    </QueryClientProvider>
  );
}
