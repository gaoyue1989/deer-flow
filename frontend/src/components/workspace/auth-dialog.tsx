"use client";

import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/core/auth/context";
import { useI18n } from "@/core/i18n/hooks";

export function AuthDialog({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const { t } = useI18n();
  const { doLogin, doRegister } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (action: "login" | "register") => {
    if (password.length < 8) {
      toast.error(t.auth.passwordTooShort);
      return;
    }
    setLoading(true);
    try {
      if (action === "login") {
        await doLogin(email, password);
        toast.success(t.auth.loginSuccess);
      } else {
        await doRegister(email, password);
        toast.success(t.auth.registerSuccess);
      }
      onOpenChange(false);
      setEmail("");
      setPassword("");
    } catch {
      toast.error(
        action === "login" ? t.auth.loginFailed : t.auth.registerFailed,
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[400px]">
        <DialogHeader>
          <DialogTitle>{t.auth.signIn}</DialogTitle>
          <DialogDescription>{t.auth.signIn}</DialogDescription>
        </DialogHeader>
        <Tabs defaultValue="login">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="login">{t.auth.login}</TabsTrigger>
            <TabsTrigger value="register">{t.auth.register}</TabsTrigger>
          </TabsList>
          <TabsContent value="login" className="space-y-4 pt-4">
            <Input
              type="email"
              placeholder={t.auth.emailPlaceholder}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              type="password"
              placeholder={t.auth.passwordPlaceholder}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleSubmit("login");
              }}
            />
            <Button
              className="w-full"
              disabled={loading}
              onClick={() => void handleSubmit("login")}
            >
              {loading ? t.common.loading : t.auth.login}
            </Button>
          </TabsContent>
          <TabsContent value="register" className="space-y-4 pt-4">
            <Input
              type="email"
              placeholder={t.auth.emailPlaceholder}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              type="password"
              placeholder={t.auth.passwordPlaceholder}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void handleSubmit("register");
              }}
            />
            <Button
              className="w-full"
              disabled={loading}
              onClick={() => void handleSubmit("register")}
            >
              {loading ? t.common.loading : t.auth.register}
            </Button>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}
