/* Pure Flora demo catalogue. Backend data replaces this fallback when the API is reachable. */
window.PF_PRODUCTS = [
 {id:"rose-blush",name:"Blush Garden Roses",category:"Roses",price:250,unit:"bunch of 20",stock:48,grower:"Meadow & Stem Farm",tag:"Bestseller",color:"pink",image:"https://images.unsplash.com/photo-1494972308805-463bc619d34e?auto=format&fit=crop&w=900&q=85",description:"Soft blush petals with a beautifully classic silhouette."},
 {id:"rose-red",name:"Velvet Red Roses",category:"Roses",price:280,unit:"bunch of 20",stock:32,grower:"Rosewood Gardens",tag:"Loved",color:"red",image:"https://images.unsplash.com/photo-1518895949257-7621c3c786d7?auto=format&fit=crop&w=900&q=85",description:"Rich red roses for bold, timeless arrangements."},
 {id:"lily-white",name:"White Oriental Lilies",category:"Lilies",price:350,unit:"bunch of 10",stock:22,grower:"Meadow & Stem Farm",tag:"Elegant",color:"white",image:"https://images.unsplash.com/photo-1561181286-d3fee7d55364?auto=format&fit=crop&w=900&q=85",description:"Graceful white lilies with a fresh, clean finish."},
 {id:"marigold-gold",name:"Golden Marigolds",category:"Marigolds",price:120,unit:"bunch of 50",stock:80,grower:"Sunpatch Collective",tag:"Seasonal",color:"yellow",image:"https://images.unsplash.com/photo-1606041008023-472dfb5e530f?auto=format&fit=crop&w=900&q=85",description:"Sunshine-bright golden blooms, ideal for celebrations."},
 {id:"tulip-pink",name:"Pink Parrot Tulips",category:"Seasonal",price:320,unit:"bunch of 10",stock:18,grower:"Petal Lane Farm",tag:"Limited",color:"pink",image:"https://images.unsplash.com/photo-1520763185298-1b434c919102?auto=format&fit=crop&w=900&q=85",description:"Sculptural, ruffled tulips with a soft spring feeling."},
 {id:"gerbera-mix",name:"Sunrise Gerbera Mix",category:"Seasonal",price:180,unit:"bunch of 15",stock:40,grower:"Sunpatch Collective",tag:"Colourful",color:"mixed",image:"https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=85",description:"A cheerful mix of bright, long-lasting gerberas."},
 {id:"orchid-purple",name:"Purple Dendrobium Orchids",category:"Exotic",price:420,unit:"bunch of 10",stock:12,grower:"Orchid House",tag:"Premium",color:"purple",image:"https://images.unsplash.com/photo-1566907225472-4a9a4f1a9b4a?auto=format&fit=crop&w=900&q=85",description:"Distinctive orchid stems for elevated floral designs."},
 {id:"baby-breath",name:"Cloud Baby's Breath",category:"Seasonal",price:200,unit:"bunch of 10",stock:28,grower:"Petal Lane Farm",tag:"Florist pick",color:"white",image:"https://images.unsplash.com/photo-1525310072745-f49212b5ac6d?auto=format&fit=crop&w=900&q=85",description:"Airy little white flowers for delicate arrangements."},
 {id:"lotus-pink",name:"Pink Lotus Stems",category:"Exotic",price:300,unit:"bunch of 10",stock:14,grower:"Riverbend Flowers",tag:"Specialty",color:"pink",image:"https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=900&q=85",description:"A striking specialty bloom with a serene, sculptural look."},
 {id:"chrysanthemum",name:"Cream Chrysanthemums",category:"Seasonal",price:160,unit:"bunch of 15",stock:36,grower:"Meadow & Stem Farm",tag:"Everyday",color:"cream",image:"https://images.unsplash.com/photo-1508610048659-a06b669e3321?auto=format&fit=crop&w=900&q=85",description:"Full, soft blooms that bring texture to every bunch."},
 {id:"rose-peach",name:"Peach Garden Roses",category:"Roses",price:270,unit:"bunch of 20",stock:26,grower:"Rosewood Gardens",tag:"New season",color:"peach",image:"https://images.unsplash.com/photo-1494972308805-463bc619d34e?auto=format&fit=crop&w=900&q=85",description:"Warm peach roses with a gentle, romantic tone."},
 {id:"carnation",name:"Soft Pink Carnations",category:"Seasonal",price:140,unit:"bunch of 20",stock:0,grower:"Petal Lane Farm",tag:"Restocking",color:"pink",image:"https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=85",description:"Ruffled pink petals with a long-lasting vase life."}
];
window.PF_CURRENCY = new Intl.NumberFormat("en-IN", {style:"currency",currency:"INR",maximumFractionDigits:0});
window.PF_FORMAT = value => window.PF_CURRENCY.format(value);
window.PF_API_BASE = window.PF_API_BASE || "http://127.0.0.1:8000/api";
window.PF_PRODUCTS_READY = fetch(`${window.PF_API_BASE}/products/`)
  .then(response => {
    if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
    return response.json();
  })
  .then(products => {
    if (!Array.isArray(products)) throw new Error("Catalog API returned an unexpected response.");
    window.PF_PRODUCTS = products;
    window.dispatchEvent(new Event("pf:products-updated"));
    return products;
  })
  .catch(error => {
    console.info("Using the sample flower catalogue until the Django API is available.", error);
    return window.PF_PRODUCTS;
  });
