import type { ReactNode } from "react";

interface Props {
  left: ReactNode;
  right: ReactNode;
}

export default function Layout({ left, right }: Props) {
  return (
    <div className="h-full flex">
      <div className="w-[60%] border-r flex flex-col">{left}</div>
      <div className="w-[40%] flex flex-col">{right}</div>
    </div>
  );
}
