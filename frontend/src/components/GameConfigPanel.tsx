import { useState } from "react";
import type { AgentConfig } from "../types";
import PromptPreview from "./PromptPreview";

interface Props {
  managerConfig: AgentConfig;
  playerConfig: AgentConfig;
  onConfigChange: (type: "manager" | "player", config: AgentConfig) => void;
}

type Tab = "manager" | "player" | "model";

export default function GameConfigPanel({
  managerConfig,
  playerConfig,
  onConfigChange,
}: Props) {
  const [tab, setTab] = useState<Tab>("manager");
  const [previewPrompt, setPreviewPrompt] = useState<string | null>(null);

  const tabs: { key: Tab; label: string }[] = [
    { key: "manager", label: "Manager" },
    { key: "player", label: "Player" },
    { key: "model", label: "Model" },
  ];

  const handleFileLoad = (type: "manager" | "player") => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".md,.txt";
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      const text = await file.text();
      const config = type === "manager" ? managerConfig : playerConfig;
      onConfigChange(type, { ...config, system_prompt: text.trim() });
    };
    input.click();
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Tabs */}
      <div className="flex border-b shrink-0">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 px-4 py-2.5 text-sm font-medium ${
              tab === t.key
                ? "border-b-2 border-cyan-600 text-cyan-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {tab === "manager" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Manager System Prompt
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewPrompt(managerConfig.system_prompt)}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Preview
                </button>
                <button
                  onClick={() => handleFileLoad("manager")}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Load .md
                </button>
              </div>
            </div>
            <textarea
              value={managerConfig.system_prompt}
              onChange={(e) =>
                onConfigChange("manager", {
                  ...managerConfig,
                  system_prompt: e.target.value,
                })
              }
              rows={12}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
        )}

        {tab === "player" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                Player System Prompt
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewPrompt(playerConfig.system_prompt)}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Preview
                </button>
                <button
                  onClick={() => handleFileLoad("player")}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Load .md
                </button>
              </div>
            </div>
            <textarea
              value={playerConfig.system_prompt}
              onChange={(e) =>
                onConfigChange("player", {
                  ...playerConfig,
                  system_prompt: e.target.value,
                })
              }
              rows={12}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-cyan-500"
            />
          </div>
        )}

        {tab === "model" && (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Model
              </label>
              <select
                value={managerConfig.model}
                onChange={(e) => {
                  onConfigChange("manager", {
                    ...managerConfig,
                    model: e.target.value,
                  });
                  onConfigChange("player", {
                    ...playerConfig,
                    model: e.target.value,
                  });
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              >
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Temperature: {managerConfig.temperature}
              </label>
              <input
                type="range"
                min={0}
                max={2}
                step={0.1}
                value={managerConfig.temperature}
                onChange={(e) => {
                  const temp = parseFloat(e.target.value);
                  onConfigChange("manager", {
                    ...managerConfig,
                    temperature: temp,
                  });
                  onConfigChange("player", {
                    ...playerConfig,
                    temperature: temp,
                  });
                }}
                className="w-full"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Manager Max Tokens
              </label>
              <input
                type="number"
                min={50}
                max={4096}
                value={managerConfig.max_tokens}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 500;
                  onConfigChange("manager", {
                    ...managerConfig,
                    max_tokens: val,
                  });
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Player Max Tokens
              </label>
              <input
                type="number"
                min={10}
                max={1000}
                value={playerConfig.max_tokens}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 100;
                  onConfigChange("player", {
                    ...playerConfig,
                    max_tokens: val,
                  });
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Prompt Preview Modal */}
      {previewPrompt !== null && (
        <PromptPreview
          prompt={previewPrompt}
          onClose={() => setPreviewPrompt(null)}
        />
      )}
    </div>
  );
}
