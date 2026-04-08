import { cookies } from "next/headers";
import { Toaster } from "sonner";

import WorkspaceLayoutClient from './layout-client';

function parseSidebarOpenCookie(
  value: string | undefined,
): boolean | undefined {
  if (value === "true") return true;
  if (value === "false") return false;
  return undefined;
}

export default async function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const cookieStore = await cookies();
  const initialSidebarOpen = parseSidebarOpenCookie(
    cookieStore.get("sidebar_state")?.value,
  );

  return (
    <>
      <WorkspaceLayoutClient>{children}</WorkspaceLayoutClient>
      <Toaster position="top-center" />
    </>
  );
}