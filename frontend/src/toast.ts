/** 轻量级全局提示条（Toast），无需 Context 嵌套。 */

export interface ToastItem {
  id: number;
  text: string;
  type: "info" | "success" | "error";
}

type Listener = (items: ToastItem[]) => void;

let items: ToastItem[] = [];
let listeners: Listener[] = [];
let seq = 0;

export function toast(text: string, type: ToastItem["type"] = "info"): void {
  const item: ToastItem = { id: ++seq, text, type };
  items = [...items, item];
  listeners.forEach((listener) => listener(items));
  setTimeout(() => {
    items = items.filter((current) => current.id !== item.id);
    listeners.forEach((listener) => listener(items));
  }, 3200);
}

export function subscribeToasts(listener: Listener): () => void {
  listeners.push(listener);
  listener(items);
  return () => {
    listeners = listeners.filter((current) => current !== listener);
  };
}
