import { useEffect, useState } from "react";
import { subscribeToasts, type ToastItem } from "../toast";

const TONE: Record<ToastItem["type"], string> = {
  info: "border-line text-[#e8e6e1]",
  success: "border-teal/50 text-[#a9d2cc]",
  error: "border-danger/50 text-[#f0b79c]",
};

/** 全局提示条容器。 */
export function Toaster() {
  const [items, setItems] = useState<ToastItem[]>([]);

  useEffect(() => subscribeToasts(setItems), []);

  return (
    <div className="pointer-events-none fixed right-5 top-[76px] z-[90] flex flex-col gap-2.5">
      {items.map((item) => (
        <div
          key={item.id}
          className={`pointer-events-auto max-w-[320px] rounded-[11px] border bg-surface2 px-4 py-3 text-sm shadow-[0_12px_30px_rgba(0,0,0,0.45)] ${TONE[item.type]}`}
        >
          {item.text}
        </div>
      ))}
    </div>
  );
}
