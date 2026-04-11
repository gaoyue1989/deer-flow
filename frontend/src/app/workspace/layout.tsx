import { Toaster } from "sonner";

import WorkspaceLayoutClient from "./layout-client";

export default async function WorkspaceLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <>
      <WorkspaceLayoutClient>{children}</WorkspaceLayoutClient>
      <Toaster position="top-center" />
    </>
  );
}
