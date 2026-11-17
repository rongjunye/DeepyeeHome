import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api, auth, downloadReport, reportUrl } from "../api";
import { DesignView } from "../components/DesignView";
import { toast } from "../toast";
import type { Design } from "../types";

export function DesignPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [design, setDesign] = useState<Design | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!auth.isLoggedIn) {
      navigate("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function load() {
    try {
      setDesign(await api<Design>(`/designs/${id}`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }

  const shareUrl = design ? `${location.origin}/share/${design.share_token}` : "";

  async function toggleShare() {
    if (!design) return;
    try {
      const updated = await api<Design>(`/designs/${design.id}/share`, {
        method: "PATCH",
        body: { is_public: !design.is_public },
      });
      setDesign(updated);
      toast(updated.is_public ? "已开启分享" : "已关闭分享", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "操作失败", "error");
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(shareUrl);
      toast("链接已复制", "success");
    } catch {
      toast("复制失败，请手动复制", "error");
    }
  }

  async function handleDownload() {
    if (!design) return;
    try {
      await downloadReport(reportUrl(design.id), `NeuroArchAI-design-${design.id}.pdf`);
      toast("报告已开始下载", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "导出失败", "error");
    }
  }

  if (error) {
    return (
      <div className="mx-auto w-[92%] max-w-[1160px] py-16">
        <div className="rounded-[14px] border border-dashed border-line p-11 text-center text-muted">
          加载失败：{error}
        </div>
        <div className="mt-4 text-center">
          <Link to="/studio" className="text-gold">
            ← 返回工作台
          </Link>
        </div>
      </div>
    );
  }

  if (!design) {
    return (
      <div className="mx-auto w-[92%] max-w-[1160px] py-16 text-center text-muted">加载中…</div>
    );
  }

  return (
    <div className="mx-auto w-[92%] max-w-[1160px] py-9 pb-16">
      <div className="mb-4">
        <Link to="/studio" className="text-[13px] text-muted transition hover:text-[#e8e6e1]">
          ← 返回工作台
        </Link>
      </div>

      <DesignView
        design={design}
        onDownloadReport={handleDownload}
        extraActions={
          <>
            <button
              onClick={toggleShare}
              className="rounded-[11px] border border-line bg-white/5 px-3.5 py-2 text-[13px] transition hover:bg-white/10"
            >
              {design.is_public ? "设为私密" : "开启分享"}
            </button>
            <button
              onClick={copyLink}
              disabled={!design.is_public}
              className="rounded-[11px] border border-line bg-white/5 px-3.5 py-2 text-[13px] transition hover:bg-white/10 disabled:opacity-40"
            >
              复制链接
            </button>
          </>
        }
      />

      <div className="mt-6 rounded-[14px] border border-line bg-surface p-5">
        <div className="text-sm">
          {design.is_public
            ? "🔓 当前为公开状态，任何人都可通过链接查看"
            : "🔒 当前为私密状态，开启分享后可生成公开链接"}
        </div>
        {design.is_public && (
          <div className="mt-2 break-all text-[13px] text-muted">{shareUrl}</div>
        )}
      </div>
    </div>
  );
}
