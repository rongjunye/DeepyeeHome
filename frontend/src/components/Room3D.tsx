import { useEffect, useRef } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import type { Layout3D, Room3D as Room } from "../types";

/**
 * 交互式 3D 户型预览。
 *
 * 把后端生成的 layout3d 数据（矩形房间列表）挤压成三维户型：
 * 每个房间铺一块彩色地板、砌四面墙，并按房间类型摆放简易家具，
 * 房间名用 Canvas 贴图做悬浮标签。支持拖拽旋转 / 滚轮缩放。
 */

const FLOOR_THICKNESS = 0.06;
const WALL_THICKNESS = 0.1;

/* ---------------- 建模辅助函数 ---------------- */

function addWall(
  scene: THREE.Scene,
  material: THREE.Material,
  width: number,
  depth: number,
  x: number,
  z: number,
  height: number
) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
  mesh.position.set(x, height / 2, z);
  scene.add(mesh);
}

function addBox(
  scene: THREE.Scene,
  width: number,
  height: number,
  depth: number,
  x: number,
  z: number,
  material: THREE.Material
) {
  const mesh = new THREE.Mesh(new THREE.BoxGeometry(width, height, depth), material);
  mesh.position.set(x, FLOOR_THICKNESS + height / 2, z);
  scene.add(mesh);
}

/** 生成房间名悬浮标签（Canvas 贴图 + Sprite） */
function makeLabel(text: string, x: number, y: number, z: number): THREE.Sprite {
  const canvas = document.createElement("canvas");
  const w = 256;
  const h = 128;
  canvas.width = w;
  canvas.height = h;
  const ctx = canvas.getContext("2d")!;

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

/** 按房间类型摆放简易家具，营造空间感 */
function addFurniture(scene: THREE.Scene, room: Room) {
  const fabric = new THREE.MeshStandardMaterial({ color: 0x6e6a63, roughness: 0.85 });
  const wood = new THREE.MeshStandardMaterial({ color: 0x9b7b52, roughness: 0.72 });
  const stone = new THREE.MeshStandardMaterial({ color: 0x8f9296, roughness: 0.6 });

  const cx = room.x + room.w / 2;
  const cz = room.z + room.d / 2;
  const fitW = (size: number) => Math.min(size, room.w * 0.7);
  const fitD = (size: number) => Math.min(size, room.d * 0.7);

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

/* ---------------- 组件 ---------------- */

export function Room3D({ layout, height = 460 }: { layout?: Layout3D; height?: number }) {
  const mountRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount || !layout || !layout.rooms?.length) return;

    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true });
    } catch {
      return; // 环境不支持 WebGL 时静默退出，由外层给出文字提示
    }

    const width = mount.clientWidth || 720;
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
    mount.appendChild(renderer.domElement);

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
      // 地板（按配色着色）
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
      const nextWidth = mount.clientWidth || width;
      camera.aspect = nextWidth / height;
      camera.updateProjectionMatrix();
      renderer.setSize(nextWidth, height);
    });
    resizeObserver.observe(mount);

    // 清理资源，避免内存泄漏
    return () => {
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
          object.material.map?.dispose();
          object.material.dispose();
        }
      });
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [layout, height]);

  if (!layout || !layout.rooms?.length) {
    return (
      <div
        style={{ height }}
        className="grid place-items-center rounded-xl border border-line bg-surface2 text-sm text-muted"
      >
        暂无 3D 布局数据
      </div>
    );
  }

  return (
    <div className="relative">
      <div ref={mountRef} className="scene3d w-full" style={{ height }} />
      <p className="pointer-events-none absolute bottom-2.5 left-1/2 -translate-x-1/2 text-xs text-muted">
        拖拽旋转 · 滚轮缩放 · 右键平移
      </p>
    </div>
  );
}
