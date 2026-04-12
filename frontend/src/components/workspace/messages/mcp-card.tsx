"use client";

import "./mcp-card.css";
import "./mcd-card.css";
import Mustache from "mustache";
import { useCallback, useEffect, useRef, useState } from "react";

import { ChainOfThoughtSearchResult } from "@/components/ai-elements/chain-of-thought";
import { ChainOfThoughtStep } from "@/components/ai-elements/chain-of-thought";
import * as lucideIcons from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { useMCPToolTemplates } from "@/core/mcp";

export interface MCPCardAction {
  action: string;
  params: Record<string, unknown>;
  toolName: string;
  serverName: string;
}

interface MCPCardProps {
  toolName: string;
  args: Record<string, unknown>;
  result: string | Record<string, unknown> | undefined;
  onAction?: (action: MCPCardAction) => void;
}

function getLucideIcon(iconName: string): LucideIcon | undefined {
  const pascalName = iconName
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join("");
  return (lucideIcons as unknown as Record<string, LucideIcon | undefined>)[pascalName];
}

function extractJSONFromText(text: string): Record<string, unknown> | null {
  if (typeof text !== "string") return null;
  
  const jsonStart = text.indexOf('{"success"');
  if (jsonStart < 0) return null;
  
  let braceCount = 0;
  let jsonEnd = jsonStart;
  
  for (let i = jsonStart; i < text.length; i++) {
    if (text[i] === '{') braceCount++;
    if (text[i] === '}') braceCount--;
    if (braceCount === 0) {
      jsonEnd = i + 1;
      break;
    }
  }
  
  const jsonStr = text.substring(jsonStart, jsonEnd);
  try {
    return JSON.parse(jsonStr);
  } catch {
    return null;
  }
}

function parseResult(raw: string | Record<string, unknown> | undefined): Record<string, unknown> {
  if (raw === undefined) return {};
  if (typeof raw === "string") {
    const extracted = extractJSONFromText(raw);
    if (extracted) return extracted;
    try { return JSON.parse(raw); } catch { return { raw }; }
  }
  return raw || {};
}

function parseWeatherResult(raw: Record<string, unknown>, args: Record<string, unknown>): Record<string, unknown> {
  const metadata = raw.__metadata__ as Record<string, unknown> | undefined;
  if (!metadata) return raw;

  const now = metadata.now as Record<string, unknown> | undefined;
  if (!now) return raw;

  const refer = metadata.refer as Record<string, unknown> | undefined;
  const sources = refer?.sources as string[] | undefined;

  return {
    city: (args.kwargs as Record<string, unknown>)?.city || (args as Record<string, unknown>)?.city || "",
    code: metadata.code,
    updateTime: metadata.updateTime,
    fxLink: metadata.fxLink,
    source: sources?.[0] || "",
    ...now,
  };
}

function parseMCDPointsProducts(raw: Record<string, unknown>, userPoints?: number): Record<string, unknown> {
  if (!raw.data || !Array.isArray(raw.data)) return raw;
  
  const products = raw.data.map((item: Record<string, unknown>) => ({
    ...item,
    canRedeem: userPoints ? Number(item.point) <= userPoints : true,
  }));
  
  return {
    datetime: raw.datetime,
    userPoints,
    products,
  };
}

function parseMCDAccount(raw: Record<string, unknown>): Record<string, unknown> {
  if (!raw.data) return raw;
  return {
    datetime: raw.datetime,
    ...raw.data,
  };
}

function parseMCDMeals(raw: Record<string, unknown>, args: Record<string, unknown>): Record<string, unknown> {
  if (!raw.data) return raw;
  
  const data = raw.data as Record<string, unknown>;
  const categories = data.categories as Array<Record<string, unknown>> | undefined;
  const mealsDict = data.meals as Record<string, Record<string, unknown>> | undefined;
  
  if (!categories || !mealsDict) return raw;
  
  const parsedCategories = categories.map(cat => {
    const meals = (cat.meals as Array<Record<string, unknown>> | [])?.map(meal => {
      const code = meal.code as string;
      const mealDetail = mealsDict[code];
      return {
        code,
        mealName: mealDetail?.name || code,
        price: mealDetail?.currentPrice,
        tags: meal.tags || [],
      };
    });
    
    return {
      name: cat.name,
      meals,
    };
  });
  
  return {
    datetime: raw.datetime,
    storeCode: (args as Record<string, unknown>)?.storeCode || "",
    storeName: (args as Record<string, unknown>)?.storeName || "",
    categories: parsedCategories,
  };
}

