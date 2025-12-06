"use client";

import { useEffect, useRef, useState } from "react";
import { FaUtensils, FaCartShopping, FaLeaf, FaSeedling, FaExclamation } from "react-icons/fa6";

type Dish = {
  id: number;
  name: string;
  price: number;
  composition?: string[];
  suitableFor?: string[];
};

const mockDishes: Dish[] = [
  { id: 1, name: "Борщ", price: 450, composition: ["Свекла", "Капуста", "Морковь"], suitableFor: ["Не подходит веганам", "Не подходит вегетарианцам", "Аллергены: лактоза"] },
  { id: 2, name: "Стейк Рибай", price: 1200, composition: ["Говядина", "Специи"], suitableFor: ["Не подходит веганам", "Не подходит вегетарианцам", "Аллергены: глютен"] },
  { id: 3, name: "Цезарь", price: 550, composition: ["Курица", "Салат", "Сухарики"], suitableFor: ["Не подходит веганам", "Не подходит вегетарианцам", "Аллергены: лактоза, глютен"] },
  { id: 4, name: "Тирамису", price: 350, composition: ["Маскарпоне", "Кофе", "Печенье"], suitableFor: ["Не подходит веганам", "Не подходит вегетарианцам", "Аллергены: лактоза, глютен, яйца"] },
  { id: 5, name: "Маргарита", price: 650, composition: ["Томат", "Моцарелла", "Базилик"], suitableFor: ["Подходит вегетарианцам", "Не подходит веганам", "Аллергены: лактоза, глютен"] },
  { id: 6, name: "Суши сет", price: 900, composition: ["Рис", "Нори", "Лосось"], suitableFor: ["Не подходит веганам", "Не подходит вегетарианцам", "Аллергены: рыба, соевый соус"] },
  { id: 7, name: "Бургер Чизбургер", price: 480, composition: ["Булочка", "Говядина", "Сыр"], suitableFor: ["Не подходит веганам", "Не подходит вегетарианцам", "Аллергены: лактоза, глютен"] },
];

const ONE_DAY = 24 * 60 * 60 * 1000;

