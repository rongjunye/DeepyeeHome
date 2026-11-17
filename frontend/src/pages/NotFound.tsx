import { Link } from "react-router-dom";

export function NotFound() {
  return (
    <div className="mx-auto grid w-[92%] max-w-[1160px] place-items-center py-24 text-center">
      <h1 className="font-serif text-5xl">404</h1>
      <p className="mt-3 text-muted">找不到这个页面</p>
      <Link
        to="/"
        className="mt-6 rounded-[11px] border border-line bg-white/5 px-5 py-3 text-sm transition hover:bg-white/10"
      >
        返回首页
      </Link>
    </div>
  );
}
