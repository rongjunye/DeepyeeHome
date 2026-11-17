/* ==========================================================================
   公共脚本：API 封装、登录态管理、导航渲染、提示条、通用工具
   ========================================================================== */

const API_BASE = "/api";

/* ---------------- 登录态存储 ---------------- */
const store = {
  get token() {
    return localStorage.getItem("na_token");
  },
  set token(v) {
    v ? localStorage.setItem("na_token", v) : localStorage.removeItem("na_token");
  },
  get user() {
    try {
      return JSON.parse(localStorage.getItem("na_user") || "null");
    } catch {
      return null;
    }
  },
  set user(v) {
    v ? localStorage.setItem("na_user", JSON.stringify(v)) : localStorage.removeItem("na_user");
  },
  get isLoggedIn() {
    return !!this.token;
  },
};

/* ---------------- API 请求封装 ---------------- */
async function api(path, { method = "GET", body, isForm = false, auth = true } = {}) {
  const headers = {};
  if (auth && store.token) headers["Authorization"] = `Bearer ${store.token}`;

  let payload;
  if (isForm) {
    payload = body; // FormData，交给浏览器自动设置 Content-Type
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const res = await fetch(API_BASE + path, { method, headers, body: payload });

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    // 登录过期：清空本地态并跳转登录页
    if (res.status === 401) {
      store.token = null;
      store.user = null;
      if (!location.pathname.includes("login")) {
        location.href = "/login.html";
      }
    }
    const detail = data && (data.detail || data.message);
    throw new Error(typeof detail === "string" ? detail : `请求失败（${res.status}）`);
  }
  return data;
}

/* ---------------- 提示条 ---------------- */
function toast(message, type = "info") {
  let wrap = document.getElementById("toast-wrap");
  if (!wrap) {
    wrap = document.createElement("div");
    wrap.id = "toast-wrap";
    document.body.appendChild(wrap);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.textContent = message;
  wrap.appendChild(el);
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transition = "0.3s";
    setTimeout(() => el.remove(), 300);
  }, 3200);
}

/* ---------------- 通用工具 ---------------- */
function escapeHtml(str) {
  return String(str ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[c]);
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("zh-CN", { hour12: false });
}

function formatMoney(n) {
  return "¥" + Number(n || 0).toLocaleString("zh-CN", { maximumFractionDigits: 0 });
}

function requireAuth() {
  if (!store.isLoggedIn) {
    location.href = "/login.html";
    return false;
  }
  return true;
}

function logout() {
  store.token = null;
  store.user = null;
  location.href = "/index.html";
}

/* ---------------- 导航栏渲染 ---------------- */
function renderNav(active = "") {
  const user = store.user;
  const links = [
    { href: "/index.html", label: "首页", key: "home" },
    { href: "/studio.html", label: "工作台", key: "studio" },
  ];

  const authArea = store.isLoggedIn
    ? `<a href="/studio.html">${escapeHtml(user?.username || "我的")}</a>
       <a href="#" onclick="logout();return false;">退出</a>`
    : `<a href="/login.html">登录 / 注册</a>`;

  const html = `
    <div class="nav">
      <div class="container nav-inner">
        <a class="brand" href="/index.html">
          <span class="logo">N</span>
          <span class="name">NeuroArchAI</span>
        </a>
        <nav class="nav-links">
          ${links
            .map(
              (l) =>
                `<a href="${l.href}" class="${active === l.key ? "active" : ""}">${l.label}</a>`
            )
            .join("")}
          ${authArea}
        </nav>
      </div>
    </div>`;
  const holder = document.getElementById("nav-holder");
  if (holder) holder.innerHTML = html;
}

/* ---------------- 下载 PDF 报告 ---------------- */
async function downloadReport(url, filename) {
  const headers = {};
  if (store.token) headers["Authorization"] = "Bearer " + store.token;

  const res = await fetch(url, { headers });
  if (!res.ok) throw new Error("导出失败（" + res.status + "）");

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

/* ---------------- Plotly 图表渲染 ---------------- */
function renderCharts(chartSpec) {
  const containers = document.querySelectorAll("[data-chart]");
  if (typeof Plotly === "undefined") {
    containers.forEach((el) => (el.innerHTML = '<p class="muted small">图表组件加载失败</p>'));
    return;
  }
  containers.forEach((el) => {
    const key = el.getAttribute("data-chart");
    const spec = chartSpec && chartSpec[key];
    if (!spec) {
      el.innerHTML = '<p class="muted small">暂无数据</p>';
      return;
    }
    Plotly.newPlot(el, spec.data || [], spec.layout || {}, {
      displayModeBar: false,
      responsive: true,
    });
  });
}
