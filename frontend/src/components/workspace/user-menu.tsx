"use client";

import { LogIn, LogOut, User } from "lucide-react";
import { useState } from "react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuth } from "@/core/auth/context";
import { useI18n } from "@/core/i18n/hooks";

import { AuthDialog } from "./auth-dialog";

export function UserMenu() {
  const { t } = useI18n();
  const { session, isAuthenticated, doLogout } = useAuth();
  const [authDialogOpen, setAuthDialogOpen] = useState(false);

  if (!isAuthenticated) {
    return (
      <>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1"
          onClick={() => setAuthDialogOpen(true)}
        >
          <LogIn className="size-4" />
          <span className="hidden sm:inline">{t.auth.signIn}</span>
        </Button>
        <AuthDialog open={authDialogOpen} onOpenChange={setAuthDialogOpen} />
      </>
    );
  }

  const initials = session?.email
    ? session.email.substring(0, 2).toUpperCase()
    : "U";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className="gap-2">
          <Avatar className="size-6">
            <AvatarFallback className="text-xs">{initials}</AvatarFallback>
          </Avatar>
          <span className="hidden max-w-[120px] truncate text-sm sm:inline">
            {session?.email}
          </span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex items-center gap-2">
          <User className="size-4" />
          <span className="truncate">{session?.email}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => doLogout()}>
          <LogOut className="size-4" />
          {t.auth.signOut}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
