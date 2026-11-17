import { useEffect, useRef, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, auth, floorplanUrl } from "../api";
import { toast } from "../toast";
import { BUDGET_LEVELS, STYLE_OPTIONS } from "../types";
import type { Design, DesignListItem, Project } from "../types";

const inputClass =
  "w-full rounded-[11px] border border-line bg-black/25 px-3.5 py-2.5 text-sm outline-none transition focus:border-gold/60 focus:ring-3 focus:ring-gold/12";
const labelClass = "mb-1.5 block text-[13px] text-muted";
const cardClass = "rounded-[14px] border border-line bg-surface p-5";

export function Studio() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [selected, setSelected] = useState<Project | null>(null);
  const [designs, setDesigns] = useState<DesignListItem[]>([]);

  const [creating, setCreating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  // 新建项目表单
  const [title, setTitle] = useState("");
  const [area, setArea] = useState("");
  const [rooms, setRooms] = useState("");
  const [description, setDescription] = useState("");

  // 生成方案表单
  const [style, setStyle] = useState(STYLE_OPTIONS[0]);
  const [genArea, setGenArea] = useState("");
  const [budgetLevel, setBudgetLevel] = useState("standard");
  const [requirements, setRequirements] = useState("");

  useEffect(() => {
    if (!auth.isLoggedIn) {
      navigate("/login");
      return;
    }
    loadProjects();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function loadProjects() {
    try {
      setProjects(await api<Project[]>("/projects"));
    } catch (error) {
      toast(error instanceof Error ? error.message : "加载失败", "error");
    }
  }

  async function createProject(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) {
      toast("请填写项目名称", "error");
      return;
    }
    setCreating(true);
    try {
      const meta_info: Record<string, unknown> = {};
      if (area) meta_info.area = Number(area);
      if (rooms) meta_info.rooms = rooms;

      const project = await api<Project>("/projects", {
        method: "POST",
        body: { title: title.trim(), description, meta_info },
      });
      toast("项目创建成功", "success");
      setTitle("");
      setArea("");
      setRooms("");
      setDescription("");
      await loadProjects();
      await openProject(project.id);
    } catch (error) {
      toast(error instanceof Error ? error.message : "创建失败", "error");
    } finally {
      setCreating(false);
    }
  }

  async function openProject(id: number) {
    try {
      const project = await api<Project>(`/projects/${id}`);
      setSelected(project);
      setGenArea(String(project.meta_info?.area ?? ""));
      await loadDesigns(id);
      window.scrollTo({ top: 320, behavior: "smooth" });
    } catch (error) {
      toast(error instanceof Error ? error.message : "打开失败", "error");
    }
  }

  async function loadDesigns(projectId: number) {
    try {
      setDesigns(await api<DesignListItem[]>(`/projects/${projectId}/designs`));
    } catch {
      setDesigns([]);
    }
  }

  async function upload(file: File) {
    if (!selected) return;
    const form = new FormData();
    form.append("file", file);
    toast("正在上传户型图…");
    try {
      const updated = await api<Project>(`/projects/${selected.id}/floorplan`, {
        method: "POST",
        body: form,
        isForm: true,
      });
      setSelected(updated);
      toast("户型图上传成功", "success");
      loadProjects();
    } catch (error) {
      toast(error instanceof Error ? error.message : "上传失败", "error");
    }
  }

  async function generate(event: FormEvent) {
    event.preventDefault();
    if (!selected) return;
    setGenerating(true);
    try {
      const body: Record<string, unknown> = { style, budget_level: budgetLevel, requirements };
      if (genArea) body.area = Number(genArea);

      const design = await api<Design>(`/projects/${selected.id}/designs`, {
        method: "POST",
        body,
      });
      toast("方案生成成功", "success");
      navigate(`/design/${design.id}`);
    } catch (error) {
      toast(error instanceof Error ? error.message : "生成失败", "error");
      setGenerating(false);
    }
  }

  return (
    <div className="mx-auto w-[92%] max-w-[1160px] py-9 pb-16">
      <h1 className="font-serif text-[22px]">工作台</h1>
      <p className="mt-[-4px] text-[13px] text-muted">创建项目 → 上传户型图 → 生成 AI 设计方案</p>

      {/* 新建项目 */}
      <div className={`${cardClass} mt-5`}>
        <h2 className="mb-4 text-base font-semibold">新建项目</h2>
        <form onSubmit={createProject}>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className={labelClass}>项目名称 *</label>
              <input
                className={inputClass}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="例如：城南小区 120㎡ 三居"
              />
            </div>
            <div>
              <label className={labelClass}>建筑面积（㎡）</label>
              <input
                className={inputClass}
                type="number"
                min={10}
                max={2000}
                step={0.1}
                value={area}
                onChange={(e) => setArea(e.target.value)}
                placeholder="120"
              />
            </div>
            <div>
              <label className={labelClass}>房间构成</label>
              <input
                className={inputClass}
                value={rooms}
                onChange={(e) => setRooms(e.target.value)}
                placeholder="3室2厅1卫"
              />
            </div>
            <div>
              <label className={labelClass}>备注</label>
              <input
                className={inputClass}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="采光好、想扩大厨房…"
              />
            </div>
          </div>
          <button
            type="submit"
            disabled={creating}
            className="mt-4 rounded-[11px] bg-gradient-to-br from-gold to-[#b98a54] px-5 py-2.5 text-sm font-semibold text-[#17130c] transition hover:brightness-105 disabled:opacity-50"
          >
            {creating ? "创建中…" : "创建项目"}
          </button>
        </form>
      </div>

      {/* 项目列表 */}
      <h2 className="mt-9 mb-4 font-serif text-[22px]">我的项目</h2>
      {projects.length === 0 ? (
        <div className="rounded-[14px] border border-dashed border-line p-11 text-center text-muted">
          还没有项目，先在上方新建一个吧
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <button
              key={project.id}
              onClick={() => openProject(project.id)}
              className="rounded-[14px] border border-line bg-surface p-5 text-left transition hover:border-gold/40 hover:bg-surface2"
            >
              <div className="flex items-start justify-between gap-3">
                <h3 className="text-base font-semibold">{project.title}</h3>
                <span className="shrink-0 rounded-full border border-line bg-white/5 px-2.5 py-1 text-xs text-muted">
                  {project.design_count} 套方案
                </span>
              </div>
              <p className="mt-2.5 text-[13px] text-muted">{project.description || "暂无备注"}</p>
              <p className="mt-1.5 text-[13px] text-muted">
                {project.meta_info?.area ? `${String(project.meta_info.area)}㎡ · ` : ""}
                {String(project.meta_info?.rooms ?? "")}
              </p>
              <p className="mt-2 text-[13px] text-muted">
                {project.floorplan_path ? "✅ 已上传户型图" : "⚠️ 未上传户型图"}
              </p>
            </button>
          ))}
        </div>
      )}

      {/* 项目详情 */}
      {selected && (
        <section className="mt-9">
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-serif text-[22px]">{selected.title}</h2>
            <button
              onClick={() => setSelected(null)}
              className="rounded-[11px] border border-line bg-white/5 px-3.5 py-2 text-[13px] transition hover:bg-white/10"
            >
              收起
            </button>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {/* 户型图 */}
            <div className={cardClass}>
              <h3 className="mb-3.5 text-base font-semibold">户型图</h3>
              <div
                onClick={() => fileRef.current?.click()}
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragOver(true);
                }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => {
                  e.preventDefault();
                  setDragOver(false);
                  if (e.dataTransfer.files[0]) upload(e.dataTransfer.files[0]);
                }}
                className={`cursor-pointer rounded-[14px] border-[1.5px] border-dashed p-6 text-center transition ${
                  dragOver
                    ? "border-gold bg-gold/10"
                    : "border-gold/45 bg-gold/[0.04] hover:bg-gold/10"
                }`}
              >
                <p>点击或拖拽图片到此处上传</p>
                <p className="mt-1.5 text-[13px] text-muted">支持 PNG / JPG / WEBP，≤ 10MB</p>
                {selected.floorplan_path && (
                  <img
                    src={floorplanUrl(selected.floorplan_path)}
                    alt="户型图"
                    className="mx-auto mt-3 max-h-[200px] rounded-[10px]"
                  />
                )}
              </div>
              <input
                ref={fileRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                hidden
                onChange={(e) => {
                  if (e.target.files?.[0]) upload(e.target.files[0]);
                }}
              />
            </div>

            {/* 生成方案 */}
            <div className={cardClass}>
              <h3 className="mb-3.5 text-base font-semibold">生成设计方案</h3>
              <form onSubmit={generate}>
                <div className="mb-4">
                  <label className={labelClass}>设计风格</label>
                  <select
                    className={inputClass}
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                  >
                    {STYLE_OPTIONS.map((option) => (
                      <option key={option}>{option}</option>
                    ))}
                  </select>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <label className={labelClass}>面积（㎡）</label>
                    <input
                      className={inputClass}
                      type="number"
                      min={10}
                      max={2000}
                      step={0.1}
                      value={genArea}
                      onChange={(e) => setGenArea(e.target.value)}
                      placeholder="沿用项目面积"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>预算档位</label>
                    <select
                      className={inputClass}
                      value={budgetLevel}
                      onChange={(e) => setBudgetLevel(e.target.value)}
                    >
                      {BUDGET_LEVELS.map((level) => (
                        <option key={level.value} value={level.value}>
                          {level.label}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-4">
                  <label className={labelClass}>额外需求</label>
                  <textarea
                    className={`${inputClass} min-h-[84px] resize-y`}
                    value={requirements}
                    onChange={(e) => setRequirements(e.target.value)}
                    placeholder="例如：需要独立书房、喜欢原木风、在意收纳…"
                  />
                </div>
                <button
                  type="submit"
                  disabled={generating}
                  className="mt-4 rounded-[11px] bg-gradient-to-br from-gold to-[#b98a54] px-5 py-2.5 text-sm font-semibold text-[#17130c] transition hover:brightness-105 disabled:opacity-50"
                >
                  {generating ? "AI 生成中，请稍候…" : "生成方案 ✨"}
                </button>
              </form>
            </div>
          </div>

          {/* 方案列表 */}
          <h3 className="mt-7 mb-3.5 text-base font-semibold">该项目的设计方案</h3>
          {designs.length === 0 ? (
            <div className="rounded-[14px] border border-dashed border-line p-6 text-center text-muted">
              还没有方案，选择一个风格生成吧
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {designs.map((design) => (
                <button
                  key={design.id}
                  onClick={() => navigate(`/design/${design.id}`)}
                  className="rounded-[14px] border border-line bg-surface p-5 text-left transition hover:border-gold/40 hover:bg-surface2"
                >
                  <div className="flex items-start justify-between gap-3">
                    <h4 className="text-[15px] font-semibold">{design.style}</h4>
                    <span
                      className={`shrink-0 rounded-full border px-2.5 py-1 text-xs ${
                        design.is_public
                          ? "border-gold/35 bg-gold/10 text-gold"
                          : "border-line bg-white/5 text-muted"
                      }`}
                    >
                      {design.is_public ? "已分享" : "私密"}
                    </span>
                  </div>
                  <p className="mt-2.5 text-[13px] text-muted">
                    {design.summary.slice(0, 70)}…
                  </p>
                  <p className="mt-2 text-[13px] text-muted">
                    {new Date(design.created_at).toLocaleString("zh-CN", { hour12: false })}
                  </p>
                </button>
              ))}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
