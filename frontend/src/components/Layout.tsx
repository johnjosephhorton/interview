import type { ReactNode } from "react";

interface Props {
  left: ReactNode;
  right: ReactNode;
}

export default function Layout({ left, right }: Props) {
  return (
    <div className="h-screen flex flex-col">
      <header className="bg-white border-b px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="text-lg font-semibold text-gray-800">AI Interviewer</h1>
      </header>
      <div className="flex flex-1 min-h-0">
        <div className="w-[60%] border-r flex flex-col">{left}</div>
        <div className="w-[40%] flex flex-col">{right}</div>
      </div>
    </div>
  );
}
