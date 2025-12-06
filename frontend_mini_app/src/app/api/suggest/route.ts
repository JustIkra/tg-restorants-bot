export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q');
  
  if (!query || query.length < 2) {
    return Response.json({ results: [] });
  }
  
  try {
    const DADATA_API_KEY = "ваш_ключ_dadata_или_просто_используем_OpenStreetMap";
    const response = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&addressdetails=1&limit=7&countrycodes=ru&accept-language=ru`,
      {
        headers: {
          'Accept': 'application/json',
          'User-Agent': 'FoodDeliveryApp/1.0'
        }
      }
    );
    
    if (!response.ok) {
      throw new Error(`OSM API error: ${response.status}`);
    }
    
    const data = await response.json();
    
    const suggestions = data.map((item: any) => {
      const address = item.address || {};
 
      let title = '';
      if (address.road) {
        title = address.road;
        if (address.house_number) {
          title += `, д. ${address.house_number}`;
        }
      } else {
        title = item.display_name.split(',')[0];
      }
      
      let subtitle = address.city || address.town || address.village || '';
      if (address.state) {
        subtitle = subtitle ? `${subtitle}, ${address.state}` : address.state;
      }
      
      return {
        title: title || item.display_name,
        subtitle: subtitle || '',
        fullAddress: subtitle ? `${title}, ${subtitle}` : title
      };
    }).filter((item: any) => item.title);
    
    if (suggestions.length < 3) {
      const localSuggestions = getLocalSuggestions(query);
      suggestions.push(...localSuggestions.slice(0, 3 - suggestions.length));
    }

    const uniqueSuggestions = suggestions.filter((item: any, index: number, self: any[]) =>
      index === self.findIndex((t: any) => t.fullAddress === item.fullAddress)
    );
    
    return Response.json({ results: uniqueSuggestions.slice(0, 5) });
    
  } catch (error) {
    console.error('API error:', error);
    const localSuggestions = getLocalSuggestions(query || '');
    return Response.json({ 
      results: localSuggestions,
      fallback: true 
    });
  }
}
function getLocalSuggestions(query: string): any[] {
  const localSuggestions = [
    { 
      title: "ул. Ленина", 
      subtitle: "Москва", 
      fullAddress: "ул. Ленина, Москва" 
    },
    { 
      title: "пр. Ленина", 
      subtitle: "Санкт-Петербург", 
      fullAddress: "пр. Ленина, Санкт-Петербург" 
    },
    { 
      title: "пр. Победы", 
      subtitle: "Санкт-Петербург", 
      fullAddress: "пр. Победы, Санкт-Петербург" 
    },
    { 
      title: "ул. Мира", 
      subtitle: "Екатеринбург", 
      fullAddress: "ул. Мира, Екатеринбург" 
    },
    { 
      title: "ул. Советская", 
      subtitle: "Москва", 
      fullAddress: "ул. Советская, Москва" 
    },
    { 
      title: "ул. Центральная", 
      subtitle: "Москва", 
      fullAddress: "ул. Центральная, Москва" 
    },
    { 
      title: "ул. Гагарина", 
      subtitle: "Москва", 
      fullAddress: "ул. Гагарина, Москва" 
    },
    { 
      title: "ул. Кирова", 
      subtitle: "Санкт-Петербург", 
      fullAddress: "ул. Кирова, Санкт-Петербург" 
    },
    { 
      title: "ул. Пушкина", 
      subtitle: "Москва", 
      fullAddress: "ул. Пушкина, Москва" 
    },
  ];
  
  const normalizedQuery = query.toLowerCase().trim();
  
  return localSuggestions
    .filter(item => 
      item.fullAddress.toLowerCase().includes(normalizedQuery) ||
      item.title.toLowerCase().includes(normalizedQuery) ||
      item.subtitle.toLowerCase().includes(normalizedQuery)
    )
    .slice(0, 7);
}