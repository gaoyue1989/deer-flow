import { getBackendBaseURL } from "../config";

import type { LoginRequest, RegisterRequest, Session } from "./types";

const AUTH_PREFIX = "/api/v1/auth";

export async function register(data: RegisterRequest): Promise<Session> {
  const res = await fetch(`${getBackendBaseURL()}${AUTH_PREFIX}/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? "Registration failed");
  }
  return res.json() as Promise<Session>;
}

export async function login(data: LoginRequest): Promise<Session> {
  const res = await fetch(`${getBackendBaseURL()}${AUTH_PREFIX}/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(err.detail ?? "Login failed");
  }
  return res.json() as Promise<Session>;
}

export async function getMe(token: string): Promise<Session | null> {
  const res = await fetch(`${getBackendBaseURL()}${AUTH_PREFIX}/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) return null;
  return res.json() as Promise<Session>;
}

export async function logout(): Promise<void> {
  await fetch(`${getBackendBaseURL()}${AUTH_PREFIX}/logout`, {
    method: "POST",
  }).catch(() => {
    /* ignore logout errors */
  });
}
