/* ==========================================================================
   工作台逻辑：项目管理 + 户型图上传 + 生成方案
   ========================================================================== */

renderNav("studio");
if (!requireAuth()) throw new Error("未登录");

let currentProject = null;

const projectListEl = document.getElementById("project-list");
const detailPanel = document.getElementById("detail-panel");

/* ---------------- 项目列表 ---------------- */
async function loadProjects() {
  projectListEl.innerHTML = '<div class="empty">加载中…</div>';
  try {
    const projects = await api("/projects");
    if (!projects.length) {
      projectListEl.innerHTML = '<div class="empty">还没有项目，先在上方新建一个吧</div>';
      return;
    }
    projectListEl.innerHTML = projects
      .map(
        (p) => `
      <div class="card" style="cursor:pointer" onclick="openDetail(${p.id})">
        <div class="row between">
          <h3 style="margin:0;font-size:16px">${escapeHtml(p.title)}</h3>
          <span class="tag">${p.design_count} 套方案</span>
        </div>
        <p class="muted small" style="margin:10px 0 6px">${escapeHtml(p.description) || "暂无备注"}</p>
        <p class="muted small" style="margin:0">
          ${p.meta_info?.area ? escapeHtml(p.meta_info.area) + "㎡ · " : ""}
          ${escapeHtml(p.meta_info?.rooms || "")}
        </p>
        <p class="muted small" style="margin:8px 0 0">
          ${p.floorplan_path ? "✅ 已上传户型图" : "⚠️ 未上传户型图"}
        </p>
      </div>`
      )
      .join("");
  } catch (err) {
    projectListEl.innerHTML = `<div class="empty">加载失败：${escapeHtml(err.message)}</div>`;
  }
}

/* ---------------- 新建项目 ---------------- */
document.getElementById("project-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const btn = document.getElementById("create-btn");
  const title = document.getElementById("p-title").value.trim();
  const area = parseFloat(document.getElementById("p-area").value);
  const rooms = document.getElementById("p-rooms").value.trim();
  const description = document.getElementById("p-desc").value.trim();

  if (!title) {
    toast("请填写项目名称", "error");
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> 创建中…';
  try {
    const meta_info = {};
    if (area) meta_info.area = area;
    if (rooms) meta_info.rooms = rooms;

    const project = await api("/projects", {
      method: "POST",
      body: { title, description, meta_info },
    });
    toast("项目创建成功", "success");
    document.getElementById("project-form").reset();
    await loadProjects();
    openDetail(project.id);
  } catch (err) {
    toast(err.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = "创建项目";
  }
});

/* ---------------- 打开项目详情 ---------------- */
async function openDetail(projectId) {
  try {
    currentProject = await api(`/projects/${projectId}`);
  } catch (err) {
    toast(err.message, "error");
    return;
  }
  detailPanel.style.display = "block";

  const meta = currentProject.meta_info || {};
  document.getElementById("detail-title").textContent = currentProject.title;
  document.getElementById("d-area").value = meta.area || "";

  renderFloorplan();
  await loadDesigns(projectId);
  detailPanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

function closeDetail() {
  detailPanel.style.display = "none";
  currentProject = null;
}

function renderFloorplan() {
  const box = document.getElementById("floorplan-preview");
  if (currentProject.floorplan_path) {
    box.innerHTML = `<img src="/uploads/${currentProject.floorplan_path}" alt="户型图" />`;
  } else {
    box.innerHTML = "";
  }
}

/* ---------------- 上传户型图 ---------------- */
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});

async function uploadFile(file) {
  if (!currentProject) return;
  const form = new FormData();
  form.append("file", file);
  toast("正在上传户型图…");
  try {
    currentProject = await api(`/projects/${currentProject.id}/floorplan`, {
      method: "POST",
      body: form,
      isForm: true,
    });
    renderFloorplan();
    toast("户型图上传成功", "success");
    loadProjects();
  } catch (err) {
    toast(err.message, "error");
  }
}

/* ---------------- 生成方案 ---------------- */
document.getElementById("design-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!currentProject) return;

  const btn = document.getElementById("gen-btn");
  const style = document.getElementById("d-style").value;
  const areaVal = parseFloat(document.getElementById("d-area").value);
  const budget_level = document.getElementById("d-level").value;
  const requirements = document.getElementById("d-req").value.trim();

  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> AI 生成中，请稍候…';

  try {
    const body = { style, budget_level, requirements };
    if (areaVal) body.area = areaVal;

    const design = await api(`/projects/${currentProject.id}/designs`, {
      method: "POST",
      body,
    });
    toast("方案生成成功", "success");
    location.href = `/design.html?id=${design.id}`;
  } catch (err) {
    toast(err.message, "error");
    btn.disabled = false;
    btn.textContent = "生成方案 ✨";
  }
});

/* ---------------- 方案列表 ---------------- */
async function loadDesigns(projectId) {
  const listEl = document.getElementById("design-list");
  listEl.innerHTML = '<div class="empty">加载中…</div>';
  try {
    const designs = await api(`/projects/${projectId}/designs`);
    if (!designs.length) {
      listEl.innerHTML = '<div class="empty">还没有方案，选择一个风格生成吧</div>';
      return;
    }
    listEl.innerHTML = designs
      .map(
        (d) => `
      <div class="card" style="cursor:pointer" onclick="location.href='/design.html?id=${d.id}'">
        <div class="row between">
          <h4 style="margin:0;font-size:15px">${escapeHtml(d.style)}</h4>
          <span class="tag ${d.is_public ? "tag-accent" : ""}">${d.is_public ? "已分享" : "私密"}</span>
        </div>
        <p class="muted small" style="margin:10px 0">${escapeHtml(d.summary).slice(0, 70)}…</p>
        <p class="muted small" style="margin:0">${formatDate(d.created_at)}</p>
      </div>`
      )
      .join("");
  } catch (err) {
    listEl.innerHTML = `<div class="empty">加载失败：${escapeHtml(err.message)}</div>`;
  }
}

/* ---------------- 初始化 ---------------- */
loadProjects();
