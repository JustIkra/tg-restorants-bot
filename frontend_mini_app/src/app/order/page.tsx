"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { FaArrowLeft, FaUser } from "react-icons/fa";
import AddressInput from "@/components/Order/AddressInput";
import SavedAddresses from "@/components/Order/SavedAddresses";
import DeliveryTimeSelector from "@/components/Order/DeliveryTimeSelector";
import PaymentMethod from "@/components/Order/PaymentMethod";
import ErrorMessage from "@/components/UI/ErrorMessage";
import ActionButtons from "@/components/UI/ActionButtons";
import { getAddressFromYandex, getLocationByIP } from "@/components/Order/geocoder";
import { useAlert } from "@/components/UI/CustomAlert";

export default function Home() {
  const router = useRouter();
  const [burgerCount, setBurgerCount] = useState(1);
  const [saladCount, setSaladCount] = useState(1);
  const [rollCount, setRollCount] = useState(1);
  
  const [deliveryTime, setDeliveryTime] = useState("Сейчас");
  const [address, setAddress] = useState("");
  const [fullName, setFullName] = useState("");
  const [showSavedAddresses, setShowSavedAddresses] = useState(false);
  const [isGettingLocation, setIsGettingLocation] = useState(false);
  const [locationError, setLocationError] = useState<string | null>(null);
  
  const [addressSuggestions, setAddressSuggestions] = useState<{title: string, subtitle: string, fullAddress: string}[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [showTimeDropdown, setShowTimeDropdown] = useState(false);
  
  const addressInputRef = useRef<HTMLInputElement>(null);
  const timeDropdownRef = useRef<HTMLDivElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  const savedAddresses = [
    "ул. Ленина, д. 15, кв. 42, Москва",
    "пр. Победы, д. 28, офис 305, Санкт-Петербург",
    "ул. Мира, д. 7, подъезд 3, Екатеринбург"
  ];

  const timeOptions = [
    { value: "Сейчас", label: "Сейчас", icon: "⚡" },
    { value: "30 минут", label: "Через 30 минут", icon: "⏱️" },
    { value: "1 час", label: "Через 1 час", icon: "🕐" },
    { value: "1.5 часа", label: "Через 1.5 часа", icon: "🕜" },
    { value: "2 часа", label: "Через 2 часа", icon: "🕑" }
  ];

  const fetchSuggestions = async (query: string) => {
    if (query.length < 2) {
      setAddressSuggestions([]);
      setShowSuggestions(false);
      setIsLoadingSuggestions(false);
      return;
    }
    
    setIsLoadingSuggestions(true);
    
    try {
      console.log('Fetching suggestions for:', query);
      const response = await fetch(`/api/suggest?q=${encodeURIComponent(query)}`);
      const data = await response.json();
      console.log('Suggestions received:', data);
      
      if (data.results && Array.isArray(data.results) && data.results.length > 0) {
        setAddressSuggestions(data.results);
        setShowSuggestions(true);
      } else {
        setAddressSuggestions([]);
        setShowSuggestions(false);
      }
    } catch (error) {
      console.error("Ошибка получения подсказок:", error);
      setAddressSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setIsLoadingSuggestions(false);
    }
  };

  const debouncedSearch = (query: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    debounceTimerRef.current = setTimeout(() => {
      fetchSuggestions(query);
    }, 300);
  };

  useEffect(() => {
    if (address.length >= 2) {
      debouncedSearch(address);
    } else {
      setAddressSuggestions([]);
      setShowSuggestions(false);
      setIsLoadingSuggestions(false);
    }
    
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [address]);

  const getCurrentLocation = async () => {
    setLocationError(null);
    setIsGettingLocation(true);

    if (!navigator.geolocation) {
      const ipLocation = await getLocationByIP();
      if (ipLocation) {
        const addressText = await getAddressFromYandex(ipLocation.lat, ipLocation.lon);
        setAddress(addressText);
      } else {
        setLocationError("Геолокация не поддерживается. Введите адрес вручную.");
      }
      setIsGettingLocation(false);
      return;
    }

    const options: PositionOptions = {
      enableHighAccuracy: false,
      timeout: 5000,
      maximumAge: 60000
    };

    const successCallback = async (position: GeolocationPosition) => {
      const { latitude, longitude } = position.coords;
      
      try {
        const addressText = await getAddressFromYandex(latitude, longitude);
        setAddress(addressText);
        
        localStorage.setItem('userLocation', JSON.stringify({
          address: addressText,
          latitude,
          longitude,
          timestamp: Date.now()
        }));
        
      } catch (error) {
        setAddress(`Координаты: ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`);
      } finally {
        setIsGettingLocation(false);
      }
    };

    const errorCallback = async (error: GeolocationPositionError) => {
      const ipLocation = await getLocationByIP();
      if (ipLocation) {
        const addressText = await getAddressFromYandex(ipLocation.lat, ipLocation.lon);
        setAddress(`Приблизительно: ${addressText} (по IP)`);
      } else {
        if (error.code === 1) {
          setLocationError("Разрешите доступ к геолокации в настройках браузера");
        } else if (error.code === 3) {
          setLocationError("Определение местоположения заняло слишком много времени");
        } else {
          setLocationError("Не удалось определить местоположение");
        }
        
        const savedLocation = localStorage.getItem('userLocation');
        if (savedLocation) {
          try {
            const locationData = JSON.parse(savedLocation);
            setAddress(`${locationData.address} (последний адрес)`);
          } catch (e) {
            console.error("Ошибка чтения сохраненного адреса:", e);
          }
        }
      }
      
      setIsGettingLocation(false);
    };

    navigator.geolocation.getCurrentPosition(
      successCallback,
      errorCallback,
      options
    );
  };

  useEffect(() => {
    const savedLocation = localStorage.getItem('userLocation');
    if (savedLocation) {
      try {
        const locationData = JSON.parse(savedLocation);
        setAddress(locationData.address);
      } catch (e) {
        console.error("Ошибка чтения сохраненного адреса:", e);
      }
    }
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (addressInputRef.current && !addressInputRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
      
      if (timeDropdownRef.current && !timeDropdownRef.current.contains(event.target as Node)) {
        setShowTimeDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelectSuggestion = (fullAddress: string) => {
    setAddress(fullAddress);
    setShowSuggestions(false);
    
    localStorage.setItem('userLocation', JSON.stringify({
      address: fullAddress,
      timestamp: Date.now()
    }));
  };

  const handleManualSearch = () => {
    if (address.length >= 2) {
      fetchSuggestions(address);
      setShowSuggestions(true);
    }
  };

  const { showAlert, AlertComponent } = useAlert();

  const handleConfirmOrder = () => {
    if (!address.trim()) {
      showAlert("Пожалуйста, укажите адрес доставки", "error");
      addressInputRef.current?.focus();
      return;
    }
    if (!fullName.trim()) {
      showAlert("Пожалуйста, укажите ваше ФИО", "error");
      return;
    }
    const totalPrice = (burgerCount * 420) + (saladCount * 320) + (rollCount * 380);
    localStorage.setItem('userLocation', JSON.stringify({
      address: address.trim(),
      timestamp: Date.now()
    }));
    showAlert(` Ваш заказ подтверждён!`, "success", 7000);
  };

  const incrementBurger = () => setBurgerCount(prev => prev + 1);
  const decrementBurger = () => setBurgerCount(prev => prev > 1 ? prev - 1 : 1);
  const incrementSalad = () => setSaladCount(prev => prev + 1);
  const decrementSalad = () => setSaladCount(prev => prev > 1 ? prev - 1 : 1);
  const incrementRoll = () => setRollCount(prev => prev + 1);
  const decrementRoll = () => setRollCount(prev => prev > 1 ? prev - 1 : 1);

  const totalPrice = (burgerCount * 420) + (saladCount * 320) + (rollCount * 380);

  return (
    <div className="relative w-full min-h-screen bg-[#130F30] overflow-x-hidden pb-32">
      <div className="absolute bg-[#A020F0] blur-[200px] opacity-40 rounded-full w-[120%] h-[50%] top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 -rotate-90" />
      <div className="absolute bg-[#A020F0] blur-[150px] opacity-40 rounded-full w-[80%] h-[60%] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

      <div className="relative w-full md:w-[90%] min-h-screen mx-auto bg-white/5 backdrop-blur-md border border-white/10 rounded-none md:rounded-2xl overflow-visible pb-32">
  
        <div className="px-4 pt-6 md:px-6 pb-4">
          <div className="flex items-center gap-3 mb-6">
            <button 
              className="p-3 hover:opacity-80 transition flex-shrink-0 rounded-lg bg-[rgba(123,111,156,0.2)] border border-white/10"
              onClick={() => router.push('/')}
            >
              <FaArrowLeft className="text-white text-xl" />
            </button>
            
            <div className="px-4 py-2 bg-[rgba(123,111,156,0.25)] rounded-lg border border-white/15 backdrop-blur-sm">
              <span className="font-semibold text-white text-lg">Zemlya</span>
            </div>
          </div>

          <h1 className="text-2xl md:text-3xl font-bold text-white mb-4">Food Delivery</h1>

          <div className="mb-6">
            <div className="px-6 py-3 bg-[#786F9C]/30 rounded-lg border border-white/10 inline-block">
              <h2 className="font-bold text-white text-xl md:text-2xl">Оформление заказа</h2>
            </div>
          </div>
        </div>

       
        <div className="px-4 md:px-6">
   
          <div className="space-y-4 mb-8">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-[#7B6F9C]/30 rounded-xl border border-white/10">
              <div className="flex-1">
                <h3 className="font-extrabold text-white text-lg md:text-xl mb-1">Сырный бургер</h3>
                <p className="text-white text-opacity-90 text-lg">{420 * burgerCount} ₽</p>
              </div>
              <div className="flex items-center gap-3 bg-white/10 rounded-2xl px-4 py-2 border border-white/10">
                <button 
                  onClick={decrementBurger}
                  className="bg-white/20 border border-white/20 text-white w-8 h-8 rounded-full text-xl cursor-pointer flex items-center justify-center hover:bg-white/30 transition"
                >
                  -
                </button>
                <span className="text-white font-bold text-xl min-w-8 text-center">{burgerCount}</span>
                <button 
                  onClick={incrementBurger}
                  className="bg-white/20 border border-white/20 text-white w-8 h-8 rounded-full text-xl cursor-pointer flex items-center justify-center hover:bg-white/30 transition"
                >
                  +
                </button>
              </div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-[#7B6F9C]/30 rounded-xl border border-white/10">
              <div className="flex-1">
                <h3 className="font-extrabold text-white text-lg md:text-xl mb-1">Цезарь-салат с курицей</h3>
                <p className="text-white text-opacity-90 text-lg">{320 * saladCount} ₽</p>
              </div>
              <div className="flex items-center gap-3 bg-white/10 rounded-2xl px-4 py-2 border border-white/10">
                <button 
                  onClick={decrementSalad}
                  className="bg-white/20 border border-white/20 text-white w-8 h-8 rounded-full text-xl cursor-pointer flex items-center justify-center hover:bg-white/30 transition"
                >
                  -
                </button>
                <span className="text-white font-bold text-xl min-w-8 text-center">{saladCount}</span>
                <button 
                  onClick={incrementSalad}
                  className="bg-white/20 border border-white/20 text-white w-8 h-8 rounded-full text-xl cursor-pointer flex items-center justify-center hover:bg-white/30 transition"
                >
                  +
                </button>
              </div>
            </div>

            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 bg-[#7B6F9C]/30 rounded-xl border border-white/10">
              <div className="flex-1">
                <h3 className="font-extrabold text-white text-lg md:text-xl mb-1">Ролл с лососем</h3>
                <p className="text-white text-opacity-90 text-lg">{380 * rollCount} ₽</p>
              </div>
              <div className="flex items-center gap-3 bg-white/10 rounded-2xl px-4 py-2 border border-white/10">
                <button 
                  onClick={decrementRoll}
                  className="bg-white/20 border border-white/20 text-white w-8 h-8 rounded-full text-xl cursor-pointer flex items-center justify-center hover:bg-white/30 transition"
                >
                  -
                </button>
                <span className="text-white font-bold text-xl min-w-8 text-center">{rollCount}</span>
                <button 
                  onClick={incrementRoll}
                  className="bg-white/20 border border-white/20 text-white w-8 h-8 rounded-full text-xl cursor-pointer flex items-center justify-center hover:bg-white/30 transition"
                >
                  +
                </button>
              </div>
            </div>
          </div>

          <div className="mb-8 flex justify-end">
            <div className="px-6 py-4 bg-gradient-to-r from-[#8B23CB]/30 to-[#A020F0]/30 rounded-lg border border-white/10 inline-block">
              <p className="font-extrabold text-white text-xl md:text-2xl">Итого: {totalPrice} ₽</p>
            </div>
          </div>

          <div className="space-y-6 mb-20">
            <div className="space-y-4">
              <div className="px-4 py-2 bg-gradient-to-r from-[#8B23CB]/30 to-[#A020F0]/30 rounded-lg border border-white/10 inline-block">
                <h4 className="font-bold text-white text-lg">Адрес доставки</h4>
              </div>
              
              <div className="p-3 bg-green-500/10 border border-green-500/20 rounded-lg">
                <p className="text-green-300 text-sm">
                  💡 Начните вводить улицу и город или нажмите на "мое местоположение"
                </p>
              </div>
              
              <AddressInput
                address={address}
                onChange={(e) => setAddress(e.target.value)}
                onManualSearch={handleManualSearch}
                addressInputRef={addressInputRef}
                isLoadingSuggestions={isLoadingSuggestions}
                showSuggestions={showSuggestions}
                addressSuggestions={addressSuggestions}
                onSelectSuggestion={handleSelectSuggestion}
              />
              
              <ActionButtons
                onGetLocation={getCurrentLocation}
                isGettingLocation={isGettingLocation}
                onToggleSavedAddresses={() => setShowSavedAddresses(!showSavedAddresses)}
                showSavedAddresses={showSavedAddresses}
              />
              
              {locationError && (
                <ErrorMessage message={locationError} />
              )}

              {showSavedAddresses && (
                <SavedAddresses
                  savedAddresses={savedAddresses}
                  address={address}
                  onSelect={(addr) => {
                    setAddress(addr);
                    localStorage.setItem('userLocation', JSON.stringify({
                      address: addr,
                      timestamp: Date.now()
                    }));
                  }}
                />
              )}
            </div>

            <DeliveryTimeSelector
              deliveryTime={deliveryTime}
              setDeliveryTime={setDeliveryTime}
              showTimeDropdown={showTimeDropdown}
              setShowTimeDropdown={setShowTimeDropdown}
              timeOptions={timeOptions}
              timeDropdownRef={timeDropdownRef}
            />

            <PaymentMethod totalPrice={totalPrice} />

            <div className="space-y-3">
              <div className="px-4 py-2 bg-gradient-to-r from-[#8B23CB]/30 to-[#A020F0]/30 rounded-lg border border-white/10 inline-block">
                <h4 className="font-bold text-white text-lg">ФИО</h4>
              </div>
              <div className="flex items-center gap-3 p-4 bg-white/5 rounded-xl border border-white/10">
                <FaUser className="text-white text-xl opacity-90 flex-shrink-0" />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="font-semibold text-white text-lg bg-transparent border-none w-full focus:outline-none focus:ring-0 placeholder-white/60"
                  placeholder="Иванов Иван Иванович"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
      <div className="fixed left-0 right-0 bottom-0 z-50 p-4 backdrop-blur-lg bg-gradient-to-t from-[#130F30] via-[#130F30]/95 to-transparent">
        <div className="max-w-2xl mx-auto bg-[#7B6F9C]/30 border border-white/10 backdrop-blur-xl rounded-xl p-4">
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleConfirmOrder}
              className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-[#8B23CB] to-[#A020F0] border border-white/20 rounded-lg hover:opacity-90 transition cursor-pointer flex-1 shadow-lg"
            >
              <span className="font-bold text-white text-lg">Подтвердить заказ</span>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M4.16667 10H15.8333M15.8333 10L10 4.16667M15.8333 10L10 15.8333" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>

            <button
              onClick={() => router.push('/')}
              className="flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-[#FF416C]/30 to-[#FF4B2B]/30 border border-[#FF416C]/40 rounded-lg hover:opacity-90 transition cursor-pointer flex-1 shadow-lg"
            >
              <span className="font-bold text-white text-lg">Отменить</span>
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15 5L5 15M5 5L15 15" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <AlertComponent />
    </div>
  );
}