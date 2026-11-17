/** API 客户端与登录态管理。 */

import type { TokenResponse, User } from "./types";

const API_BASE = "/api";

/* ---------------- 登录态 ---------------- */
export const auth = {
  get token(): string | null {
    return localStorage.getItem("na_token");
  },
  set token(value: string | null) {
    if (value) localStorage.setItem("na_token", value);
    else localStorage.removeItem("na_token");
  },
  get user(): User | null {
    try {
      return JSON.parse(localStorage.getItem("na_user") || "null");
    } catch {
      return null;
    }
  },
  set user(value: User | null) {
    if (value) localStorage.setItem("na_user", JSON.stringify(value));
    else localStorage.removeItem("na_user");
  },
  get isLoggedIn(): boolean {
    return !!localStorage.getItem("na_token");
  },
  save(data: TokenResponse) {
    this.token = data.access_token;
    this.user = data.user;
  },
  clear() {
    this.token = null;
    this.user = null;
  },
};

/* ---------------- 请求封装 ---------------- */
interface RequestOptions {
  method?: string;
  body?: unknown;
  isForm?: boolean;
  auth?: boolean;
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export async function api<T = unknown>(
  path: string,
  options: RequestOptions = {}
): Promise<T> {
  const { method = "GET", body, isForm = false, auth: needAuth = true } = options;

  const headers: Record<string, string> = {};
  if (needAuth && auth.token) headers.Authorization = `Bearer ${auth.token}`;

  let payload: BodyInit | undefined;
  if (isForm) {
    payload = body as BodyInit;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const response = await fetch(API_BASE + path, { method, headers, body: payload });

  if (response.status === 204) return undefined as T;

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    if (response.status === 401) {
      auth.clear();
      if (!location.pathname.includes("/login")) location.href = "/login";
    }
    const detail = data && (data.detail || data.message);
    const message =
      typeof detail === "string" ? detail : `请求失败（${response.status}）`;
    throw new ApiError(message, response.status);
  }

  return data as T;
}

/* ---------------- 上传户型图的完整地址 ---------------- */
export function floorplanUrl(relativePath: string): string {
  return `/uploads/${relativePath}`;
}

export function reportUrl(designId: number): string {
  return `${API_BASE}/designs/${designId}/report`;
}

export function sharedReportUrl(token: string): string {
  return `${API_BASE}/share/${token}/report`;
}

/**
 * 下载 PDF 报告。
 *
 * 报告接口需要携带 Bearer Token，普通 <a href> 带不上请求头，
 * 因此这里先用 fetch 取回二进制，再通过 Blob URL 触发下载。
 */
export async function downloadReport(url: string, filename: string): Promise<void> {
  const headers: Record<string, string> = {};
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`;

  const response = await fetch(url, { headers });
  if (!response.ok) throw new Error(`导出失败（${response.status}）`);

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(objectUrl);
}
