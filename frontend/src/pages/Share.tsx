import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, downloadReport, sharedReportUrl } from "../api";
import { DesignView } from "../components/DesignView";
import { toast } from "../toast";
import type { Design } from "../types";

/** 公开分享页：无需登录，只读。 */
export function SharePage() {
  const { token } = useParams();
  const [design, setDesign] = useState<Design | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  async function load() {
    try {
      setDesign(await api<Design>(`/share/${token}`, { auth: false }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }

  async function handleDownload() {
    if (!token) return;
    try {
      await downloadReport(sharedReportUrl(token), `NeuroArchAI-share-${token.slice(0, 8)}.pdf`);
      toast("报告已开始下载", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "导出失败", "error");
    }
  }

  if (error) {
    return (
      <div className="mx-auto w-[92%] max-w-[1160px] py-16">
        <div className="rounded-[14px] border border-dashed border-line p-11 text-center text-muted">
          无法查看：{error}
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
        <span className="rounded-full border border-gold/35 bg-gold/10 px-2.5 py-1 text-xs text-gold">
          分享方案 · 只读
        </span>
      </div>

      <DesignView design={design} onDownloadReport={handleDownload} />

      <p className="mt-8 text-center text-[13px] text-muted">
        由{" "}
        <Link to="/" className="text-gold">
          NeuroArchAI Platform
        </Link>{" "}
        生成
      </p>
    </div>
  );
}
