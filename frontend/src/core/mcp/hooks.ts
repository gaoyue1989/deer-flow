import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";

import { loadMCPConfig, updateMCPConfig } from "./api";
import type { MCPToolTemplate } from "./types";

export function useMCPConfig() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["mcpConfig"],
    queryFn: () => loadMCPConfig(),
  });
  return { config: data, isLoading, error };
}

export function useEnableMCPServer() {
  const queryClient = useQueryClient();
  const { config } = useMCPConfig();
  return useMutation({
    mutationFn: async ({
      serverName,
      enabled,
    }: {
      serverName: string;
      enabled: boolean;
    }) => {
      if (!config) {
        throw new Error("MCP config not found");
      }
      if (!config.mcp_servers[serverName]) {
        throw new Error(`MCP server ${serverName} not found`);
      }
      await updateMCPConfig({
        mcp_servers: {
          ...config.mcp_servers,
          [serverName]: {
            ...config.mcp_servers[serverName],
            enabled,
          },
        },
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["mcpConfig"] });
    },
  });
}

// Cache for loaded templates
const templateCache = new Map<string, string>();

export function useMCPToolTemplates() {
  const { config } = useMCPConfig();

  const templates = useMemo(() => {
    const result: Record<string, MCPToolTemplate> = {};
    if (!config?.mcp_servers) return result;

    for (const [serverName, serverConfig] of Object.entries(
      config.mcp_servers,
    )) {
      if (serverConfig.tools) {
        for (const [toolName, toolConfig] of Object.entries(
          serverConfig.tools,
        )) {
          result[toolName] = {
            card_title: toolConfig.card_title,
            icon: toolConfig.icon,
            template_path: toolConfig.template_path,
            server_name: serverName,
            tool_name: toolName,
          };
        }
      }
    }
    return result;
  }, [config]);

  const getTemplate = useCallback(
    (toolName: string): MCPToolTemplate | undefined => {
      return templates[toolName];
    },
    [templates],
  );

  const loadTemplateContent = useCallback(
    async (template: MCPToolTemplate): Promise<string> => {
      if (template.template_content) {
        return template.template_content;
      }
      const cacheKey = template.tool_name;
      if (templateCache.has(cacheKey)) {
        return templateCache.get(cacheKey)!;
      }
      try {
        const response = await fetch(
          `/api/mcp/templates/${template.tool_name}`,
        );
        if (!response.ok) {
          throw new Error(`Failed to load template: ${template.tool_name}`);
        }
        const data = await response.json();
        const content = data.content as string;
        templateCache.set(cacheKey, content);
        return content;
      } catch (error) {
        console.error(
          `Error loading template for ${template.tool_name}:`,
          error,
        );
        return "";
      }
    },
    [],
  );

  return { templates, getTemplate, loadTemplateContent };
}
