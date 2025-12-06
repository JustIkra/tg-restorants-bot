import React from "react";

type Category = { id: number | string; name: string; icon: React.ReactNode };

interface CategorySelectorProps {
  categories: Category[];
  activeCategoryId: number | string;
  onCategoryClick: (id: number | string) => void;
}

const CategorySelector: React.FC<CategorySelectorProps> = ({ categories, activeCategoryId, onCategoryClick }) => (
  <div className="flex gap-4 flex-nowrap pl-[17px] pr-6 py-2">
    {categories.map((category) => (
      <div key={category.id} className="relative">
        <button
          onClick={() => onCategoryClick(category.id)}
          className="flex flex-col items-center flex-shrink-0 group"
        >
          <div className="relative w-[93px] h-[89px] mb-2 flex items-center justify-center">
            <div 
              className={`absolute inset-0 bg-[#7B6F9C] rounded-[14px] transition-all duration-300\
                        ${activeCategoryId === category.id 
                          ? 'opacity-30' 
                          : 'opacity-20 group-hover:opacity-30'
                        }`}
            />
            <div className="relative z-10">
              <div 
                className={`text-3xl transition-all duration-300 group-hover:scale-110\
                          ${activeCategoryId === category.id 
                            ? 'text-white' 
                            : 'text-gray-300 group-hover:text-white'
                          }`}
              >
                {category.icon}
              </div>
            </div>
          </div>
          <span 
            className={`text-sm font-medium transition-colors duration-300 text-center w-full\
                      ${activeCategoryId === category.id 
                        ? 'text-white font-semibold' 
                        : 'text-gray-300 group-hover:text-white'
                      }`}
          >
            {category.name}
          </span>
        </button>
        {activeCategoryId === category.id && (
          <div className="absolute top-0 right-0 w-6 h-6 bg-gradient-to-br from-[#8B23CB] to-[#A020F0] rounded-full flex items-center justify-center z-20 shadow-lg transform translate-x-1 -translate-y-1">
            <div className="w-2 h-2 bg-white rounded-full" />
          </div>
        )}
      </div>
    ))}
  </div>
);

export default CategorySelector;
