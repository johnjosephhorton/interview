import { useState } from "react";
import type { AgentConfig } from "../types";
import PromptPreview from "./PromptPreview";

interface Props {
  interviewerConfig: AgentConfig;
  respondentConfig: AgentConfig;
  onConfigChange: (type: "interviewer" | "respondent", config: AgentConfig) => void;
}

type Tab = "interviewer" | "respondent" | "model";

export default function ConfigPanel({
  interviewerConfig,
  respondentConfig,
  onConfigChange,
}: Props) {
  const [tab, setTab] = useState<Tab>("interviewer");
  const [previewPrompt, setPreviewPrompt] = useState<string | null>(null);

  const tabs: { key: Tab; label: string }[] = [
    { key: "interviewer", label: "Interviewer" },
    { key: "respondent", label: "Respondent" },
    { key: "model", label: "Model" },
  ];

  const handleFileLoad = (type: "interviewer" | "respondent") => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".md,.txt";
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      const text = await file.text();
      const config = type === "interviewer" ? interviewerConfig : respondentConfig;
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
                ? "border-b-2 border-blue-600 text-blue-600"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {tab === "interviewer" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                System Prompt
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewPrompt(interviewerConfig.system_prompt)}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Preview
                </button>
                <button
                  onClick={() => handleFileLoad("interviewer")}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Load .md
                </button>
              </div>
            </div>
            <textarea
              value={interviewerConfig.system_prompt}
              onChange={(e) =>
                onConfigChange("interviewer", {
                  ...interviewerConfig,
                  system_prompt: e.target.value,
                })
              }
              rows={12}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        )}

        {tab === "respondent" && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-gray-700">
                System Prompt
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setPreviewPrompt(respondentConfig.system_prompt)}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Preview
                </button>
                <button
                  onClick={() => handleFileLoad("respondent")}
                  className="text-xs px-2 py-1 rounded bg-gray-100 hover:bg-gray-200"
                >
                  Load .md
                </button>
              </div>
            </div>
            <textarea
              value={respondentConfig.system_prompt}
              onChange={(e) =>
                onConfigChange("respondent", {
                  ...respondentConfig,
                  system_prompt: e.target.value,
                })
              }
              rows={12}
              className="w-full border rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500"
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
                value={interviewerConfig.model}
                onChange={(e) => {
                  onConfigChange("interviewer", {
                    ...interviewerConfig,
                    model: e.target.value,
                  });
                  onConfigChange("respondent", {
                    ...respondentConfig,
                    model: e.target.value,
                  });
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="gpt-4o-mini">gpt-4o-mini</option>
                <option value="gpt-4o">gpt-4o</option>
                <option value="gpt-4-turbo">gpt-4-turbo</option>
                <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Temperature: {interviewerConfig.temperature}
              </label>
              <input
                type="range"
                min={0}
                max={2}
                step={0.1}
                value={interviewerConfig.temperature}
                onChange={(e) => {
                  const temp = parseFloat(e.target.value);
                  onConfigChange("interviewer", {
                    ...interviewerConfig,
                    temperature: temp,
                  });
                  onConfigChange("respondent", {
                    ...respondentConfig,
                    temperature: temp,
                  });
                }}
                className="w-full"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 block mb-1">
                Max Tokens
              </label>
              <input
                type="number"
                min={50}
                max={4096}
                value={interviewerConfig.max_tokens}
                onChange={(e) => {
                  const val = parseInt(e.target.value) || 200;
                  onConfigChange("interviewer", {
                    ...interviewerConfig,
                    max_tokens: val,
                  });
                  onConfigChange("respondent", {
                    ...respondentConfig,
                    max_tokens: val,
                  });
                }}
                className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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
