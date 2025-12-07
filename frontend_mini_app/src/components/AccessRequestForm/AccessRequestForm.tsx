"use client";

import React, { useState } from "react";
import { FaUser, FaBuilding, FaPaperPlane, FaSpinner } from "react-icons/fa6";

interface AccessRequestFormProps {
  name: string;
  username: string | null;
  onSubmit: (office: string) => Promise<void>;
  onSuccess: () => void;
}

const AccessRequestForm: React.FC<AccessRequestFormProps> = ({
  name,
  username,
  onSubmit,
  onSuccess,
}) => {
  const [office, setOffice] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!office.trim()) {
      setError("Пожалуйста, укажите офис");
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      await onSubmit(office.trim());
      onSuccess();
    } catch (err) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : typeof err === "string"
          ? err
          : "Не удалось отправить запрос";
      setError(errorMessage);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#130F30] flex items-center justify-center p-4">
      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      <div className="relative w-full max-w-md bg-white/5 backdrop-blur-md border border-white/10 rounded-2xl p-6 md:p-8">
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-[#8B23CB] to-[#A020F0] flex items-center justify-center">
            <FaUser className="text-white text-2xl" />
          </div>
          <h2 className="text-white text-2xl font-bold mb-2">
            Запрос доступа
          </h2>
          <p className="text-gray-300 text-sm">
            Заполните форму для получения доступа к приложению
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Имя
            </label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                <FaUser className="text-gray-400" />
              </div>
              <input
                type="text"
                value={name}
                readOnly
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 cursor-not-allowed"
              />
            </div>
          </div>

          {username && (
            <div>
              <label className="block text-white text-sm font-medium mb-2">
                Username
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2">
                  <FaUser className="text-gray-400" />
                </div>
                <input
                  type="text"
                  value={`@${username}`}
                  readOnly
                  className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 cursor-not-allowed"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-white text-sm font-medium mb-2">
              Офис <span className="text-red-400">*</span>
            </label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2">
                <FaBuilding className="text-gray-400" />
              </div>
              <input
                type="text"
                value={office}
                onChange={(e) => setOffice(e.target.value)}
                placeholder="Введите название офиса"
                disabled={isSubmitting}
                className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#A020F0] focus:ring-2 focus:ring-[#A020F0]/50 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              />
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg">
              <p className="text-red-200 text-sm">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !office.trim()}
            className="w-full py-3 px-6 rounded-lg font-medium bg-gradient-to-br from-[#8B23CB] to-[#A020F0] text-white border border-white/20 hover:from-[#9B33DB] hover:to-[#B030FF] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <FaSpinner className="animate-spin" />
                <span>Отправка...</span>
              </>
            ) : (
              <>
                <FaPaperPlane />
                <span>Отправить запрос</span>
              </>
            )}
          </button>
        </form>

        <p className="text-gray-400 text-xs text-center mt-4">
          После отправки запроса дождитесь одобрения менеджера
        </p>
      </div>
    </div>
  );
};

export default AccessRequestForm;
