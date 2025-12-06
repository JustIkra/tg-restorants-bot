import React from "react";

interface SavedAddressesProps {
  savedAddresses: string[];
  address: string;
  onSelect: (addr: string) => void;
}

const SavedAddresses: React.FC<SavedAddressesProps> = ({ savedAddresses, address, onSelect }) => (
  <div className="space-y-2">
    {savedAddresses.map((addr, index) => (
      <button
        key={index}
        onClick={() => onSelect(addr)}
        className={`w-full p-3 text-left rounded-lg border transition ${address === addr ? 'bg-gradient-to-r from-[#8B23CB]/20 to-[#A020F0]/20 border-white/30' : 'bg-white/5 border-white/10'}`}
      >
        <span className="font-medium text-white">{addr}</span>
      </button>
    ))}
  </div>
);

export default SavedAddresses;
