/**
 * BloomMart Marketplace - Production Vanilla JavaScript
 * Handles search, filtering, category navigation, sorting, cart drawer,
 * B2B/B2P mode switching, wishlist, and mobile drawers.
 */

(function() {
  'use strict';

  // State Management
  const state = {
    products: [],
    filteredProducts: [],
    categories: [],
    activeCategory: 'all',
    searchQuery: '',
    selectedPrices: [],
    selectedQuantities: [],
    selectedColors: [],
    selectedTypes: [],
    selectedAvailability: [],
    sortBy: 'relevance',
    shoppingMode: localStorage.getItem('bloommart_mode') || 'personal', // 'personal' or 'business'
    cart: JSON.parse(localStorage.getItem('bloommart_cart') || '[]'),
    wishlist: JSON.parse(localStorage.getItem('bloommart_wishlist') || '[]'),
  };

  // DOM Elements cache
  let dom = {};

  function init() {
    cacheDom();
    loadCatalogData();
    bindEvents();
    applyShoppingModeUI();
    renderCategories();
    applyFilters();
    updateCartUI();
  }

  function cacheDom() {
    dom = {
      productGrid: document.getElementById('product-grid'),
      productCount: document.getElementById('product-count'),
      emptyState: document.getElementById('empty-state'),
      searchInput: document.getElementById('search-input'),
      searchClearBtn: document.getElementById('search-clear-btn'),
      categoriesContainer: document.getElementById('categories-container'),
      scrollLeftBtn: document.getElementById('scroll-left-btn'),
      scrollRightBtn: document.getElementById('scroll-right-btn'),
      sortSelect: document.getElementById('sort-select'),
      clearFiltersBtn: document.getElementById('clear-filters-btn'),
      sidebarForm: document.getElementById('filter-sidebar-form'),
      mobileFilterDrawer: document.getElementById('mobile-filter-drawer'),
      mobileFilterBackdrop: document.getElementById('mobile-filter-backdrop'),
      openMobileFilterBtn: document.getElementById('open-mobile-filters-btn'),
      closeMobileFilterBtn: document.getElementById('close-mobile-filters-btn'),
      applyMobileFilterBtn: document.getElementById('apply-mobile-filters-btn'),
      clearMobileFilterBtn: document.getElementById('clear-mobile-filters-btn'),
      cartDrawer: document.getElementById('cart-drawer'),
      cartBackdrop: document.getElementById('cart-backdrop'),
      openCartBtn: document.getElementById('open-cart-btn'),
      closeCartBtn: document.getElementById('close-cart-btn'),
      cartBadge: document.getElementById('cart-badge'),
      cartItemsList: document.getElementById('cart-items-list'),
      cartSubtotal: document.getElementById('cart-subtotal'),
      cartTax: document.getElementById('cart-tax'),
      cartTotal: document.getElementById('cart-total'),
      cartEmptyView: document.getElementById('cart-empty-view'),
      cartContentView: document.getElementById('cart-content-view'),
      modePersonalBtn: document.getElementById('mode-personal-btn'),
      modeBusinessBtn: document.getElementById('mode-business-btn'),
      b2bBanner: document.getElementById('b2b-banner'),
      loginModal: document.getElementById('login-modal'),
      loginBackdrop: document.getElementById('login-backdrop'),
      openLoginBtn: document.getElementById('open-login-btn'),
      closeLoginBtn: document.getElementById('close-login-btn'),
      toast: document.getElementById('toast-notification'),
      toastMessage: document.getElementById('toast-message'),
    };
  }

  function loadCatalogData() {
    // Try reading JSON data embedded in page by Django view, otherwise fallback to window.CATALOG_DATA
    const embeddedDataEl = document.getElementById('django-products-data');
    if (embeddedDataEl && embeddedDataEl.textContent.trim()) {
      try {
        state.products = JSON.parse(embeddedDataEl.textContent);
      } catch (e) {
        console.error('Failed to parse embedded Django JSON:', e);
      }
    }

    if (!state.products || state.products.length === 0) {
      if (window.CATALOG_DATA && window.CATALOG_DATA.length > 0) {
        state.products = window.CATALOG_DATA;
      }
    }

    state.filteredProducts = [...state.products];
  }

  function bindEvents() {
    // Search input
    if (dom.searchInput) {
      dom.searchInput.addEventListener('input', debounce(function(e) {
        state.searchQuery = e.target.value.trim().toLowerCase();
        if (dom.searchClearBtn) {
          dom.searchClearBtn.classList.toggle('hidden', state.searchQuery.length === 0);
        }
        applyFilters();
      }, 250));
    }

    if (dom.searchClearBtn) {
      dom.searchClearBtn.addEventListener('click', function() {
        if (dom.searchInput) {
          dom.searchInput.value = '';
          state.searchQuery = '';
          dom.searchClearBtn.classList.add('hidden');
          applyFilters();
        }
      });
    }

    // Category scroll buttons
    if (dom.scrollLeftBtn && dom.categoriesContainer) {
      dom.scrollLeftBtn.addEventListener('click', function() {
        dom.categoriesContainer.scrollBy({ left: -240, behavior: 'smooth' });
      });
    }

    if (dom.scrollRightBtn && dom.categoriesContainer) {
      dom.scrollRightBtn.addEventListener('click', function() {
        dom.categoriesContainer.scrollBy({ left: 240, behavior: 'smooth' });
      });
    }

    // Sort select
    if (dom.sortSelect) {
      dom.sortSelect.addEventListener('change', function(e) {
        state.sortBy = e.target.value;
        applySorting();
        renderProducts();
      });
    }

    // Filter checkboxes in desktop sidebar
    if (dom.sidebarForm) {
      dom.sidebarForm.addEventListener('change', function(e) {
        handleFilterCheckboxChange();
      });
    }

    // Clear filters
    if (dom.clearFiltersBtn) {
      dom.clearFiltersBtn.addEventListener('click', function() {
        resetAllFilters();
      });
    }

    // Mobile filter drawer open/close
    if (dom.openMobileFilterBtn) {
      dom.openMobileFilterBtn.addEventListener('click', openMobileFilters);
    }
    if (dom.closeMobileFilterBtn) {
      dom.closeMobileFilterBtn.addEventListener('click', closeMobileFilters);
    }
    if (dom.mobileFilterBackdrop) {
      dom.mobileFilterBackdrop.addEventListener('click', closeMobileFilters);
    }
    if (dom.clearMobileFilterBtn) {
      dom.clearMobileFilterBtn.addEventListener('click', resetAllFilters);
    }
    if (dom.applyMobileFilterBtn) {
      dom.applyMobileFilterBtn.addEventListener('click', closeMobileFilters);
    }

    // Cart Drawer open/close
    if (dom.openCartBtn) {
      dom.openCartBtn.addEventListener('click', openCart);
    }
    if (dom.closeCartBtn) {
      dom.closeCartBtn.addEventListener('click', closeCart);
    }
    if (dom.cartBackdrop) {
      dom.cartBackdrop.addEventListener('click', closeCart);
    }

    // Login modal open/close
    if (dom.openLoginBtn) {
      dom.openLoginBtn.addEventListener('click', openLoginModal);
    }
    if (dom.closeLoginBtn) {
      dom.closeLoginBtn.addEventListener('click', closeLoginModal);
    }
    if (dom.loginBackdrop) {
      dom.loginBackdrop.addEventListener('click', closeLoginModal);
    }

    // Mode toggles
    if (dom.modePersonalBtn) {
      dom.modePersonalBtn.addEventListener('click', function() {
        setShoppingMode('personal');
      });
    }
    if (dom.modeBusinessBtn) {
      dom.modeBusinessBtn.addEventListener('click', function() {
        setShoppingMode('business');
      });
    }

    // ESC key closes modals/drawers
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape') {
        closeCart();
        closeMobileFilters();
        closeLoginModal();
      }
    });
  }

  // Shopping Mode Switching (Personal vs Business)
  function setShoppingMode(mode) {
    state.shoppingMode = mode;
    localStorage.setItem('bloommart_mode', mode);
    applyShoppingModeUI();
    renderProducts();
    showToast(mode === 'business' ? 'Switched to Business Mode (B2B Bulk Pricing & MOQs Active)' : 'Switched to Personal Mode (Retail Pricing)');
  }

  function applyShoppingModeUI() {
    const isBiz = state.shoppingMode === 'business';

    if (dom.modePersonalBtn && dom.modeBusinessBtn) {
      if (isBiz) {
        dom.modeBusinessBtn.className = 'px-3 py-1 text-xs font-semibold rounded-md bg-emerald-700 text-white shadow-sm transition';
        dom.modePersonalBtn.className = 'px-3 py-1 text-xs font-medium rounded-md text-zinc-600 hover:text-zinc-900 transition';
      } else {
        dom.modePersonalBtn.className = 'px-3 py-1 text-xs font-semibold rounded-md bg-white text-zinc-900 shadow-sm border border-zinc-200 transition';
        dom.modeBusinessBtn.className = 'px-3 py-1 text-xs font-medium rounded-md text-zinc-600 hover:text-zinc-900 transition';
      }
    }

    if (dom.b2bBanner) {
      dom.b2bBanner.classList.toggle('hidden', !isBiz);
    }
  }

  // Filter Handling
  function handleFilterCheckboxChange() {
    const checkedPrices = Array.from(document.querySelectorAll('input[name="filter-price"]:checked')).map(el => el.value);
    const checkedQuantities = Array.from(document.querySelectorAll('input[name="filter-quantity"]:checked')).map(el => el.value);
    const checkedColors = Array.from(document.querySelectorAll('input[name="filter-color"]:checked')).map(el => el.value);
    const checkedTypes = Array.from(document.querySelectorAll('input[name="filter-type"]:checked')).map(el => el.value);
    const checkedAvailability = Array.from(document.querySelectorAll('input[name="filter-availability"]:checked')).map(el => el.value);

    state.selectedPrices = checkedPrices;
    state.selectedQuantities = checkedQuantities;
    state.selectedColors = checkedColors;
    state.selectedTypes = checkedTypes;
    state.selectedAvailability = checkedAvailability;

    applyFilters();
  }

  function resetAllFilters() {
    // Uncheck all inputs in both desktop and mobile forms
    document.querySelectorAll('input[type="checkbox"]').forEach(input => {
      input.checked = false;
    });

    state.selectedPrices = [];
    state.selectedQuantities = [];
    state.selectedColors = [];
    state.selectedTypes = [];
    state.selectedAvailability = [];
    state.searchQuery = '';
    state.activeCategory = 'all';

    if (dom.searchInput) dom.searchInput.value = '';
    if (dom.searchClearBtn) dom.searchClearBtn.classList.add('hidden');
    if (dom.sortSelect) dom.sortSelect.value = 'relevance';
    state.sortBy = 'relevance';

    renderCategories();
    applyFilters();
    showToast('Filters cleared');
  }

  function applyFilters() {
    let list = [...state.products];

    // 1. Category filter
    if (state.activeCategory && state.activeCategory !== 'all') {
      list = list.filter(item => {
        if (state.activeCategory === 'roses') return item.flower_type === 'Roses' || item.category === 'roses';
        if (state.activeCategory === 'bouquets') return item.category === 'bouquets';
        if (state.activeCategory === 'wedding') return item.category === 'wedding';
        if (state.activeCategory === 'birthday') return item.category === 'birthday';
        if (state.activeCategory === 'arrangements') return item.category === 'arrangements';
        if (state.activeCategory === 'plants') return item.category === 'plants';
        if (state.activeCategory === 'corporate') return item.category === 'corporate';
        if (state.activeCategory === 'bulk') return item.category === 'bulk';
        if (state.activeCategory === 'seasonal') return item.category === 'seasonal';
        return item.category === state.activeCategory;
      });
    }

    // 2. Search query filter
    if (state.searchQuery) {
      const q = state.searchQuery;
      list = list.filter(item => {
        return item.name.toLowerCase().includes(q) ||
               item.description.toLowerCase().includes(q) ||
               item.flower_type.toLowerCase().includes(q) ||
               item.color.toLowerCase().includes(q) ||
               (item.badge && item.badge.toLowerCase().includes(q));
      });
    }

    // 3. Price filter
    if (state.selectedPrices.length > 0) {
      list = list.filter(item => {
        const p = state.shoppingMode === 'business' ? item.b2b_price_100 : item.price;
        return state.selectedPrices.some(range => {
          if (range === 'under_500') return p < 500;
          if (range === '500_1000') return p >= 500 && p <= 1000;
          if (range === '1000_2500') return p > 1000 && p <= 2500;
          if (range === 'above_2500') return p > 2500;
          return true;
        });
      });
    }

    // 4. Quantity filter
    if (state.selectedQuantities.length > 0) {
      list = list.filter(item => {
        const qty = item.stem_count || 20;
        return state.selectedQuantities.some(qRange => {
          if (qRange === '1_10') return qty >= 1 && qty <= 10;
          if (qRange === '10_50') return qty > 10 && qty <= 50;
          if (qRange === '50_100') return qty > 50 && qty <= 100;
          if (qRange === '100_plus') return qty >= 100;
          return true;
        });
      });
    }

    // 5. Color filter
    if (state.selectedColors.length > 0) {
      list = list.filter(item => state.selectedColors.includes(item.color));
    }

    // 6. Flower Type filter
    if (state.selectedTypes.length > 0) {
      list = list.filter(item => state.selectedTypes.includes(item.flower_type));
    }

    // 7. Availability filter
    if (state.selectedAvailability.length > 0) {
      list = list.filter(item => state.selectedAvailability.includes(item.availability));
    }

    state.filteredProducts = list;
    applySorting();
    renderProducts();
  }

  function applySorting() {
    const sort = state.sortBy;
    state.filteredProducts.sort((a, b) => {
      const priceA = state.shoppingMode === 'business' ? a.b2b_price_100 : a.price;
      const priceB = state.shoppingMode === 'business' ? b.b2b_price_100 : b.price;

      if (sort === 'price_asc') {
        return priceA - priceB;
      } else if (sort === 'price_desc') {
        return priceB - priceA;
      } else if (sort === 'popularity') {
        return (b.popularity || 0) - (a.popularity || 0);
      } else if (sort === 'newest') {
        return (b.is_new ? 1 : 0) - (a.is_new ? 1 : 0);
      } else {
        // Default relevance (rating * reviews)
        return (b.rating * b.reviews) - (a.rating * a.reviews);
      }
    });
  }

  // Render Product Grid
  function renderProducts() {
    if (!dom.productGrid) return;

    if (dom.productCount) {
      const count = state.filteredProducts.length;
      dom.productCount.textContent = `${count} ${count === 1 ? 'product' : 'products'}`;
    }

    if (state.filteredProducts.length === 0) {
      dom.productGrid.classList.add('hidden');
      if (dom.emptyState) dom.emptyState.classList.remove('hidden');
      return;
    }

    dom.productGrid.classList.remove('hidden');
    if (dom.emptyState) dom.emptyState.classList.add('hidden');

    const isBiz = state.shoppingMode === 'business';

    dom.productGrid.innerHTML = state.filteredProducts.map(product => {
      const isWishlisted = state.wishlist.includes(product.id);
      const isPreOrder = product.availability === 'pre_order';
      
      // Personal mode pricing
      const retailPrice = product.price;
      const origPrice = product.original_price;
      const discountPct = origPrice > retailPrice ? Math.round(((origPrice - retailPrice) / origPrice) * 100) : 0;

      // Business mode pricing
      const b2bMoq = product.b2b_moq || 50;
      const b2b100 = product.b2b_price_100;
      const b2b500 = product.b2b_price_500;

      return `
        <article class="product-card group relative bg-white rounded-2xl border border-zinc-200/90 flex flex-col justify-between overflow-hidden shadow-sm hover:border-emerald-300">
          
          <!-- Image Container -->
          <div class="relative w-full aspect-square bg-zinc-100 overflow-hidden">
            <img 
              src="${product.image}" 
              alt="${escapeHtml(product.name)}" 
              loading="lazy"
              onerror="this.src='https://images.unsplash.com/photo-1518709268805-4e9042af9f23?auto=format&fit=crop&w=600&q=80'"
              class="product-card-image w-full h-full object-cover"
            />

            <!-- Top Badges -->
            <div class="absolute top-2.5 left-2.5 flex flex-col gap-1 z-10">
              ${product.badge ? `
                <span class="inline-flex items-center px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider rounded-md bg-zinc-900/80 backdrop-blur-sm text-white shadow-xs">
                  ${product.badge}
                </span>
              ` : ''}
              ${isBiz ? `
                <span class="inline-flex items-center px-2 py-0.5 text-[11px] font-semibold rounded-md bg-emerald-700 text-white shadow-xs">
                  B2B Tier
                </span>
              ` : ''}
            </div>

            <!-- Wishlist Button -->
            <button 
              type="button" 
              class="wishlist-btn absolute top-2.5 right-2.5 w-8 h-8 rounded-full bg-white/90 hover:bg-white text-zinc-600 hover:text-red-500 shadow-sm flex items-center justify-center transition ${isWishlisted ? 'active text-red-500' : ''}"
              data-product-id="${product.id}"
              aria-label="Add to wishlist"
            >
              <svg class="w-4 h-4 transition" fill="${isWishlisted ? '#ef4444' : 'none'}" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
              </svg>
            </button>

            <!-- Availability Tag -->
            <div class="absolute bottom-2 left-2.5 z-10">
              <span class="inline-flex items-center gap-1.5 px-2 py-0.5 text-[11px] font-medium rounded-full ${isPreOrder ? 'bg-amber-100 text-amber-800' : 'bg-emerald-50 text-emerald-800 border border-emerald-200/60'}">
                <span class="w-1.5 h-1.5 rounded-full ${isPreOrder ? 'bg-amber-500' : 'bg-emerald-600'}"></span>
                ${isPreOrder ? 'Pre-order' : 'In Stock'}
              </span>
            </div>
          </div>

          <!-- Product Details -->
          <div class="p-3.5 sm:p-4 flex-1 flex flex-col justify-between">
            <div>
              <!-- Flower Type & Rating -->
              <div class="flex items-center justify-between text-xs text-zinc-500 mb-1">
                <span class="font-medium text-emerald-800 bg-emerald-50/70 px-1.5 py-0.5 rounded text-[11px]">
                  ${product.flower_type}
                </span>
                <div class="flex items-center gap-1">
                  <svg class="w-3.5 h-3.5 text-amber-400 fill-current" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                  </svg>
                  <span class="font-semibold text-zinc-700">${product.rating}</span>
                  <span class="text-zinc-400">(${product.reviews})</span>
                </div>
              </div>

              <!-- Product Name -->
              <h3 class="font-semibold text-zinc-900 text-sm sm:text-base leading-snug line-clamp-1 group-hover:text-emerald-700 transition">
                ${escapeHtml(product.name)}
              </h3>

              <!-- Short Description -->
              <p class="text-xs text-zinc-500 mt-1 line-clamp-2 leading-relaxed">
                ${escapeHtml(product.description)}
              </p>
            </div>

            <!-- Pricing Section -->
            <div class="mt-3 pt-3 border-t border-zinc-100">
              ${isBiz ? `
                <!-- B2B Pricing Structure -->
                <div class="space-y-1.5 bg-zinc-50 p-2.5 rounded-lg border border-zinc-200/80 mb-3">
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-zinc-500 font-medium">MOQ:</span>
                    <span class="font-bold text-zinc-800">${b2bMoq} stems</span>
                  </div>
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-zinc-500">100+ units:</span>
                    <span class="font-bold text-emerald-700">₹${b2b100.toLocaleString('en-IN')}</span>
                  </div>
                  <div class="flex items-center justify-between text-xs">
                    <span class="text-zinc-500">500+ units:</span>
                    <span class="font-bold text-emerald-800">₹${b2b500.toLocaleString('en-IN')}</span>
                  </div>
                </div>
              ` : `
                <!-- Retail Pricing -->
                <div class="flex items-baseline gap-2 mb-1">
                  <span class="text-lg sm:text-xl font-bold text-zinc-900">
                    ₹${retailPrice.toLocaleString('en-IN')}
                  </span>
                  ${origPrice > retailPrice ? `
                    <span class="text-xs text-zinc-400 line-through">
                      ₹${origPrice.toLocaleString('en-IN')}
                    </span>
                    <span class="text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                      ${discountPct}% off
                    </span>
                  ` : ''}
                </div>
                <div class="text-[11px] text-zinc-500 mb-3">
                  ${escapeHtml(product.pricing_unit || 'per unit')}
                </div>
              `}

              <!-- Quantity Selector & Action Button -->
              <div class="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
                <!-- Counter -->
                <div class="inline-flex items-center justify-between border border-zinc-200 rounded-lg bg-zinc-50 p-0.5 shrink-0">
                  <button 
                    type="button" 
                    class="qty-decrement w-7 h-7 flex items-center justify-center rounded text-zinc-600 hover:bg-white hover:text-zinc-900 transition active:scale-95"
                    data-product-id="${product.id}"
                    aria-label="Decrease quantity"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M20 12H4"/></svg>
                  </button>
                  <span 
                    id="card-qty-${product.id}" 
                    class="w-8 text-center text-xs font-semibold text-zinc-800 select-none"
                  >
                    ${isBiz ? b2bMoq : 1}
                  </span>
                  <button 
                    type="button" 
                    class="qty-increment w-7 h-7 flex items-center justify-center rounded text-zinc-600 hover:bg-white hover:text-zinc-900 transition active:scale-95"
                    data-product-id="${product.id}"
                    aria-label="Increase quantity"
                  >
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 4v16m8-8H4"/></svg>
                  </button>
                </div>

                <!-- Add to Cart or Request Quote Button -->
                <button 
                  type="button" 
                  class="add-to-cart-btn flex-1 py-2 px-3 text-xs sm:text-sm font-semibold rounded-lg ${isBiz ? 'bg-zinc-900 hover:bg-zinc-800 text-white' : 'bg-emerald-700 hover:bg-emerald-800 text-white'} shadow-xs flex items-center justify-center gap-1.5 transition active:scale-[0.98]"
                  data-product-id="${product.id}"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"/>
                  </svg>
                  <span>${isBiz ? 'Add Bulk Order' : 'Add to Cart'}</span>
                </button>
              </div>

              ${isBiz ? `
                <button 
                  type="button" 
                  class="quote-btn w-full mt-2 py-1 text-center text-[11px] font-medium text-emerald-700 hover:text-emerald-800 hover:underline"
                  data-product-id="${product.id}"
                >
                  Request Bulk Quote with GST
                </button>
              ` : ''}

            </div>
          </div>
        </article>
      `;
    }).join('');

    bindProductCardActions();
  }

  // Bind interactions on rendered cards
  function bindProductCardActions() {
    // Quantity increment & decrement
    document.querySelectorAll('.qty-decrement').forEach(btn => {
      btn.onclick = function() {
        const id = parseInt(btn.getAttribute('data-product-id'), 10);
        const qtyEl = document.getElementById(`card-qty-${id}`);
        if (!qtyEl) return;
        let val = parseInt(qtyEl.textContent, 10);
        const isBiz = state.shoppingMode === 'business';
        const product = state.products.find(p => p.id === id);
        const minVal = isBiz ? (product.b2b_moq || 50) : 1;
        const step = isBiz ? 25 : 1;

        if (val - step >= minVal) {
          qtyEl.textContent = val - step;
        } else {
          qtyEl.textContent = minVal;
        }
      };
    });

    document.querySelectorAll('.qty-increment').forEach(btn => {
      btn.onclick = function() {
        const id = parseInt(btn.getAttribute('data-product-id'), 10);
        const qtyEl = document.getElementById(`card-qty-${id}`);
        if (!qtyEl) return;
        let val = parseInt(qtyEl.textContent, 10);
        const isBiz = state.shoppingMode === 'business';
        const step = isBiz ? 50 : 1;
        qtyEl.textContent = val + step;
      };
    });

    // Add to cart buttons
    document.querySelectorAll('.add-to-cart-btn').forEach(btn => {
      btn.onclick = function() {
        const id = parseInt(btn.getAttribute('data-product-id'), 10);
        const qtyEl = document.getElementById(`card-qty-${id}`);
        const qty = qtyEl ? parseInt(qtyEl.textContent, 10) : 1;
        addToCart(id, qty);
      };
    });

    // Wishlist buttons
    document.querySelectorAll('.wishlist-btn').forEach(btn => {
      btn.onclick = function() {
        const id = parseInt(btn.getAttribute('data-product-id'), 10);
        toggleWishlist(id, btn);
      };
    });

    // Request Bulk Quote
    document.querySelectorAll('.quote-btn').forEach(btn => {
      btn.onclick = function() {
        const id = parseInt(btn.getAttribute('data-product-id'), 10);
        const product = state.products.find(p => p.id === id);
        if (product) {
          openLoginModal();
          showToast(`Inquiring B2B wholesale quotation for ${product.name}`);
        }
      };
    });
  }

  // Categories strip rendering
  function renderCategories() {
    if (!dom.categoriesContainer) return;

    // Use embedded categories or fallback array
    const categories = [
      { id: 'all', name: 'All Flowers', icon: 'flower' },
      { id: 'roses', name: 'Roses', icon: 'heart' },
      { id: 'bouquets', name: 'Bouquets', icon: 'gift' },
      { id: 'wedding', name: 'Wedding Flowers', icon: 'sparkles' },
      { id: 'birthday', name: 'Birthday Flowers', icon: 'cake' },
      { id: 'arrangements', name: 'Floral Arrangements', icon: 'palette' },
      { id: 'plants', name: 'Plants', icon: 'leaf' },
      { id: 'corporate', name: 'Corporate Gifting', icon: 'briefcase' },
      { id: 'bulk', name: 'Bulk Flowers', icon: 'boxes' },
      { id: 'seasonal', name: 'Seasonal Flowers', icon: 'sun' }
    ];

    dom.categoriesContainer.innerHTML = categories.map(cat => {
      const isActive = state.activeCategory === cat.id;
      return `
        <button 
          type="button" 
          class="category-pill shrink-0 flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-medium border transition select-none ${
            isActive 
              ? 'bg-emerald-800 text-white border-emerald-800 shadow-xs' 
              : 'bg-white text-zinc-700 border-zinc-200 hover:border-zinc-300 hover:bg-zinc-50'
          }"
          data-category-id="${cat.id}"
        >
          <span>${escapeHtml(cat.name)}</span>
        </button>
      `;
    }).join('');

    dom.categoriesContainer.querySelectorAll('.category-pill').forEach(btn => {
      btn.onclick = function() {
        const catId = btn.getAttribute('data-category-id');
        state.activeCategory = catId;
        renderCategories();
        applyFilters();
      };
    });
  }

  // Wishlist handler
  function toggleWishlist(productId, btnEl) {
    const idx = state.wishlist.indexOf(productId);
    if (idx > -1) {
      state.wishlist.splice(idx, 1);
      btnEl.classList.remove('active', 'text-red-500');
      btnEl.querySelector('svg').setAttribute('fill', 'none');
      showToast('Removed from favorites');
    } else {
      state.wishlist.push(productId);
      btnEl.classList.add('active', 'text-red-500');
      btnEl.querySelector('svg').setAttribute('fill', '#ef4444');
      showToast('Saved to your favorites');
    }
    localStorage.setItem('bloommart_wishlist', JSON.stringify(state.wishlist));
  }

  // Cart operations
  function addToCart(productId, quantity) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    const isBiz = state.shoppingMode === 'business';
    const effectivePrice = isBiz 
      ? (quantity >= 500 ? product.b2b_price_500 : product.b2b_price_100)
      : product.price;

    const existingIndex = state.cart.findIndex(item => item.id === productId && item.isB2B === isBiz);

    if (existingIndex > -1) {
      state.cart[existingIndex].quantity += quantity;
      state.cart[existingIndex].price = effectivePrice;
    } else {
      state.cart.push({
        id: product.id,
        name: product.name,
        price: effectivePrice,
        original_price: product.price,
        image: product.image,
        pricing_unit: product.pricing_unit,
        quantity: quantity,
        isB2B: isBiz
      });
    }

    localStorage.setItem('bloommart_cart', JSON.stringify(state.cart));
    updateCartUI();
    showToast(`Added ${quantity} × ${product.name} to cart`);
    openCart();
  }

  function updateCartItemQty(index, newQty) {
    if (newQty <= 0) {
      state.cart.splice(index, 1);
    } else {
      state.cart[index].quantity = newQty;
    }
    localStorage.setItem('bloommart_cart', JSON.stringify(state.cart));
    updateCartUI();
  }

  function removeCartItem(index) {
    state.cart.splice(index, 1);
    localStorage.setItem('bloommart_cart', JSON.stringify(state.cart));
    updateCartUI();
    showToast('Item removed from cart');
  }

  function updateCartUI() {
    const totalItems = state.cart.reduce((sum, item) => sum + item.quantity, 0);

    // Badge in header
    if (dom.cartBadge) {
      dom.cartBadge.textContent = totalItems;
      dom.cartBadge.classList.toggle('hidden', totalItems === 0);
      dom.cartBadge.classList.remove('scale-125');
      setTimeout(() => dom.cartBadge.classList.add('scale-125'), 10);
      setTimeout(() => dom.cartBadge.classList.remove('scale-125'), 200);
    }

    // Cart drawer content
    if (!dom.cartItemsList) return;

    if (state.cart.length === 0) {
      if (dom.cartContentView) dom.cartContentView.classList.add('hidden');
      if (dom.cartEmptyView) dom.cartEmptyView.classList.remove('hidden');
      return;
    }

    if (dom.cartEmptyView) dom.cartEmptyView.classList.add('hidden');
    if (dom.cartContentView) dom.cartContentView.classList.remove('hidden');

    let subtotal = 0;

    dom.cartItemsList.innerHTML = state.cart.map((item, index) => {
      const itemSubtotal = item.price * item.quantity;
      subtotal += itemSubtotal;

      return `
        <div class="flex items-center gap-3 p-3 bg-zinc-50/80 rounded-xl border border-zinc-200/80">
          <img src="${item.image}" alt="${escapeHtml(item.name)}" class="w-16 h-16 rounded-lg object-cover bg-zinc-200 shrink-0">
          <div class="flex-1 min-w-0">
            <h4 class="text-xs sm:text-sm font-semibold text-zinc-900 truncate">${escapeHtml(item.name)}</h4>
            <div class="text-xs text-zinc-500 mt-0.5">
              ₹${item.price.toLocaleString('en-IN')} ${item.isB2B ? '<span class="text-emerald-700 font-bold">(B2B Rate)</span>' : ''}
            </div>
            
            <div class="flex items-center justify-between mt-2">
              <div class="inline-flex items-center border border-zinc-200 rounded-md bg-white p-0.5">
                <button type="button" class="w-6 h-6 flex items-center justify-center text-zinc-600 hover:text-zinc-900" onclick="window.BloomMart.updateQty(${index}, ${item.quantity - 1})">-</button>
                <span class="w-7 text-center text-xs font-semibold text-zinc-800">${item.quantity}</span>
                <button type="button" class="w-6 h-6 flex items-center justify-center text-zinc-600 hover:text-zinc-900" onclick="window.BloomMart.updateQty(${index}, ${item.quantity + 1})">+</button>
              </div>
              <span class="text-xs sm:text-sm font-bold text-zinc-900">₹${itemSubtotal.toLocaleString('en-IN')}</span>
            </div>
          </div>
          <button type="button" class="p-1.5 text-zinc-400 hover:text-red-500 rounded-md transition" onclick="window.BloomMart.removeItem(${index})" aria-label="Remove item">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg>
          </button>
        </div>
      `;
    }).join('');

    // Tax & Totals calculation
    const tax = Math.round(subtotal * 0.05); // 5% GST on flowers in India
    const delivery = subtotal > 1500 ? 0 : 99;
    const grandTotal = subtotal + tax + delivery;

    if (dom.cartSubtotal) dom.cartSubtotal.textContent = `₹${subtotal.toLocaleString('en-IN')}`;
    if (dom.cartTax) dom.cartTax.textContent = `₹${tax.toLocaleString('en-IN')}`;
    if (dom.cartTotal) dom.cartTotal.textContent = `₹${grandTotal.toLocaleString('en-IN')}`;
  }

  // Drawers & Modals
  function openCart() {
    if (!dom.cartDrawer) return;
    dom.cartDrawer.classList.remove('pointer-events-none');
    dom.cartBackdrop.classList.remove('opacity-0');
    dom.cartDrawer.querySelector('.drawer-panel').classList.remove('translate-x-full');
    document.body.classList.add('overflow-hidden');
  }

  function closeCart() {
    if (!dom.cartDrawer) return;
    dom.cartBackdrop.classList.add('opacity-0');
    dom.cartDrawer.querySelector('.drawer-panel').classList.add('translate-x-full');
    setTimeout(() => {
      dom.cartDrawer.classList.add('pointer-events-none');
      document.body.classList.remove('overflow-hidden');
    }, 300);
  }

  function openMobileFilters() {
    if (!dom.mobileFilterDrawer) return;
    dom.mobileFilterDrawer.classList.remove('pointer-events-none');
    dom.mobileFilterBackdrop.classList.remove('opacity-0');
    dom.mobileFilterDrawer.querySelector('.drawer-panel').classList.remove('translate-x-full');
    document.body.classList.add('overflow-hidden');
  }

  function closeMobileFilters() {
    if (!dom.mobileFilterDrawer) return;
    dom.mobileFilterBackdrop.classList.add('opacity-0');
    dom.mobileFilterDrawer.querySelector('.drawer-panel').classList.add('translate-x-full');
    setTimeout(() => {
      dom.mobileFilterDrawer.classList.add('pointer-events-none');
      document.body.classList.remove('overflow-hidden');
    }, 300);
  }

  function openLoginModal() {
    if (!dom.loginModal) return;
    dom.loginModal.classList.remove('pointer-events-none');
    dom.loginBackdrop.classList.remove('opacity-0');
    dom.loginModal.querySelector('.modal-panel').classList.remove('scale-95', 'opacity-0');
    document.body.classList.add('overflow-hidden');
  }

  function closeLoginModal() {
    if (!dom.loginModal) return;
    dom.loginBackdrop.classList.add('opacity-0');
    dom.loginModal.querySelector('.modal-panel').classList.add('scale-95', 'opacity-0');
    setTimeout(() => {
      dom.loginModal.classList.add('pointer-events-none');
      document.body.classList.remove('overflow-hidden');
    }, 300);
  }

  // Notification toast
  function showToast(message) {
    if (!dom.toast || !dom.toastMessage) return;
    dom.toastMessage.textContent = message;
    dom.toast.classList.remove('translate-y-24', 'opacity-0');
    clearTimeout(dom.toastTimer);
    dom.toastTimer = setTimeout(() => {
      dom.toast.classList.add('translate-y-24', 'opacity-0');
    }, 3000);
  }

  // Utilities
  function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  function escapeHtml(string) {
    if (!string) return '';
    return String(string)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  // Expose global methods for inline HTML onclick calls
  window.BloomMart = {
    updateQty: updateCartItemQty,
    removeItem: removeCartItem,
    openCart: openCart,
    closeCart: closeCart,
    openMobileFilters: openMobileFilters,
    closeMobileFilters: closeMobileFilters,
    openLoginModal: openLoginModal,
    closeLoginModal: closeLoginModal,
    setShoppingMode: setShoppingMode,
    resetFilters: resetAllFilters
  };

  // Run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
