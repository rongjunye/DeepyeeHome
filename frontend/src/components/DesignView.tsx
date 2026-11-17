import type { ReactNode } from "react";
import { PlotlyChart } from "./PlotlyChart";
import { Room3D } from "./Room3D";
import type { Design } from "../types";

const money = (value: number) =>
  "¥" + Number(value || 0).toLocaleString("zh-CN", { maximumFractionDigits: 0 });

const card = "rounded-[14px] border border-line bg-surface p-5";
const h2 = "mb-2.5 font-serif text-[17px]";

function SectionTitle({ children }: { children: ReactNode }) {
  return <h2 className="mb-4 mt-8 font-serif text-[22px]">{children}</h2>;
}

interface Props {
  design: Design;
  onDownloadReport: () => void;
  extraActions?: ReactNode;
}

/** 方案正文渲染（方案详情页与分享页共用）。 */
export function DesignView({ design, onDownloadReport, extraActions }: Props) {
  const budget = design.budget;
  const palette = design.color_palette ?? [];
  const materials = design.materials ?? [];

  return (
    <div>
      {/* 头部 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="rounded-full border border-gold/35 bg-gold/10 px-2.5 py-1 text-xs text-gold">
            {design.style}风格
          </span>
          <span className="rounded-full border border-line bg-white/5 px-2.5 py-1 text-xs text-muted">
            引擎：{design.provider}
          </span>
        </div>
        <div className="flex flex-wrap gap-2">
          {extraActions}
          <button
            onClick={onDownloadReport}
            className="rounded-[11px] border border-line bg-white/5 px-3.5 py-2 text-[13px] transition hover:bg-white/10"
          >
            下载 PDF 报告
          </button>
        </div>
      </div>

      <h1 className="mt-4 font-serif text-[26px]">设计方案 #{design.id}</h1>
      <p className="text-[13px] text-muted">
        生成于 {new Date(design.created_at).toLocaleString("zh-CN", { hour12: false })}
      </p>

      {/* 总述 */}
      <div className={`${card} mt-5`}>
        <h2 className={h2}>方案总述</h2>
        <p className="text-[15px] leading-relaxed">{design.summary}</p>
      </div>

      {/* 布局 + 风格 */}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className={card}>
          <h2 className={h2}>空间布局与动线</h2>
          <p className="whitespace-pre-wrap text-[14px] leading-relaxed text-[#c9c6c0]">
            {design.layout_plan}
          </p>
        </div>
        <div className={card}>
          <h2 className={h2}>风格落地要点</h2>
          <p className="whitespace-pre-wrap text-[14px] leading-relaxed text-[#c9c6c0]">
            {design.style_recommendation}
          </p>
        </div>
      </div>

      {/* 3D 预览 */}
      <SectionTitle>3D 户型预览</SectionTitle>
      <div className={card}>
        <Room3D layout={design.layout3d} height={480} />
        <p className="mt-3 text-[13px] text-muted">
          依据布局数据实时生成的三维户型（非真实渲染效果图），用于直观感受空间关系与分区。
        </p>
      </div>

      {/* 配色 */}
      {palette.length > 0 && (
        <>
          <SectionTitle>配色方案</SectionTitle>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {palette.map((color) => (
              <div
                key={color.hex + color.name}
                className="flex items-center gap-3 rounded-[10px] border border-line bg-black/20 p-3"
              >
                <span
                  className="h-9 w-9 shrink-0 rounded-lg border border-white/15"
                  style={{ background: color.hex }}
                />
                <div>
                  <div className="text-sm">{color.name}</div>
                  <div className="text-[13px] text-muted">{color.hex}</div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* 预算 */}
      <SectionTitle>预算估算</SectionTitle>
      <div className="grid gap-4 lg:grid-cols-2">
        <div className={card}>
          <div className="flex items-center justify-between py-2">
            <span className="text-muted">建筑面积</span>
            <strong>{budget.area} ㎡</strong>
          </div>
          <hr className="my-2 border-line" />
          <div className="flex items-center justify-between py-2">
            <span className="text-muted">综合单价</span>
            <strong>{money(budget.per_sqm)} / ㎡</strong>
          </div>
          <hr className="my-2 border-line" />
          <div className="flex items-center justify-between py-2">
            <span className="text-muted">档位</span>
            <strong>{budget.level_label}</strong>
          </div>
          <hr className="my-2 border-line" />
          <div className="flex items-center justify-between py-2">
            <span className="text-muted">预估总价</span>
            <strong className="text-[22px] text-gold">{money(budget.total)}</strong>
          </div>
          <p className="mt-3.5 text-[13px] leading-relaxed text-muted">{budget.note}</p>
        </div>
        <div className={card}>
          <PlotlyChart figure={design.chart_spec?.budget_pie} height={330} />
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className={card}>
          <PlotlyChart figure={design.chart_spec?.material_bar} height={330} />
        </div>
        <div className={card}>
          <PlotlyChart figure={design.chart_spec?.style_radar} height={330} />
        </div>
      </div>

      {/* 材料清单 */}
      {materials.length > 0 && (
        <>
          <SectionTitle>材料清单</SectionTitle>
          <div className={`${card} overflow-x-auto`}>
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="text-left text-muted">
                  <th className="border-b border-line px-2 py-2.5">类别</th>
                  <th className="border-b border-line px-2 py-2.5">材料 / 工艺</th>
                  <th className="border-b border-line px-2 py-2.5">规格</th>
                  <th className="border-b border-line px-2 py-2.5 text-right">预估费用</th>
                </tr>
              </thead>
              <tbody>
                {materials.map((material) => (
                  <tr key={material.category + material.name}>
                    <td className="border-b border-line px-2 py-2.5">{material.category}</td>
                    <td className="border-b border-line px-2 py-2.5">{material.name}</td>
                    <td className="border-b border-line px-2 py-2.5 text-muted">
                      {material.specification}
                    </td>
                    <td className="border-b border-line px-2 py-2.5 text-right">
                      {money(material.estimated_cost)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
