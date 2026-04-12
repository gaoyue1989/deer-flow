export interface McpToolDisplayConfig {
  card_title: string;
  icon: string;
  template_path: string;
}

export interface MCPServerConfig extends Record<string, unknown> {
  enabled: boolean;
  description: string;
  tools?: Record<string, McpToolDisplayConfig>;
}

export interface MCPConfig {
  mcp_servers: Record<string, MCPServerConfig>;
}

export interface MCPToolTemplate {
  card_title: string;
  icon: string;
  template_path: string;
  server_name: string;
  tool_name: string;
  template_content?: string;
}
