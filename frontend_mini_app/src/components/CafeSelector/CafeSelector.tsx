import React from "react";

type Cafe = { id: number; name: string };

interface CafeSelectorProps {
  cafes: Cafe[];
  activeCafeId: number;
  onCafeClick: (id: number) => void;
}

const CafeSelector: React.FC<CafeSelectorProps> = ({ cafes, activeCafeId, onCafeClick }) => (
  <div className="flex gap-3 flex-nowrap pl-[17px] pr-6">
    {cafes.map((cafe) => (
      <button
        key={cafe.id}
        onClick={() => onCafeClick(cafe.id)}
        className="relative px-6 py-3 transition-all duration-500 overflow-hidden flex-shrink-0 group"
      >
        <div 
          className={`absolute inset-0 rounded-xl transition-all duration-500 ${
            activeCafeId === cafe.id 
              ? 'bg-gradient-to-r from-[#8B23CB] via-[#A020F0] to-[#7723B6]' 
              : 'bg-[#7B6F9C] opacity-30'
          }`}
        />
        <div className="absolute inset-0 overflow-hidden rounded-xl">
          <div 
            className={`absolute inset-0 bg-gradient-to-r from-[#8B23CB] via-[#A020F0] to-[#8B23CB] \
                      bg-[length:200%_100%] rounded-xl transition-opacity duration-1000\
                      ${activeCafeId === cafe.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
            style={{
              animation: activeCafeId === cafe.id ? 'gradientShift 3s ease-in-out infinite' : 'none'
            }}
          />
        </div>
        <span 
          className={`relative font-medium text-sm whitespace-nowrap transition-colors duration-300\
                    ${activeCafeId === cafe.id 
                      ? 'text-white font-semibold' 
                      : 'text-gray-300 group-hover:text-white'
                    }`}
        >
          {cafe.name}
        </span>
      </button>
    ))}
  </div>
);

export default CafeSelector;
