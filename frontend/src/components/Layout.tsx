import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { auth } from "../api";
import { Toaster } from "./Toaster";

/** 全站布局：顶部导航 + 内容出口 + 全局提示条。 */
export function Layout() {
  const location = useLocation();
  const navigate = useNavigate();
  // Layout 会随路由变化重渲染，因此这里直接读取登录态即可保持最新
  const loggedIn = auth.isLoggedIn;
  const user = auth.user;

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `px-3.5 py-2 rounded-[10px] text-sm transition ${
      isActive ? "text-[#e8e6e1] bg-gold/15" : "text-muted hover:text-[#e8e6e1] hover:bg-white/5"
    }`;

  return (
    <div className="min-h-screen flex flex-col">
      <header className="sticky top-0 z-40 border-b border-line bg-ink/70 backdrop-blur-md">
        <div className="mx-auto flex h-[62px] w-[92%] max-w-[1160px] items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5 font-semibold tracking-wide">
            <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-gold to-teal text-[15px] font-extrabold text-ink">
              N
            </span>
            <span className="hidden sm:inline">NeuroArchAI</span>
          </Link>

          <nav className="flex items-center gap-1.5">
            <NavLink to="/" className={linkClass} end>
              首页
            </NavLink>
            <NavLink to="/studio" className={linkClass}>
              工作台
            </NavLink>
            {loggedIn ? (
              <>
                <span className="px-3.5 py-2 text-sm text-gold">{user?.username ?? "我的"}</span>
                <button
                  className="px-3.5 py-2 text-sm text-muted transition hover:text-[#e8e6e1]"
                  onClick={() => {
                    auth.clear();
                    navigate("/");
                  }}
                >
                  退出
                </button>
              </>
            ) : (
              <NavLink to="/login" className={linkClass}>
                登录 / 注册
              </NavLink>
            )}
          </nav>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-line py-7 text-center text-[13px] text-muted">
        NeuroArchAI Platform · AI 驱动的户型装修设计助手
      </footer>

      <Toaster />
    </div>
  );
}
