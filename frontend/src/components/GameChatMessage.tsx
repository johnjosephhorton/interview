import type { GameMessage } from "../types";

interface Props {
  message: GameMessage;
}

export default function GameChatMessage({ message }: Props) {
  const isManager = message.role === "manager";

  return (
    <div className={`flex ${isManager ? "justify-start" : "justify-end"}`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          isManager
            ? "bg-cyan-100 text-cyan-900"
            : "bg-gray-200 text-gray-900"
        }`}
      >
        <div className="text-xs font-medium mb-1 opacity-60">
          {isManager ? "Game Manager" : "You"}
        </div>
        <div className="text-sm whitespace-pre-wrap">{message.text}</div>
      </div>
    </div>
  );
}
