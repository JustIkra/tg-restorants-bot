/**
 * TelegramFallback Component
 *
 * Displays a user-friendly message when the app is accessed outside of Telegram.
 * Shows instructions on how to open the app through the Telegram bot.
 */

import { FaTelegram } from "react-icons/fa6";

export default function TelegramFallback() {
  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
      {/* Background blur effects */}
      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      {/* Content card */}
      <div className="relative max-w-md w-full bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-8 text-center">
        <FaTelegram className="text-[#26A5E4] text-6xl mx-auto mb-4" />
        <h1 className="text-white text-2xl font-bold mb-4">
          Откройте через Telegram
        </h1>
        <p className="text-gray-300 mb-6">
          Это приложение работает только внутри Telegram.
          Откройте бот и нажмите кнопку &quot;Заказать обед&quot; или используйте команду /order.
        </p>
        <div className="bg-white/5 border border-white/10 rounded-lg p-4 text-left">
          <p className="text-gray-400 text-sm mb-2">Инструкция:</p>
          <ol className="text-gray-300 text-sm space-y-1">
            <li>1. Откройте Telegram</li>
            <li>2. Найдите бот в поиске</li>
            <li>3. Нажмите кнопку Menu или отправьте /order</li>
          </ol>
        </div>
      </div>
    </div>
  );
}
