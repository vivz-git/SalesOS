"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { createClient } from "@/lib/supabase/client";

export interface Workspace {
  id: string;
  name: string;
  slug: string;
  created_at?: string;
  updated_at?: string;
}

interface WorkspaceContextType {
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  loading: boolean;
  setActiveWorkspaceId: (id: string) => void;
  createWorkspace: (name: string, slug?: string) => Promise<Workspace>;
  refreshWorkspaces: () => Promise<void>;
}

const COOKIE_NAME = "salesos_workspace_id";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

function setCookie(name: string, value: string, days = 30) {
  if (typeof document === "undefined") return;
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspaceId, setActiveWorkspaceIdState] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchWorkspaces() {
    try {
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const headers = new Headers();
      if (session?.access_token) {
        headers.set("Authorization", `Bearer ${session.access_token}`);
      }

      const res = await fetch("/api/v1/workspaces", { headers });
      if (res.ok) {
        const data: Workspace[] = await res.json();
        setWorkspaces(data);
        const savedId = getCookie(COOKIE_NAME);
        if (savedId && data.some((w) => w.id === savedId)) {
          setActiveWorkspaceIdState(savedId);
        } else if (data.length > 0) {
          setActiveWorkspaceIdState(data[0].id);
          setCookie(COOKIE_NAME, data[0].id);
        }
      }
    } catch {
      // API unavailable or network failure
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  function setActiveWorkspaceId(id: string) {
    setActiveWorkspaceIdState(id);
    setCookie(COOKIE_NAME, id);
  }

  async function createWorkspace(name: string, slug?: string): Promise<Workspace> {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    const headers = new Headers({ "Content-Type": "application/json" });
    if (session?.access_token) {
      headers.set("Authorization", `Bearer ${session.access_token}`);
    }

    const res = await fetch("/api/v1/workspaces", {
      method: "POST",
      headers,
      body: JSON.stringify({ name, slug }),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to create workspace");
    }
    const newWs: Workspace = await res.json();
    setWorkspaces((prev) => [...prev, newWs]);
    setActiveWorkspaceId(newWs.id);
    return newWs;
  }

  const activeWorkspace = workspaces.find((w) => w.id === activeWorkspaceId) || null;

  return (
    <WorkspaceContext.Provider
      value={{
        workspaces,
        activeWorkspace,
        loading,
        setActiveWorkspaceId,
        createWorkspace,
        refreshWorkspaces: fetchWorkspaces,
      }}
    >
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
}
