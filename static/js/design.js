/* ==========================================================================
   方案详情页逻辑
   ========================================================================== */

renderNav("");
if (!requireAuth()) throw new Error("未登录");

const contentEl = document.getElementById("content");
let design = null;

function param(name) {
  return new URLSearchParams(location.search).get(name);
}

async function loadDesign() {
  const id = param("id");
  if (!id) {
    contentEl.innerHTML = '<div class="empty">缺少方案 ID</div>';
    return;
  }
  try {
    design = await api(`/designs/${id}`);
    render();
  } catch (err) {
    contentEl.innerHTML = `<div class="empty">加载失败：${escapeHtml(err.message)}</div>`;
  }
}

function render() {
  const b = design.budget || {};
  const palette = design.color_palette || [];
  const materials = design.materials || [];

  contentEl.innerHTML = `
    <div class="row between wrap" style="margin-bottom: 6px">
      <div>
        <span class="tag tag-accent">${escapeHtml(design.style)}风格</span>
        <span class="tag" style="margin-left:6px">引擎：${escapeHtml(design.provider)}</span>
      </div>
      <div class="row">
        <button class="btn btn-sm" onclick="downloadDesignReport()">下载 PDF 报告</button>
        <a class="btn btn-sm btn-ghost" href="/studio.html">← 返回工作台</a>
      </div>
    </div>
    <h1 class="section-title" style="margin-top: 12px">设计方案 #${design.id}</h1>
    <p class="muted small">生成于 ${formatDate(design.created_at)}</p>

    <div class="card" style="margin-top: 20px">
      <h2 style="margin:0 0 10px;font-size:17px">方案总述</h2>
      <p style="margin:0">${escapeHtml(design.summary)}</p>
    </div>

    <div class="grid grid-2" style="margin-top:18px">
      <div class="card">
        <h2 style="margin:0 0 10px;font-size:17px">空间布局与动线</h2>
        <p style="margin:0;white-space:pre-wrap">${escapeHtml(design.layout_plan)}</p>
      </div>
      <div class="card">
        <h2 style="margin:0 0 10px;font-size:17px">风格落地要点</h2>
        <p style="margin:0;white-space:pre-wrap">${escapeHtml(design.style_recommendation)}</p>
      </div>
    </div>

    <h2 class="section-title" style="margin-top:30px">3D 户型预览</h2>
    <div class="card">
      <div id="scene3d" class="scene3d" style="border-radius:10px;background:#11141a"></div>
      <p class="muted small" style="margin-top:10px">
        依据布局数据实时生成的三维户型（非真实渲染效果图），用于直观感受空间关系与分区。
      </p>
    </div>

    <h2 class="section-title" style="margin-top:30px">配色方案</h2>
    <div class="grid grid-4">
      ${palette
        .map(
          (c) => `
        <div class="swatch">
          <span class="chip" style="background:${escapeHtml(c.hex)}"></span>
          <div>
            <div style="font-size:14px">${escapeHtml(c.name)}</div>
            <div class="muted small">${escapeHtml(c.hex)}</div>
          </div>
        </div>`
        )
        .join("")}
    </div>

    <h2 class="section-title" style="margin-top:30px">预算估算</h2>
    <div class="grid grid-2">
      <div class="card">
        <div class="row between">
          <span class="muted">建筑面积</span><strong>${b.area || "-"} ㎡</strong>
        </div>
        <hr class="divider" />
        <div class="row between">
          <span class="muted">单价（综合）</span><strong>${b.per_sqm ? formatMoney(b.per_sqm) + " / ㎡" : "-"}</strong>
        </div>
        <hr class="divider" />
        <div class="row between">
          <span class="muted">档位</span><strong>${escapeHtml(b.level_label || "-")}</strong>
        </div>
        <hr class="divider" />
        <div class="row between">
          <span class="muted">预估总价</span>
          <strong style="color:var(--gold);font-size:22px">${formatMoney(b.total)}</strong>
        </div>
        <p class="muted small" style="margin-top:14px">${escapeHtml(b.note || "")}</p>
      </div>
      <div class="card">
        <div data-chart="budget_pie" class="chart"></div>
      </div>
    </div>

    <div class="grid grid-2" style="margin-top:18px">
      <div class="card">
        <div data-chart="material_bar" class="chart"></div>
      </div>
      <div class="card">
        <div data-chart="style_radar" class="chart"></div>
      </div>
    </div>

    <h2 class="section-title" style="margin-top:30px">材料清单</h2>
    <div class="card" style="overflow-x:auto">
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <thead>
          <tr class="muted" style="text-align:left">
            <th style="padding:10px 8px;border-bottom:1px solid var(--border)">类别</th>
            <th style="padding:10px 8px;border-bottom:1px solid var(--border)">材料 / 工艺</th>
            <th style="padding:10px 8px;border-bottom:1px solid var(--border)">规格</th>
            <th style="padding:10px 8px;border-bottom:1px solid var(--border);text-align:right">预估费用</th>
          </tr>
        </thead>
        <tbody>
          ${materials
            .map(
              (m) => `
            <tr>
              <td style="padding:10px 8px;border-bottom:1px solid var(--border)">${escapeHtml(m.category)}</td>
              <td style="padding:10px 8px;border-bottom:1px solid var(--border)">${escapeHtml(m.name)}</td>
              <td style="padding:10px 8px;border-bottom:1px solid var(--border)" class="muted">${escapeHtml(m.specification)}</td>
              <td style="padding:10px 8px;border-bottom:1px solid var(--border);text-align:right">${formatMoney(m.estimated_cost)}</td>
            </tr>`
            )
            .join("")}
        </tbody>
      </table>
    </div>

    <h2 class="section-title" style="margin-top:30px">分享</h2>
    <div class="card">
      <div class="row between wrap">
        <div>
          <div id="share-status">${design.is_public ? "🔓 当前为公开状态，任何人都可通过链接查看" : "🔒 当前为私密状态"}</div>
          <div class="muted small" id="share-link" style="margin-top:6px"></div>
        </div>
        <div class="row">
          <button class="btn" id="toggle-share">${design.is_public ? "设为私密" : "开启分享"}</button>
          <button class="btn btn-primary" id="copy-share" ${design.is_public ? "" : "disabled"}>复制链接</button>
        </div>
      </div>
    </div>
  `;

  renderCharts(design.chart_spec);
  bindShare();
  mount3D(design.layout3d);
}

