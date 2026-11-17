/**
 * 免构建版 3D 户型预览（Three.js · ES Module）
 *
 * 通过 importmap 从 CDN 加载 three，对外导出 renderRoom3D(container, layout)。
 * 后端 layout3d 数据结构见 app/ai/layout3d.py。
 */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const FLOOR_THICKNESS = 0.06;
const WALL_THICKNESS = 0.1;

/* ---------------- 建模辅助 ---------------- */

function addWall(scene, material, width, depth, x, z, height) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
  mesh.position.set(x, height / 2, z);
  scene.add(mesh);
}

function addBox(scene, width, height, depth, x, z, material) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
  mesh.position.set(x, FLOOR_THICKNESS + height / 2, z);
  scene.add(mesh);
}

/** 房间名悬浮标签：Canvas 贴图 + Sprite */
function makeLabel(text, x, y, z) {
  const canvas = document.createElement("canvas");
  const w = 256;
  const h = 128;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d");

  ctx.fillStyle = "rgba(15,17,21,0.84)";
  const radius = 16;
  const bx = 6;
  const by = 36;
  const bw = w - 12;
  const bh = 56;
  ctx.beginPath();
  ctx.moveTo(bx + radius, by);
  ctx.lineTo(bx + bw - radius, by);
  ctx.quadraticCurveTo(bx + bw, by, bx + bw, by + radius);
  ctx.lineTo(bx + bw, by + bh - radius);
  ctx.quadraticCurveTo(bx + bw, by + bh, bx + bw - radius, by + bh);
  ctx.lineTo(bx + radius, by + bh);
  ctx.quadraticCurveTo(bx, by + bh, bx, by + bh - radius);
  ctx.lineTo(bx, by + radius);
  ctx.quadraticCurveTo(bx, by, bx + radius, by);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#e8e6e1";
  ctx.font = "600 40px 'Noto Serif SC', 'Microsoft YaHei', sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(text, w / 2, by + bh / 2 + 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(
    new THREE.SpriteMaterial({ map: texture, transparent: true, depthTest: false })
  );
  sprite.position.set(x, y, z);
  sprite.scale.set(2.3, 1.15, 1);
  return sprite;
}

/** 按房间类型摆放简易家具 */
function addFurniture(scene, room) {
  const fabric = new THREE.MeshStandardMaterial({ color: 0x6e6a63, roughness: 0.85 });
  const wood = new THREE.MeshStandardMaterial({ color: 0x9b7b52, roughness: 0.72 });
  const stone = new THREE.MeshStandardMaterial({ color: 0x8f9296, roughness: 0.6 });

  const cx = room.x + room.w / 2;
  const cz = room.z + room.d / 2;
  const fitW = (size) => Math.min(size, room.w * 0.7);
  const fitD = (size) => Math.min(size, room.d * 0.7);

  switch (room.type) {
    case "living":
      addBox(scene, fitW(2.1), 0.72, fitD(0.85), cx, cz + room.d * 0.22, fabric);
      addBox(scene, fitW(1.0), 0.4, fitD(0.55), cx, cz - room.d * 0.2, wood);
      break;
    case "master":
    case "bedroom":
      addBox(scene, fitW(1.7), 0.48, fitD(1.95), cx, cz, fabric);
      break;
    case "dining":
      addBox(scene, fitW(1.35), 0.74, fitD(0.85), cx, cz, wood);
      break;
    case "kitchen":
      addBox(scene, fitW(room.w * 0.8), 0.86, 0.58, cx, room.z + 0.4, stone);
      break;
    case "bath":
      addBox(scene, fitW(0.65), 0.5, fitD(0.5), cx, cz, stone);
      break;
    case "entry":
      addBox(scene, fitW(room.w * 0.78), 1.15, 0.38, cx, room.z + 0.3, wood);
      break;
    default:
      break;
  }
}

/* ---------------- 对外入口 ---------------- */

/**
 * 在指定容器内渲染 3D 户型。
 *
 * @param {HTMLElement} container 挂载容器
 * @param {object} layout 后端 layout3d 数据
 * @param {object} [options] { height }
 * @returns {Function|null} 清理函数（重复渲染时会自动调用上一次的清理）
 */
