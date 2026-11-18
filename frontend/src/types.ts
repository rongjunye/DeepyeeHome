/** 与后端 Pydantic 模型对应的 TypeScript 类型定义。 */

export interface User {
  id: number;
  email: string;
  username: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
}

/** 管理后台：用户条目（含数据统计） */
export interface AdminUser {
  id: number;
  email: string;
  username: string;
  is_admin: boolean;
  is_active: boolean;
  created_at: string;
  project_count: number;
  design_count: number;
}

/** 管理后台：全局统计 */
export interface AdminStats {
  total_users: number;
  active_users: number;
  admin_users: number;
  total_projects: number;
  total_designs: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Project {
  id: number;
  title: string;
  description: string;
  floorplan_path: string | null;
  meta_info: Record<string, unknown>;
  created_at: string;
  design_count: number;
  /** 是否已保存真实户型标注 */
  has_layout: boolean;
}

/** 标注中的一个房间（坐标为相对户型图的归一化值 0~1） */
export interface LayoutRoom {
  name: string;
  type: string;
  x: number;
  y: number;
  w: number;
  h: number;
  color?: string | null;
}

/** 项目保存的真实户型布局 */
export interface ProjectLayout {
  rooms: LayoutRoom[];
  total_width_m: number;
  image_aspect: number;
  source: string;
}

/** 房间类型可选项 */
export const ROOM_TYPES = [
  { value: "living", label: "客厅" },
  { value: "dining", label: "餐厅" },
  { value: "kitchen", label: "厨房" },
  { value: "master", label: "主卧" },
  { value: "bedroom", label: "次卧" },
  { value: "bath", label: "卫生间" },
  { value: "balcony", label: "阳台" },
  { value: "entry", label: "玄关" },
  { value: "other", label: "其他" },
];

export interface ColorSwatch {
  name: string;
  hex: string;
}

export interface MaterialItem {
  category: string;
  name: string;
  specification: string;
  estimated_cost: number;
}

export interface BudgetCategory {
  category: string;
  amount: number;
  ratio: number;
}

export interface Budget {
  currency: string;
  level: string;
  level_label: string;
  area: number;
  per_sqm: number;
  total: number;
  by_category: BudgetCategory[];
  note: string;
}

export interface Room3D {
  name: string;
  type: string;
  x: number;
  z: number;
  w: number;
  d: number;
  area: number;
  color: string;
}

export interface Layout3D {
  width: number;
  depth: number;
  wall_height: number;
  area: number;
  rooms: Room3D[];
}

/** Plotly 图表规格（后端已生成 data / layout） */
export interface FigureSpec {
  data: unknown[];
  layout: Record<string, unknown>;
}

export type ChartSpec = Record<string, FigureSpec>;

export interface Design {
  id: number;
  project_id: number;
  style: string;
  provider: string;
  summary: string;
  layout_plan: string;
  style_recommendation: string;
  color_palette: ColorSwatch[];
  materials: MaterialItem[];
  budget: Budget;
  chart_spec: ChartSpec;
  layout3d: Layout3D;
  share_token: string;
  is_public: boolean;
  created_at: string;
}

export interface DesignListItem {
  id: number;
  project_id: number;
  style: string;
  provider: string;
  summary: string;
  is_public: boolean;
  share_token: string;
  created_at: string;
}

export interface DesignGeneratePayload {
  style: string;
  rooms?: string;
  area?: number;
  budget_level: string;
  requirements?: string;
}

export const STYLE_OPTIONS = [
  "现代简约",
  "北欧",
  "新中式",
  "日式侘寂",
  "工业风",
  "轻奢",
  "奶油风",
];

export const BUDGET_LEVELS = [
  { value: "economy", label: "经济型" },
  { value: "standard", label: "标准型" },
  { value: "premium", label: "品质型" },
];