/**
 * 懒加载 3D 组件并渲染户型。
 * room3d.js 是 ES Module，通过 importmap 从 CDN 取 three。
 */
async function mount3D(layout) {
  const container = document.getElementById("scene3d");
  if (!container || !layout || !layout.rooms || !layout.rooms.length) return;
  container.innerHTML = '<p class="muted small" style="padding:16px">3D 场景加载中…</p>';
  try {
    const module = await import("/js/room3d.js");
    module.renderRoom3D(container, layout, { height: 480 });
  } catch (error) {
    container.innerHTML =
      '<p class="muted small" style="padding:16px">3D 组件加载失败（可能是离线环境），不影响其他内容查看。</p>';
  }
}

function shareUrl() {
  return `${location.origin}/share.html?token=${design.share_token}`;
}

async function downloadDesignReport() {
  try {
    await downloadReport(`/api/designs/${design.id}/report`, `NeuroArchAI-design-${design.id}.pdf`);
    toast("报告已开始下载", "success");
  } catch (err) {
    toast(err.message, "error");
  }
}

function bindShare() {
  const linkEl = document.getElementById("share-link");
  if (design.is_public) linkEl.textContent = shareUrl();

  document.getElementById("toggle-share").addEventListener("click", async () => {
    try {
      design = await api(`/designs/${design.id}/share`, {
        method: "PATCH",
        body: { is_public: !design.is_public },
      });
      toast(design.is_public ? "已开启分享" : "已关闭分享", "success");
      render();
    } catch (err) {
      toast(err.message, "error");
    }
  });

  document.getElementById("copy-share").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(shareUrl());
      toast("链接已复制", "success");
    } catch {
      toast("复制失败，请手动复制", "error");
    }
  });
}

loadDesign();