function parseMCDResult(toolName: string, raw: Record<string, unknown>, args: Record<string, unknown>): Record<string, unknown> {
  if (toolName.includes("mall-points-products") || toolName.includes("points")) {
    return parseMCDPointsProducts(raw);
  }
  if (toolName.includes("query-my-account") || toolName.includes("account")) {
    return parseMCDAccount(raw);
  }
  if (toolName.includes("query-meals") || toolName.includes("meals")) {
    return parseMCDMeals(raw, args);
  }
  return raw;
}

export function MCPCard({ toolName, args, result, onAction }: MCPCardProps) {
  const { getTemplate, loadTemplateContent } = useMCPToolTemplates();
  const containerRef = useRef<HTMLDivElement>(null);
  const [templateContent, setTemplateContent] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const template = getTemplate(toolName);

  useEffect(() => {
    if (!template?.template_path) {
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    setIsLoading(true);
    setError(null);

    loadTemplateContent(template)
      .then((content) => {
        if (!cancelled) {
          setTemplateContent(content);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message);
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [template, loadTemplateContent]);

  const handleContainerClick = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const target = (e.target as HTMLElement).closest("[data-action]");
      if (!target || !onAction || !template) return;

      const action = target.getAttribute("data-action");
      const paramsStr = target.getAttribute("data-params") || "{}";

      if (!action) return;

      let params: Record<string, unknown>;
      try {
        params = JSON.parse(paramsStr);
      } catch {
        params = {};
      }

      onAction({
        action,
        params,
        toolName: template.tool_name,
        serverName: template.server_name,
      });
    },
    [onAction, template],
  );

  if (!template) {
    return null;
  }

  if (isLoading) {
    return (
      <ChainOfThoughtStep label={template.card_title || toolName} icon={getLucideIcon(template.icon) || lucideIcons.WrenchIcon}>
        <ChainOfThoughtSearchResult>Loading template...</ChainOfThoughtSearchResult>
      </ChainOfThoughtStep>
    );
  }

  if (error || !templateContent) {
    return (
      <ChainOfThoughtStep label={template.card_title || toolName} icon={getLucideIcon(template.icon) || lucideIcons.WrenchIcon}>
        <ChainOfThoughtSearchResult className="text-destructive">
          {error || "Template not found"}
        </ChainOfThoughtSearchResult>
      </ChainOfThoughtStep>
    );
  }

  const parsedResult = parseResult(result);

  let flattenedResult: Record<string, unknown>;
  
  if (toolName.includes("weather")) {
    flattenedResult = parseWeatherResult(parsedResult, args);
  } else if (toolName.includes("mcd") || toolName.includes("mall") || toolName.includes("account") || toolName.includes("coupon") || toolName.includes("meal")) {
    flattenedResult = parseMCDResult(toolName, parsedResult, args);
  } else {
    flattenedResult = parsedResult;
  }

  const view = {
    args: args || {},
    result: flattenedResult,
  };

  let renderedHtml: string;
  try {
    renderedHtml = Mustache.render(templateContent, view);
  } catch (renderError) {
    return (
      <ChainOfThoughtStep label={template.card_title || toolName} icon={getLucideIcon(template.icon) || lucideIcons.WrenchIcon}>
        <ChainOfThoughtSearchResult className="text-destructive">
          Template render error: {(renderError as Error).message}
        </ChainOfThoughtSearchResult>
      </ChainOfThoughtStep>
    );
  }

  const IconComponent = getLucideIcon(template.icon) || lucideIcons.WrenchIcon;

  return (
    <ChainOfThoughtStep label={template.card_title || toolName} icon={IconComponent}>
      <div
        ref={containerRef}
        className="mcp-card-container mt-2"
        dangerouslySetInnerHTML={{ __html: renderedHtml }}
        onClick={handleContainerClick}
      />
    </ChainOfThoughtStep>
  );
}
