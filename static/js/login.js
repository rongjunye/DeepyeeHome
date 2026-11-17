/* ==========================================================================
   登录 / 注册页逻辑
   ========================================================================== */

renderNav("");

let mode = "login"; // login | register

const titleEl = document.getElementById("form-title");
const subEl = document.getElementById("form-sub");
const usernameField = document.getElementById("username-field");
const submitBtn = document.getElementById("submit-btn");
const switchHint = document.getElementById("switch-hint");
const switchBtn = document.getElementById("switch-btn");

function applyMode() {
  const isLogin = mode === "login";
  titleEl.textContent = isLogin ? "欢迎回来" : "创建账号";
  subEl.textContent = isLogin ? "登录后即可管理你的设计项目" : "注册后立即开始你的第一个设计";
  usernameField.style.display = isLogin ? "none" : "block";
  submitBtn.textContent = isLogin ? "登录" : "注册";
  switchHint.textContent = isLogin ? "还没有账号？" : "已经有账号了？";
  switchBtn.textContent = isLogin ? "立即注册" : "去登录";
}

switchBtn.addEventListener("click", (e) => {
  e.preventDefault();
  mode = mode === "login" ? "register" : "login";
  applyMode();
});

document.getElementById("auth-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const username = document.getElementById("username").value.trim();

  if (!email || !password) {
    toast("请填写邮箱和密码", "error");
    return;
  }
  if (mode === "register" && username.length < 2) {
    toast("昵称至少 2 个字符", "error");
    return;
  }
  if (password.length < 6) {
    toast("密码至少 6 位", "error");
    return;
  }

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span> 处理中…';

  try {
    const path = mode === "login" ? "/auth/login" : "/auth/register";
    const body =
      mode === "login" ? { email, password } : { email, username, password };
    const data = await api(path, { method: "POST", body, auth: false });

    store.token = data.access_token;
    store.user = data.user;
    toast(mode === "login" ? "登录成功" : "注册成功，欢迎加入！", "success");
    setTimeout(() => (location.href = "/studio.html"), 500);
  } catch (err) {
    toast(err.message, "error");
    submitBtn.disabled = false;
    submitBtn.textContent = mode === "login" ? "登录" : "注册";
  }
});

applyMode();