export default function FortuneWheel() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [selectedDish, setSelectedDish] = useState<Dish | null>(null);
  const [isSpinning, setIsSpinning] = useState(false);
  const [canSpin, setCanSpin] = useState(true);
  const [timeLeft, setTimeLeft] = useState(0);

  const isSpinningRef = useRef(false);
  const gradientShift = useRef(0);
  const currentAngle = useRef(0);

  const dishes = mockDishes;
  const numberOfItems = dishes.length;
  const arc = (2 * Math.PI) / numberOfItems;
  const baseColors = ["#9d4edd", "#7b2cbf", "#8a2be2", "#6a0dad"];

  useEffect(() => {
    const lastSpin = localStorage.getItem("lastSpin");
    if (lastSpin) {
      const nextSpinTime = parseInt(lastSpin) + ONE_DAY;
      const now = Date.now();
      if (now < nextSpinTime) {
        setCanSpin(false);
        setTimeLeft(nextSpinTime - now);
      }
    }
  }, []);

  useEffect(() => {
    if (canSpin) return;
    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1000) {
          clearInterval(interval);
          setCanSpin(true);
          return 0;
        }
        return prev - 1000;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [canSpin]);

  const drawWheel = (ctx: CanvasRenderingContext2D, angle = 0, spinning = false) => {
    if (!ctx) return;

    const width = canvasRef.current?.width || 500;
    const height = canvasRef.current?.height || 500;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 2 - 10;

    ctx.clearRect(0, 0, width, height);

    for (let i = 0; i < numberOfItems; i++) {
      const startAngle = angle + i * arc;
      let color = baseColors[i % baseColors.length];

      if (spinning) {
        const colorIndex = (i + gradientShift.current) % baseColors.length;
        const nextColorIndex = (Math.floor(colorIndex) + 1) % baseColors.length;
        const t = colorIndex - Math.floor(colorIndex);

        const hexToRgb = (hex: string) => {
          const bigint = parseInt(hex.slice(1), 16);
          return [(bigint >> 16) & 255, (bigint >> 8) & 255, bigint & 255];
        };
        const rgbToHex = (r: number, g: number, b: number) =>
          `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;

        const c1 = hexToRgb(baseColors[Math.floor(colorIndex)]);
        const c2 = hexToRgb(baseColors[nextColorIndex]);
        const r = Math.round(c1[0] + (c2[0] - c1[0]) * t);
        const g = Math.round(c1[1] + (c2[1] - c1[1]) * t);
        const b = Math.round(c1[2] + (c2[2] - c1[2]) * t);
        color = rgbToHex(r, g, b);
      }

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.arc(centerX, centerY, radius, startAngle, startAngle + arc);
      ctx.fillStyle = color;
      ctx.fill();
      ctx.strokeStyle = "rgba(255,255,255,0.15)";
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.save();
      ctx.translate(centerX, centerY);
      ctx.rotate(startAngle + arc / 2);
      ctx.fillStyle = "white";
      ctx.font = `bold ${Math.max(14, radius / 15)}px sans-serif`;
      ctx.textAlign = "right";
      ctx.fillText(dishes[i].name, radius - 30, 10);
      ctx.restore();
    }

    for (let i = 0; i < numberOfItems; i++) {
      const startAngle = angle + i * arc;
      const bulbX = centerX + Math.cos(startAngle) * radius;
      const bulbY = centerY + Math.sin(startAngle) * radius;
      const pulse = 0.7 + 0.3 * Math.sin(performance.now() / 300 + i);

      ctx.beginPath();
      ctx.arc(bulbX, bulbY, 10, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${0.15 * pulse})`;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(bulbX, bulbY, 4.5, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 210, 255, ${0.7 + 0.3 * pulse})`;
      ctx.fill();
    }

    const centerPulse = 0.6 + 0.4 * Math.sin(performance.now() / 400);
    ctx.beginPath();
    ctx.arc(centerX, centerY, 12, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 255, 255, ${0.2 * centerPulse})`;
    ctx.fill();

    ctx.beginPath();
    ctx.arc(centerX, centerY, 6, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255, 200, 255, ${0.8 * centerPulse})`;
    ctx.fill();
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    let animationFrame: number;

    const animate = () => {
      if (isSpinningRef.current) {
        gradientShift.current += 0.02;
      }
      drawWheel(ctx, currentAngle.current, isSpinningRef.current);
      animationFrame = requestAnimationFrame(animate);
    };

    animate();
    return () => cancelAnimationFrame(animationFrame);
  }, []);

  const spin = () => {
    if (!canSpin || isSpinningRef.current) return;

    setSelectedDish(null);
    setIsSpinning(true);
    isSpinningRef.current = true;

    const now = Date.now();
    localStorage.setItem("lastSpin", now.toString());
    setCanSpin(false);
    setTimeLeft(ONE_DAY);

    const duration = 5000;
    const startAngle = currentAngle.current;
    const randomRotation = Math.random() * 2 * Math.PI + 5 * 2 * Math.PI;
    const endAngle = startAngle + randomRotation;
    const startTime = performance.now();

    const animateSpin = (time: number) => {
      const elapsed = time - startTime;
      const t = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - t, 3);
      currentAngle.current = startAngle + (endAngle - startAngle) * easeOut;
      if (t < 1) requestAnimationFrame(animateSpin);
      else {
        const normalizedAngle = currentAngle.current % (2 * Math.PI);
        const pointerAngle = (3 * Math.PI / 2 - normalizedAngle + 2 * Math.PI) % (2 * Math.PI);
        const index = Math.floor(pointerAngle / arc);
        setSelectedDish(dishes[index]);
        setIsSpinning(false);
        isSpinningRef.current = false;
      }
    };

    requestAnimationFrame(animateSpin);
  };

  const formatTime = (ms: number) => {
    const totalSeconds = Math.floor(ms / 1000);
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    const seconds = totalSeconds % 60;
    return `${hours.toString().padStart(2, "0")}:${minutes
      .toString()
      .padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  };

  return (
    <div className="relative w-full min-h-screen flex flex-col items-center justify-center p-4 bg-[#130F30] overflow-x-hidden">
      <div className="absolute bg-[#A020F0] blur-[250px] opacity-40 rounded-full w-[140%] h-[60%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90 pointer-events-none" />
      <div className="absolute bg-[#A020F0] blur-[180px] opacity-40 rounded-full w-[90%] h-[70%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none" />

      <h1 className="text-4xl md:text-5xl font-bold text-white mb-8 z-10 relative text-center">
        Колесо фортуны
      </h1>

      <div className="relative w-full max-w-[500px] h-auto aspect-square mb-8">
        <canvas
          ref={canvasRef}
          width={500}
          height={500}
          className="w-full h-full rounded-full shadow-[0_0_70px_rgba(162,100,255,0.6)]"
        />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 z-20 rotate-180 pointer-events-none">
          <div className="w-0 h-0 border-l-[20px] border-r-[20px] border-b-[40px] border-l-transparent border-r-transparent border-b-purple-400" />
        </div>
      </div>

      <button
        onClick={spin}
        disabled={!canSpin || isSpinning}
        className="px-10 py-4 rounded-2xl font-bold text-white bg-gradient-to-br from-[#8B23CB] to-[#A020F0] shadow-lg hover:scale-105 transition disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {isSpinning
          ? "Крутим..."
          : canSpin
          ? "Крутить колесо"
          : `Доступно через: ${formatTime(timeLeft)}`}
      </button>

      {selectedDish && (
        <div className="mt-6 p-6 bg-white/10 border border-white/20 rounded-3xl text-white text-center backdrop-blur-xl flex flex-col items-center gap-4 w-full max-w-md">
          <FaUtensils className="text-2xl" />
          <p className="text-lg mb-1">Ваш выбор:</p>
          <p className="text-3xl font-bold">{selectedDish.name}</p>
          <p className="text-sm opacity-80">{selectedDish.price} ₽</p>

          {selectedDish.composition && selectedDish.composition.length > 0 && (
            <div className="mt-4 text-left w-full">
              <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
                <span className="w-2 h-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-full"></span>
                Состав:
              </h3>
              <div className="flex flex-wrap gap-2">
                {selectedDish.composition.map((item, idx) => (
                  <span key={idx} className="px-3 py-1.5 bg-white/5 text-gray-300 rounded-lg text-sm border border-white/5">
                    {item}
                  </span>
                ))}
              </div>
            </div>
          )}

          {selectedDish.suitableFor && selectedDish.suitableFor.length > 0 && (
            <div className="mt-4 text-left w-full">
              <h3 className="text-white font-semibold mb-2 flex items-center gap-2">
                <span className="w-2 h-2 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] rounded-full"></span>
                Кому подходит:
              </h3>
              <div className="flex flex-col gap-2">
                {selectedDish.suitableFor.map((item, idx) => {
                  let icon = <FaExclamation className="text-yellow-400" />;
                  if (item.toLowerCase().includes("веган")) icon = <FaLeaf className="text-green-400" />;
                  if (item.toLowerCase().includes("вегетариан")) icon = <FaSeedling className="text-green-500" />;
                  let colorClass = "text-gray-400";
                  if (item.includes("Не подходит")) colorClass = "text-red-300";
                  if (item.includes("Подходит")) colorClass = "text-green-300";
                  if (item.toLowerCase().includes("аллерген")) colorClass = "text-yellow-300";

                  return (
                    <div key={idx} className={`flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-sm ${colorClass}`}>
                      {icon}
                      <span>{item}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

         <button
  onClick={() => window.location.href = '/'}
  className="flex items-center justify-center px-8 py-3 rounded-xl bg-gradient-to-br from-[#8B23CB] to-[#A020F0] hover:from-[#8B23CB]/90 hover:to-[#A020F0]/90 shadow-lg transition-all duration-300 hover:scale-105 active:scale-95 text-white font-bold mt-4"
>
  <FaCartShopping className="mr-2" /> Добавить в корзину
</button>
        </div>
      )}
    </div>
  );
}
