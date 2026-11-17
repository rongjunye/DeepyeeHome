import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api, auth } from "../api";
import { toast } from "../toast";
import type { TokenResponse } from "../types";

type Mode = "login" | "register";

export function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<Mode>("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const isLogin = mode === "login";

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!email || !password) {
      toast("请填写邮箱和密码", "error");
      return;
    }
    if (!isLogin && username.trim().length < 2) {
      toast("昵称至少 2 个字符", "error");
      return;
    }
    if (password.length < 6) {
      toast("密码至少 6 位", "error");
      return;
    }

    setLoading(true);
    try {
      const data = await api<TokenResponse>(isLogin ? "/auth/login" : "/auth/register", {
        method: "POST",
        auth: false,
        body: isLogin
          ? { email, password }
          : { email, username: username.trim(), password },
      });
      auth.save(data);
      toast(isLogin ? "登录成功" : "注册成功，欢迎加入！", "success");
      setTimeout(() => navigate("/studio"), 400);
    } catch (error) {
      toast(error instanceof Error ? error.message : "操作失败", "error");
      setLoading(false);
    }
  }

  const inputClass =
    "w-full rounded-[11px] border border-line bg-black/25 px-3.5 py-2.5 text-sm outline-none transition focus:border-gold/60 focus:ring-3 focus:ring-gold/12";

  return (
    <div className="grid place-items-center py-14">
      <div className="w-[min(430px,94vw)] rounded-[14px] border border-line bg-surface p-7">
        <h2 className="mb-1.5 text-center font-serif text-[22px]">
          {isLogin ? "欢迎回来" : "创建账号"}
        </h2>
        <p className="mb-6 text-center text-[13px] text-muted">
          {isLogin ? "登录后即可管理你的设计项目" : "注册后立即开始你的第一个设计"}
        </p>

        <form onSubmit={submit}>
          {!isLogin && (
            <div className="mb-4">
              <label className="mb-1.5 block text-[13px] text-muted">昵称</label>
              <input
                className={inputClass}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="给自己起个名字"
                autoComplete="nickname"
              />
            </div>
          )}

          <div className="mb-4">
            <label className="mb-1.5 block text-[13px] text-muted">邮箱</label>
            <input
              className={inputClass}
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>

          <div className="mb-5">
            <label className="mb-1.5 block text-[13px] text-muted">密码</label>
            <input
              className={inputClass}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="至少 6 位"
              autoComplete={isLogin ? "current-password" : "new-password"}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-[11px] bg-gradient-to-br from-gold to-[#b98a54] px-5 py-3 text-sm font-semibold text-[#17130c] transition hover:brightness-105 disabled:opacity-50"
          >
            {loading ? "处理中…" : isLogin ? "登录" : "注册"}
          </button>
        </form>

        <p className="mt-4.5 text-center text-[13px] text-muted">
          {isLogin ? "还没有账号？" : "已经有账号了？"}
          <button
            className="ml-1 text-gold"
            onClick={() => setMode(isLogin ? "register" : "login")}
          >
            {isLogin ? "立即注册" : "去登录"}
          </button>
        </p>
      </div>
    </div>
  );
}
