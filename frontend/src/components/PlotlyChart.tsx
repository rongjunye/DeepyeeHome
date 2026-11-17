import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { FigureSpec } from "../types";

/** 用 Plotly.js 渲染后端生成的图表规格。 */
export function PlotlyChart({ figure, height = 320 }: { figure?: FigureSpec; height?: number }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node || !figure) return;

    Plotly.react(node, figure.data, figure.layout, {
      displayModeBar: false,
      responsive: true,
    });

    return () => {
      Plotly.purge(node);
    };
  }, [figure]);

  if (!figure) {
    return (
      <div style={{ height }} className="grid place-items-center text-sm text-muted">
        暂无图表数据
      </div>
    );
  }

  return <div ref={ref} style={{ width: "100%", height }} />;
}