export function renderRoom3D(container, layout, options = {}) {
  if (!container || !layout || !layout.rooms || !layout.rooms.length) return null;

  const height = options.height || 460;
  container.style.height = height + "px";
  container.style.position = "relative";

  // 清理上一次的场景，避免重复渲染叠加
  if (typeof container._dispose3d === "function") {
    container._dispose3d();
    container._dispose3d = null;
  }
  container.innerHTML = "";

  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true });
  } catch (error) {
    container.innerHTML =
      '<div style="display:grid;place-items:center;height:100%;color:#9aa0a6;font-size:14px">当前浏览器不支持 WebGL，无法显示 3D 预览</div>';
    return null;
  }

  const width = container.clientWidth || 720;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x11141a);

  const cx = layout.width / 2;
  const cz = layout.depth / 2;
  const span = Math.max(layout.width, layout.depth);

  const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
  camera.position.set(cx + span * 0.9, span * 1.0, cz + span * 1.25);
  camera.lookAt(cx, 0.5, cz);

  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width, height);
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(cx, 0.5, cz);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.maxPolarAngle = Math.PI / 2.05;
  controls.minDistance = span * 0.35;
  controls.maxDistance = span * 3.2;
  controls.update();

  // 灯光
  scene.add(new THREE.AmbientLight(0xffffff, 0.75));
  const key = new THREE.DirectionalLight(0xffffff, 0.85);
  key.position.set(cx + span, span * 1.6, cz + span * 0.8);
  scene.add(key);
  const warm = new THREE.DirectionalLight(0xc89f6d, 0.3);
  warm.position.set(cx - span, span * 0.9, cz - span);
  scene.add(warm);

  const wallHeight = layout.wall_height || 2.8;

  // 地基
  const base = new THREE.Mesh(
    new THREE.BoxGeometry(layout.width + 0.5, 0.22, layout.depth + 0.5),
    new THREE.MeshStandardMaterial({ color: 0x1b1f24, roughness: 0.95 })
  );
  base.position.set(cx, -0.12, cz);
  scene.add(base);

  const wallMaterial = new THREE.MeshStandardMaterial({
    color: 0xe9e4dc,
    roughness: 0.92,
    metalness: 0.02,
  });

  for (const room of layout.rooms) {
    // 地板
    const floor = new THREE.Mesh(
      new THREE.BoxGeometry(room.w, FLOOR_THICKNESS, room.d),
      new THREE.MeshStandardMaterial({
        color: new THREE.Color(room.color || "#cccccc"),
        roughness: 0.82,
      })
    );
    floor.position.set(room.x + room.w / 2, FLOOR_THICKNESS / 2, room.z + room.d / 2);
    scene.add(floor);

    // 四面墙
    addWall(scene, wallMaterial, room.w, WALL_THICKNESS, room.x + room.w / 2, room.z, wallHeight);
    addWall(
      scene,
      wallMaterial,
      room.w,
      WALL_THICKNESS,
      room.x + room.w / 2,
      room.z + room.d,
      wallHeight
    );
    addWall(scene, wallMaterial, WALL_THICKNESS, room.d, room.x, room.z + room.d / 2, wallHeight);
    addWall(
      scene,
      wallMaterial,
      WALL_THICKNESS,
      room.d,
      room.x + room.w,
      room.z + room.d / 2,
      wallHeight
    );

    addFurniture(scene, room);
    scene.add(makeLabel(room.name, room.x + room.w / 2, wallHeight + 0.3, room.z + room.d / 2));
  }

  let frameId = 0;
  const renderLoop = () => {
    controls.update();
    renderer.render(scene, camera);
    frameId = requestAnimationFrame(renderLoop);
  };
  renderLoop();

  const resizeObserver = new ResizeObserver(() => {
    const nextWidth = container.clientWidth || width;
    camera.aspect = nextWidth / height;
    camera.updateProjectionMatrix();
    renderer.setSize(nextWidth, height);
  });
  resizeObserver.observe(container);

  // 清理函数
  const dispose = () => {
    cancelAnimationFrame(frameId);
    resizeObserver.disconnect();
    controls.dispose();
    scene.traverse((object) => {
      if (object instanceof THREE.Mesh) {
        object.geometry.dispose();
        const material = object.material;
        if (Array.isArray(material)) material.forEach((item) => item.dispose());
        else material.dispose();
      }
      if (object instanceof THREE.Sprite) {
        if (object.material.map) object.material.map.dispose();
        object.material.dispose();
      }
    });
    renderer.dispose();
    if (renderer.domElement.parentNode === container) {
      container.removeChild(renderer.domElement);
    }
  };

  container._dispose3d = dispose;
  return dispose;
}