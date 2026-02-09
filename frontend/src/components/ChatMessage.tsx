import type { Message } from "../types";

interface Props {
  message: Message;
}

export default function ChatMessage({ message }: Props) {
  const isInterviewer = message.role === "interviewer";

  return (
    <div className={`flex ${isInterviewer ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isInterviewer
            ? "bg-blue-100 text-blue-900"
            : "bg-gray-200 text-gray-900"
        }`}
      >
        <div className="text-xs font-medium mb-1 opacity-60">
          {isInterviewer ? "Interviewer" : "Respondent"}
        </div>
        <div className="text-sm whitespace-pre-wrap">{message.text}</div>
      </div>
    </div>
  );
}
