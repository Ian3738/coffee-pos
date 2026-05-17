/**
 * 晤光咖啡 — 共用資料層
 * 用 localStorage 取代後端資料庫,讓專案能部署到 GitHub Pages
 *
 * 提供的 API 與 Flask 版本對應:
 *   db.getMenu()                        ↔ GET  /api/menu (僅上架)
 *   db.getAllMenu()                     ↔ GET  /api/admin/menu
 *   db.createMenuItem(item)             ↔ POST /api/admin/menu
 *   db.updateMenuItem(id, patch)        ↔ PUT  /api/admin/menu/<id>
 *   db.deleteMenuItem(id)               ↔ DELETE /api/admin/menu/<id>
 *   db.createOrder({items, cash})       ↔ POST /api/orders
 *   db.getOrders({status, date})        ↔ GET  /api/admin/orders
 *   db.updateOrderStatus(id, status)    ↔ PUT  /api/admin/orders/<id>/status
 *   db.getStats()                       ↔ GET  /api/admin/stats
 *   db.exportAll() / db.importAll(json) / db.resetAll()
 */
(function () {
  'use strict';

  const KEYS = {
    menu:   'cafe.menu',
    orders: 'cafe.orders',
    seq:    'cafe.seq',
  };

  // ====== 預設菜單 ======
  // 圖片來源:Unsplash (免費商用,無需註明)
  const IMG = id => `https://images.unsplash.com/photo-${id}?w=600&h=400&fit=crop&auto=format&q=80`;
  const DEFAULT_MENU = [
    { category: '咖啡', icon: '☕', name: '濃縮咖啡',     description: '單份義式濃縮',       base_price: 60,  customizable: 1, has_temp: 0, has_sweet: 0, image_url: IMG('1510707577719-ae7c14805e3a') },
    { category: '咖啡', icon: '☕', name: '美式咖啡',     description: '濃縮加熱水',         base_price: 75,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1497935586351-b67a49e012bf') },
    { category: '咖啡', icon: '🥛', name: '拿鐵',         description: '濃縮配蒸奶,綿密奶香', base_price: 90,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1561882468-9110e03e0f78') },
    { category: '咖啡', icon: '☕', name: '卡布奇諾',     description: '經典奶泡咖啡',       base_price: 90,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1572442388796-11668a67e53d') },
    { category: '咖啡', icon: '🍫', name: '摩卡',         description: '巧克力與咖啡的融合', base_price: 100, customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1542990253-0d0f5be5f0ed') },
    { category: '咖啡', icon: '🍯', name: '焦糖瑪奇朵',   description: '焦糖香氣濃郁',       base_price: 110, customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1517701604599-bb29b565090c') },
    { category: '茶飲', icon: '🍵', name: '英式紅茶',     description: '錫蘭紅茶',           base_price: 60,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1597481499750-3e6b22637e12') },
    { category: '茶飲', icon: '🍵', name: '日式煎茶',     description: '甘醇綠茶',           base_price: 70,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1564890369478-c89ca6d9cde9') },
    { category: '茶飲', icon: '🥛', name: '鮮奶茶',       description: '紅茶配上鮮奶',       base_price: 85,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1517256064527-09c73fc73e38') },
    { category: '茶飲', icon: '🍑', name: '水蜜桃水果茶', description: '果香繽紛',           base_price: 95,  customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1570696516188-ade861b84a49') },
    { category: '特調', icon: '🍫', name: '熱可可',       description: '醇厚比利時可可',     base_price: 95,  customizable: 1, has_temp: 0, has_sweet: 0, image_url: IMG('1534687941688-651ccaafbff8') },
    { category: '特調', icon: '🍵', name: '抹茶拿鐵',     description: '京都宇治抹茶',       base_price: 110, customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1515823064-d6e0c04616a7') },
    { category: '特調', icon: '🌾', name: '燕麥拿鐵',     description: '植物奶 · 低負擔',    base_price: 120, customizable: 1, has_temp: 1, has_sweet: 1, image_url: IMG('1568649929103-28ffbefaca1e') },
    { category: '點心', icon: '🥐', name: '法式可頌',     description: '層次酥香',           base_price: 55,  customizable: 0, has_temp: 0, has_sweet: 0, image_url: IMG('1555507036-ab1f4038808a') },
    { category: '點心', icon: '🍰', name: '提拉米蘇',     description: '經典義式甜點',       base_price: 120, customizable: 0, has_temp: 0, has_sweet: 0, image_url: IMG('1571877227200-a0d98ea607e9') },
    { category: '點心', icon: '🧀', name: '紐約起司蛋糕', description: '濃郁起司風味',       base_price: 130, customizable: 0, has_temp: 0, has_sweet: 0, image_url: IMG('1567171466295-4afa63d45416') },
    { category: '點心', icon: '🍪', name: '巧克力餅乾',   description: '手工烘焙',           base_price: 45,  customizable: 0, has_temp: 0, has_sweet: 0, image_url: IMG('1499636136210-6f4ee915583e') },
    { category: '點心', icon: '🥯', name: '原味貝果',     description: '紐約風味',           base_price: 65,  customizable: 0, has_temp: 0, has_sweet: 0, image_url: IMG('1517433367423-c7e5b0f35086') },
  ];

  // ====== 內部 ======
  function read(key, def) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : def;
    } catch (e) {
      console.error('localStorage 讀取失敗', key, e);
      return def;
    }
  }

  function write(key, val) {
    localStorage.setItem(key, JSON.stringify(val));
  }

  function nextId(name) {
    const seq = read(KEYS.seq, {});
    seq[name] = (seq[name] || 0) + 1;
    write(KEYS.seq, seq);
    return seq[name];
  }

  function nowLocal() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  }

  function todayStr() {
    const d = new Date();
    const pad = n => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
  }

  function ensureSeeded() {
    const menu = read(KEYS.menu, null);
    if (menu === null) {
      const seeded = DEFAULT_MENU.map((m, i) => ({
        id: i + 1,
        ...m,
        is_available: 1,
        sort_order: i,
        created_at: nowLocal(),
      }));
      write(KEYS.menu, seeded);
      write(KEYS.seq, { menu: seeded.length, order: 0 });
    } else {
      // 遷移:舊版菜單可能缺 image_url,從 DEFAULT_MENU 依品名補回
      const byName = new Map(DEFAULT_MENU.map(d => [d.name, d.image_url]));
      let patched = 0;
      for (const m of menu) {
        if (!m.image_url && byName.has(m.name)) {
          m.image_url = byName.get(m.name);
          patched++;
        }
      }
      if (patched > 0) {
        write(KEYS.menu, menu);
        console.log(`[菜單遷移] 補上 ${patched} 張照片`);
      }
    }
  }

  // ====== 菜單 ======
  function getAllMenu() {
    ensureSeeded();
    const menu = read(KEYS.menu, []);
    return [...menu].sort((a, b) => {
      if (a.category !== b.category) return a.category.localeCompare(b.category);
      return (a.sort_order - b.sort_order) || (a.id - b.id);
    });
  }

  function getMenu() {
    return getAllMenu().filter(m => m.is_available);
  }

  function createMenuItem(item) {
    const menu = read(KEYS.menu, []);
    const id = nextId('menu');
    const newItem = {
      id,
      category: item.category,
      icon: item.icon || '☕',
      name: item.name,
      description: item.description || '',
      base_price: parseInt(item.base_price) || 0,
      customizable: item.customizable ? 1 : 0,
      has_temp: item.has_temp ? 1 : 0,
      has_sweet: item.has_sweet ? 1 : 0,
      is_available: item.is_available !== undefined ? (item.is_available ? 1 : 0) : 1,
      sort_order: parseInt(item.sort_order) || 999,
      image_url: item.image_url || '',
      created_at: nowLocal(),
    };
    menu.push(newItem);
    write(KEYS.menu, menu);
    return newItem;
  }

  function updateMenuItem(id, patch) {
    const menu = read(KEYS.menu, []);
    const idx = menu.findIndex(m => m.id === id);
    if (idx === -1) throw new Error('品項不存在');
    Object.keys(patch).forEach(k => {
      if (['customizable', 'has_temp', 'has_sweet', 'is_available'].includes(k)) {
        menu[idx][k] = patch[k] ? 1 : 0;
      } else if (['base_price', 'sort_order'].includes(k)) {
        menu[idx][k] = parseInt(patch[k]) || 0;
      } else {
        menu[idx][k] = patch[k];
      }
    });
    write(KEYS.menu, menu);
    return menu[idx];
  }

  function deleteMenuItem(id) {
    const menu = read(KEYS.menu, []);
    const after = menu.filter(m => m.id !== id);
    if (after.length === menu.length) throw new Error('品項不存在');
    write(KEYS.menu, after);
    return true;
  }

  // ====== 訂單 ======
  function createOrder({ items, cash_received }) {
    if (!items || items.length === 0) throw new Error('訂單不能為空');
    const menu = read(KEYS.menu, []);
    const menuById = new Map(menu.map(m => [m.id, m]));

    // 後端式驗證:檢查上架狀態
    for (const it of items) {
      if (it.menu_item_id != null) {
        const m = menuById.get(it.menu_item_id);
        if (!m) throw new Error(`品項不存在 (id=${it.menu_item_id})`);
        if (!m.is_available) throw new Error(`「${m.name}」已售完,請重新選擇`);
      }
    }

    // 重新計算總額
    const total = items.reduce((s, it) => s + parseInt(it.unit_price) * parseInt(it.qty), 0);
    const cash = parseInt(cash_received) || 0;
    if (cash < total) throw new Error(`收取金額不足,還差 $${total - cash}`);

    const change = cash - total;
    const id = nextId('order');
    const order_no = 'A' + String(Date.now()).slice(-6);
    const order = {
      id,
      order_no,
      total,
      cash_received: cash,
      change_given: change,
      status: 'pending',
      created_at: nowLocal(),
      updated_at: nowLocal(),
      items: items.map(it => ({
        menu_item_id: it.menu_item_id,
        name: it.name,
        qty: parseInt(it.qty),
        unit_price: parseInt(it.unit_price),
        options: it.options || '',
      })),
    };

    const orders = read(KEYS.orders, []);
    orders.push(order);
    write(KEYS.orders, orders);
    return order;
  }

  function getOrders({ status, date } = {}) {
    let orders = read(KEYS.orders, []);
    if (status) orders = orders.filter(o => o.status === status);
    if (date)   orders = orders.filter(o => o.created_at.slice(0, 10) === date);
    return [...orders].sort((a, b) => b.created_at.localeCompare(a.created_at)).slice(0, 200);
  }

  function updateOrderStatus(id, status) {
    const VALID = ['pending', 'preparing', 'ready', 'completed', 'cancelled'];
    if (!VALID.includes(status)) throw new Error(`狀態須為 ${VALID.join(', ')} 之一`);
    const orders = read(KEYS.orders, []);
    const idx = orders.findIndex(o => o.id === id);
    if (idx === -1) throw new Error('訂單不存在');
    orders[idx].status = status;
    orders[idx].updated_at = nowLocal();
    write(KEYS.orders, orders);
    return { ok: true, status };
  }

  // ====== 統計 ======
  function getStats() {
    const today = todayStr();
    const orders = read(KEYS.orders, []);
    const valid = orders.filter(o => o.status !== 'cancelled');

    const todayOrders = valid.filter(o => o.created_at.slice(0, 10) === today);
    const todayRevenue = todayOrders.reduce((s, o) => s + o.total, 0);
    const allRevenue = valid.reduce((s, o) => s + o.total, 0);

    const todayStatus = {};
    orders.filter(o => o.created_at.slice(0, 10) === today).forEach(o => {
      todayStatus[o.status] = (todayStatus[o.status] || 0) + 1;
    });

    function aggregate(list) {
      const map = new Map();
      list.forEach(o => {
        o.items.forEach(it => {
          const cur = map.get(it.name) || { name: it.name, qty: 0, revenue: 0 };
          cur.qty += it.qty;
          cur.revenue += it.qty * it.unit_price;
          map.set(it.name, cur);
        });
      });
      return [...map.values()].sort((a, b) => b.qty - a.qty).slice(0, 8);
    }

    // 過去 7 天每日營收
    const last7 = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const ds = d.toISOString().slice(0, 10);
      const dayOrders = valid.filter(o => o.created_at.slice(0, 10) === ds);
      if (dayOrders.length > 0) {
        last7.push({
          d: ds,
          orders: dayOrders.length,
          revenue: dayOrders.reduce((s, o) => s + o.total, 0),
        });
      }
    }

    return {
      today: { date: today, order_count: todayOrders.length, revenue: todayRevenue },
      all_time: { order_count: valid.length, revenue: allRevenue },
      today_status: todayStatus,
      hot_today: aggregate(todayOrders),
      hot_all: aggregate(valid),
      last7: last7,
    };
  }

  // ====== 維運 ======
  function exportAll() {
    return {
      version: 1,
      exported_at: nowLocal(),
      menu: read(KEYS.menu, []),
      orders: read(KEYS.orders, []),
      seq: read(KEYS.seq, {}),
    };
  }

  function importAll(data) {
    if (!data || !data.menu) throw new Error('資料格式錯誤');
    write(KEYS.menu, data.menu);
    write(KEYS.orders, data.orders || []);
    write(KEYS.seq, data.seq || { menu: data.menu.length, order: (data.orders || []).length });
  }

  function resetAll() {
    localStorage.removeItem(KEYS.menu);
    localStorage.removeItem(KEYS.orders);
    localStorage.removeItem(KEYS.seq);
    ensureSeeded();
  }

  function clearOrders() {
    write(KEYS.orders, []);
    const seq = read(KEYS.seq, {});
    seq.order = 0;
    write(KEYS.seq, seq);
  }

  // ====== 對外 ======
  window.db = {
    getMenu, getAllMenu, createMenuItem, updateMenuItem, deleteMenuItem,
    createOrder, getOrders, updateOrderStatus,
    getStats,
    exportAll, importAll, resetAll, clearOrders,
  };
})();
