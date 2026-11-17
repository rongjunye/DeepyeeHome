import { Link } from "react-router-dom";

const FEATURES = [
  { tag: "01", title: "账号体系", desc: "注册 / 登录，多个项目独立管理，数据只属于你自己。" },
  { tag: "02", title: "户型图上传", desc: "支持 PNG / JPG / WEBP，自动校验格式与体积。" },
  { tag: "03", title: "AI 方案生成", desc: "多智能体 / 大模型 / 算法引擎三档可选，稳健可用。" },
  { tag: "04", title: "3D 预览", desc: "把布局实时挤压成三维户型，拖拽旋转查看空间关系。" },
  { tag: "05", title: "PDF 报告", desc: "一键导出含预算、材料与配色的完整报告。" },
  { tag: "06", title: "保存与分享", desc: "方案永久保存，生成链接即可公开分享。" },
];

const STEPS = [
  { title: "① 新建项目", desc: "填写项目名称、面积与房间构成，上传户型图。" },
  { title: "② 选择风格", desc: "现代简约 / 北欧 / 新中式 / 侘寂 / 工业风 / 轻奢 / 奶油风。" },
  { title: "③ 生成方案", desc: "查看布局建议、配色、材料清单、预算图表与 3D 户型。" },
];

export function Home() {
  return (
    <div className="mx-auto w-[92%] max-w-[1160px]">
      {/* Hero */}
      <header className="py-16 md:py-20">
        <span className="inline-block rounded-full border border-gold/35 bg-gold/10 px-3 py-1 text-xs text-gold">
          AI × 室内设计 × 造价 × 3D 可视化
        </span>
        <h1 className="mt-4 font-serif text-3xl leading-tight md:text-5xl">
          上传一张户型图，
          <br />
          让 AI 帮你把家「设计」出来
        </h1>
        <p className="mt-4 max-w-[620px] text-[17px] text-muted">
          NeuroArchAI 会分析你的户型条件，输出空间布局与动线建议、风格落地要点、
          配色方案、材料清单与预算估算，并实时生成可交互的 3D 户型预览。
        </p>
        <div className="mt-7 flex flex-wrap gap-3">
          <Link
            to="/studio"
            className="rounded-[11px] bg-gradient-to-br from-gold to-[#b98a54] px-5 py-3 text-sm font-semibold text-[#17130c] transition hover:brightness-105"
          >
            开始设计 →
          </Link>
          <Link
            to="/login"
            className="rounded-[11px] border border-line bg-white/5 px-5 py-3 text-sm transition hover:bg-white/10"
          >
            登录 / 注册
          </Link>
        </div>
        <p className="mt-3.5 text-[13px] text-muted">
          零配置即可体验：未配置大模型时自动使用内置算法引擎。
        </p>
      </header>

      {/* 核心能力 */}
      <section className="py-8">
        <h2 className="mb-4 font-serif text-[22px]">核心能力</h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((item) => (
            <div key={item.tag} className="rounded-[14px] border border-line bg-surface p-5">
              <span className="inline-block rounded-full border border-line bg-white/5 px-2.5 py-1 text-xs text-muted">
                {item.tag}
              </span>
              <h3 className="mt-3 mb-1.5 text-base font-semibold">{item.title}</h3>
              <p className="text-[13px] text-muted">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 三步流程 */}
      <section className="py-8 pb-16">
        <h2 className="mb-4 font-serif text-[22px]">只需三步</h2>
        <div className="grid gap-4 md:grid-cols-3">
          {STEPS.map((step) => (
            <div key={step.title} className="rounded-[14px] border border-line bg-surface p-5">
              <h3 className="mb-1.5 font-semibold">{step.title}</h3>
              <p className="text-[13px] text-muted">{step.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
