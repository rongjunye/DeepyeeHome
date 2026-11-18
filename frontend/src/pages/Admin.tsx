import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, auth } from "../api";
import { toast } from "../toast";
import type { AdminStats, AdminUser } from "../types";

const card = "rounded-[14px] border border-line bg-surface p-5";
const btn =
  "rounded-[11px] border border-line bg-white/5 px-3 py-1.5 text-[13px] transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-40";
const inputClass =
  "w-full rounded-[11px] border border-line bg-black/25 px-3.5 py-2.5 text-sm outline-none transition focus:border-gold/60 focus:ring-3 focus:ring-gold/12";

/** 管理后台：全局统计 + 用户管理 + 修改密码（仅管理员可访问）。 */
export function Admin() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [savingPassword, setSavingPassword] = useState(false);

  useEffect(() => {
    if (!auth.isLoggedIn) {
      navigate("/login");
      return;
    }
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function load() {
    setLoading(true);
    try {
      const [statsData, userData] = await Promise.all([
        api<AdminStats>("/admin/stats"),
        api<AdminUser[]>("/admin/users"),
      ]);
      setStats(statsData);
      setUsers(userData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  }

  async function toggle(user: AdminUser, field: "is_active" | "is_admin") {
    try {
      const updated = await api<AdminUser>(`/admin/users/${user.id}`, {
        method: "PATCH",
        body: { [field]: !user[field] },
      });
      setUsers((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      toast("已更新", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : "操作失败", "error");
    }
  }

  async function changePassword(event: FormEvent) {
    event.preventDefault();
    if (newPassword.length < 6) {
      toast("新密码至少 6 位", "error");
      return;
    }
    setSavingPassword(true);
    try {
      await api("/auth/change-password", {
        method: "POST",
        body: { old_password: oldPassword, new_password: newPassword },
      });
      toast("密码修改成功", "success");
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      toast(err instanceof Error ? err.message : "修改失败", "error");
    } finally {
      setSavingPassword(false);
    }
  }

  const myId = auth.user?.id;

  if (error) {
    return (
      <div className="mx-auto w-[92%] max-w-[1160px] py-16">
        <div className="rounded-[14px] border border-dashed border-line p-11 text-center text-muted">
          {error}
        </div>
        <p className="mt-4 text-center text-[13px] text-muted">
          该页面仅管理员可访问。如需管理员权限，请使用{" "}
          <code className="text-gold">scripts/create_admin.py</code> 授予。
        </p>
      </div>
    );
  }

  return (
    <div className="mx-auto w-[92%] max-w-[1160px] py-9 pb-16">
      <h1 className="font-serif text-[22px]">管理后台</h1>
      <p className="mt-[-4px] text-[13px] text-muted">全局统计 · 用户管理 · 账号安全</p>

      {/* 统计 */}
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {[
          { label: "总用户", value: stats?.total_users },
          { label: "启用中", value: stats?.active_users },
          { label: "管理员", value: stats?.admin_users },
          { label: "项目数", value: stats?.total_projects },
          { label: "方案数", value: stats?.total_designs },
        ].map((item) => (
          <div key={item.label} className={card}>
            <div className="text-[13px] text-muted">{item.label}</div>
            <div className="mt-1 font-serif text-2xl text-gold">
              {loading ? "…" : (item.value ?? 0)}
            </div>
          </div>
        ))}
      </div>

      {/* 用户管理 */}
      <h2 className="mt-9 mb-4 font-serif text-[22px]">用户管理</h2>
      <div className={`${card} overflow-x-auto`}>
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="text-left text-muted">
              <th className="border-b border-line px-2 py-2.5">ID</th>
              <th className="border-b border-line px-2 py-2.5">邮箱</th>
              <th className="border-b border-line px-2 py-2.5">用户名</th>
              <th className="border-b border-line px-2 py-2.5">角色</th>
              <th className="border-b border-line px-2 py-2.5">状态</th>
              <th className="border-b border-line px-2 py-2.5">项目/方案</th>
              <th className="border-b border-line px-2 py-2.5">注册时间</th>
              <th className="border-b border-line px-2 py-2.5 text-right">操作</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => {
              const isSelf = user.id === myId;
              return (
                <tr key={user.id}>
                  <td className="border-b border-line px-2 py-2.5">{user.id}</td>
                  <td className="border-b border-line px-2 py-2.5">{user.email}</td>
                  <td className="border-b border-line px-2 py-2.5">
                    {user.username}
                    {isSelf && <span className="ml-1.5 text-xs text-gold">(我)</span>}
                  </td>
                  <td className="border-b border-line px-2 py-2.5">
                    {user.is_admin ? (
                      <span className="rounded-full border border-gold/35 bg-gold/10 px-2.5 py-1 text-xs text-gold">
                        管理员
                      </span>
                    ) : (
                      <span className="text-muted">普通用户</span>
                    )}
                  </td>
                  <td className="border-b border-line px-2 py-2.5">
                    {user.is_active ? (
                      <span className="text-[#a9d2cc]">启用</span>
                    ) : (
                      <span className="text-[#f0b79c]">已停用</span>
                    )}
                  </td>
                  <td className="border-b border-line px-2 py-2.5 text-muted">
                    {user.project_count} / {user.design_count}
                  </td>
                  <td className="border-b border-line px-2 py-2.5 text-muted">
                    {new Date(user.created_at).toLocaleString("zh-CN", { hour12: false })}
                  </td>
                  <td className="border-b border-line px-2 py-2.5">
                    <div className="flex justify-end gap-2">
                      <button
                        className={btn}
                        disabled={isSelf}
                        onClick={() => toggle(user, "is_active")}
                        title={isSelf ? "不能停用自己" : ""}
                      >
                        {user.is_active ? "停用" : "启用"}
                      </button>
                      <button
                        className={btn}
                        disabled={isSelf}
                        onClick={() => toggle(user, "is_admin")}
                        title={isSelf ? "不能取消自己的管理员权限" : ""}
                      >
                        {user.is_admin ? "取消管理员" : "设为管理员"}
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
            {!loading && users.length === 0 && (
              <tr>
                <td colSpan={8} className="px-2 py-6 text-center text-muted">
                  暂无用户
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* 修改密码 */}
      <h2 className="mt-9 mb-4 font-serif text-[22px]">修改我的密码</h2>
      <div className={card} style={{ maxWidth: 460 }}>
        <form onSubmit={changePassword}>
          <div className="mb-4">
            <label className="mb-1.5 block text-[13px] text-muted">当前密码</label>
            <input
              className={inputClass}
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              placeholder="输入当前密码"
              autoComplete="current-password"
            />
          </div>
          <div className="mb-5">
            <label className="mb-1.5 block text-[13px] text-muted">新密码</label>
            <input
              className={inputClass}
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="至少 6 位"
              autoComplete="new-password"
            />
          </div>
          <button
            type="submit"
            disabled={savingPassword}
            className="rounded-[11px] bg-gradient-to-br from-gold to-[#b98a54] px-5 py-2.5 text-sm font-semibold text-[#17130c] transition hover:brightness-105 disabled:opacity-50"
          >
            {savingPassword ? "保存中…" : "修改密码"}
          </button>
        </form>
      </div>
    </div>
  );
}
