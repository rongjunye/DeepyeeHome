import { useCallback, useRef, type PointerEvent as ReactPointerEvent } from "react";
import type { LayoutRoom, ProjectLayout } from "../types";

/**
 * 户型标注编辑器。
 *
 * 在户型图上方叠加可拖拽 / 可缩放 / 可命名的矩形，用来描述真实房间位置。
 * 所有坐标都以「归一化值 0~1」存储，因此与容器尺寸、窗口缩放无关。
 */

const MIN_SIZE = 0.03; // 最小边长（归一化）

const TYPE_COLOR: Record<string, string> = {
  living: "#C89F6D",
  dining: "#D9A86C",
  kitchen: "#8FA98F",
  master: "#8C7BB0",
  bedroom: "#7FA6A0",
  bath: "#6B8DD6",
  balcony: "#B8BDC4",
  entry: "#C4A0A0",
  other: "#9AA0A6",
};

type Handle = "nw" | "ne" | "sw" | "se";

interface Props {
  imageUrl: string;
  aspect: number; // 高 / 宽
  value: ProjectLayout;
  onChange: (next: ProjectLayout) => void;
  selected: number | null;
  onSelect: (index: number | null) => void;
}

const clamp = (v: number, min: number, max: number) => Math.min(Math.max(v, min), max);

export function FloorplanEditor({ imageUrl, aspect, value, onChange, selected, onSelect }: Props) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const rooms = value.rooms;

  /** 把指针位移换算成归一化位移并回调 */
  const beginDrag = useCallback(
    (event: ReactPointerEvent, index: number, mode: "move" | "resize", handle?: Handle) => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      event.preventDefault();
      event.stopPropagation();

      const rect = canvas.getBoundingClientRect();
      const startX = event.clientX;
      const startY = event.clientY;
      const room = rooms[index];

      const onMove = (moveEvent: PointerEvent) => {
        const dx = (moveEvent.clientX - startX) / rect.width;
        const dy = (moveEvent.clientY - startY) / rect.height;

        let next: LayoutRoom;
        if (mode === "move") {
          next = {
            ...room,
            x: clamp(room.x + dx, 0, 1 - room.w),
            y: clamp(room.y + dy, 0, 1 - room.h),
          };
        } else {
          // 先算出四条边，再按被拖动的角/边分别夹取
          let left = room.x;
          let top = room.y;
          let right = room.x + room.w;
          let bottom = room.y + room.h;

          if (handle!.includes("w")) left = clamp(left + dx, 0, right - MIN_SIZE);
          if (handle!.includes("e")) right = clamp(right + dx, left + MIN_SIZE, 1);
          if (handle!.includes("n")) top = clamp(top + dy, 0, bottom - MIN_SIZE);
          if (handle!.includes("s")) bottom = clamp(bottom + dy, top + MIN_SIZE, 1);

          next = { ...room, x: left, y: top, w: right - left, h: bottom - top };
        }

        const updated = rooms.map((item, i) => (i === index ? next : item));
        onChange({ ...value, rooms: updated });
      };

      const onUp = () => {
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
      };

      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    },
    [rooms, value, onChange]
  );

  const handles: Handle[] = ["nw", "ne", "sw", "se"];

  return (
    <div
      ref={canvasRef}
      className="relative w-full select-none overflow-hidden rounded-[10px] border border-line bg-black/40"
      style={{ paddingTop: `${aspect * 100}%` }}
      onPointerDown={() => onSelect(null)}
    >
      <img
        src={imageUrl}
        alt="户型图"
        draggable={false}
        className="absolute inset-0 h-full w-full object-fill opacity-90"
      />

      {rooms.map((room, index) => {
        const color = room.color || TYPE_COLOR[room.type] || TYPE_COLOR.other;
        const isSelected = index === selected;
        return (
          <div
            key={index}
            className="absolute cursor-move"
            style={{
              left: `${room.x * 100}%`,
              top: `${room.y * 100}%`,
              width: `${room.w * 100}%`,
              height: `${room.h * 100}%`,
              background: `${color}33`,
              border: `2px solid ${isSelected ? "#ffffff" : color}`,
              borderRadius: 6,
            }}
            onPointerDown={(e) => {
              e.stopPropagation();
              onSelect(index);
              beginDrag(e, index, "move");
            }}
          >
            <span
              className="pointer-events-none absolute left-1 top-1 max-w-[calc(100%-8px)] truncate rounded px-1.5 py-0.5 text-[11px] font-medium"
              style={{ background: "rgba(15,17,21,0.75)", color: "#e8e6e1" }}
            >
              {room.name}
            </span>

            {isSelected &&
              handles.map((handle) => (
                <span
                  key={handle}
                  className="absolute h-3 w-3 rounded-full border border-[#0f1115] bg-white"
                  style={{
                    left: handle.includes("w") ? -6 : undefined,
                    right: handle.includes("e") ? -6 : undefined,
                    top: handle.includes("n") ? -6 : undefined,
                    bottom: handle.includes("s") ? -6 : undefined,
                    cursor: `${handle}-resize`,
                  }}
                  onPointerDown={(e) => beginDrag(e, index, "resize", handle)}
                />
              ))}
          </div>
        );
      })}
    </div>
  );
}

export { TYPE_COLOR };