export const YANDEX_GEOCODER_API_KEY = "a4a7cd16-4874-4753-80aa-10d586ee8c58";

export async function getAddressFromYandex(latitude: number, longitude: number): Promise<string> {
  try {
    const response = await fetch(
      `https://geocode-maps.yandex.ru/1.x/?format=json&geocode=${longitude},${latitude}&lang=ru_RU&apikey=${YANDEX_GEOCODER_API_KEY}&results=1&kind=house`
    );
    const data = await response.json();
    
    console.log('Yandex Geocoder Response:', data);
    
    if (data.response?.GeoObjectCollection?.featureMember?.[0]?.GeoObject) {
      const geoObject = data.response.GeoObjectCollection.featureMember[0].GeoObject;
      const address = geoObject.metaDataProperty?.GeocoderMetaData?.text;

      const detailedAddress = geoObject.metaDataProperty?.GeocoderMetaData?.Address?.formatted;
      const postalCode = geoObject.metaDataProperty?.GeocoderMetaData?.Address?.postal_code;

      if (detailedAddress) {
        return detailedAddress;
      } else if (address) {
        return address;
      }
    }

    return `Неизвестный адрес (${latitude.toFixed(6)}, ${longitude.toFixed(6)})`;
  } catch (error) {
    console.error("Ошибка Яндекс геокодирования:", error);
    return `Ошибка определения (${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;
  }
}

export async function getPreciseAddress(latitude: number, longitude: number): Promise<string> {
  try {
    const yandexAddress = await getAddressFromYandex(latitude, longitude);

    try {
      const osmResponse = await fetch(
        `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&addressdetails=1&accept-language=ru`
      );
      const osmData = await osmResponse.json();
      
      if (osmData.display_name) {
        console.log('OSM Address:', osmData.display_name);
        
        if (yandexAddress.includes('Неизвестный') || yandexAddress.includes('Ошибка')) {
          return osmData.display_name;
        }
      }
    } catch (osmError) {
      console.warn('OSM geocoding failed:', osmError);
    }
    
    return yandexAddress;
  } catch (error) {
    console.error('Precise geocoding error:', error);
    return `г. Москва (приблизительно: ${latitude.toFixed(4)}, ${longitude.toFixed(4)})`;
  }
}

export async function getLocationByIP(): Promise<{lat: number, lon: number, city: string, accuracy?: number} | null> {
  try {
    const providers = [
      'https://ipapi.co/json/',
      'https://ipinfo.io/json?token=YOUR_TOKEN_HERE',
      'https://geolocation-db.com/json/'
    ];
    
    for (const provider of providers) {
      try {
        const response = await fetch(provider, { timeout: 3000 });
        const data = await response.json();
        
        if (data.latitude && data.longitude) {
          console.log('IP Location from', provider, ':', data);
          return {
            lat: data.latitude,
            lon: data.longitude,
            city: data.city || data.region || data.country_name || "Неизвестно",
            accuracy: data.accuracy || null
          };
        }
      } catch (providerError) {
        console.warn(`Provider ${provider} failed:`, providerError);
        continue;
      }
    }
    
    return null;
  } catch (error) {
    console.error("Ошибка IP-геолокации:", error);
    return null;
  }
}