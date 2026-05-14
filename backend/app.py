"""暖陽咖啡 點餐系統 — Flask 後端 + REST API。"""
import json
import time
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory, abort
from database import init_db, get_conn, db_cursor

app = Flask(__name__, static_folder='static', static_url_path='/static')

ORDER_STATUSES = ['pending', 'preparing', 'ready', 'completed', 'cancelled']


# ========== 頁面路由 ==========
@app.route('/')
def root():
    return send_from_directory('static', 'customer.html')


@app.route('/admin')
def admin_page():
    return send_from_directory('static', 'admin.html')


# ========== 顧客端 API ==========
@app.route('/api/menu', methods=['GET'])
def get_menu():
    """顧客取菜單 — 只回上架品項。"""
    with db_cursor() as conn:
        rows = conn.execute("""
            SELECT * FROM menu_items
            WHERE is_available = 1
            ORDER BY category, sort_order, id
        """).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/orders', methods=['POST'])
def create_order():
    """送出訂單。

    Body:
      {
        "items": [
          {"menu_item_id": 3, "name": "拿鐵", "qty": 2, "unit_price": 105, "options": "熱 / 大杯 / 半糖"}
        ],
        "cash_received": 500
      }
    """
    data = request.get_json(force=True)
    items = data.get('items', [])
    cash = int(data.get('cash_received', 0))

    if not items:
        return jsonify({'error': '訂單不能為空'}), 400

    # 後端重新計算總額,不信任前端
    total = sum(int(it['unit_price']) * int(it['qty']) for it in items)
    if cash < total:
        return jsonify({'error': f'收取金額不足,還差 ${total - cash}'}), 400

    change = cash - total
    order_no = 'A' + str(int(time.time()))[-6:]

    with db_cursor() as conn:
        # 確認所有品項仍上架
        for it in items:
            mid = it.get('menu_item_id')
            if mid is None:
                continue
            row = conn.execute(
                "SELECT is_available, name FROM menu_items WHERE id=?", (mid,)
            ).fetchone()
            if row is None:
                return jsonify({'error': f'品項不存在 (id={mid})'}), 400
            if not row['is_available']:
                return jsonify({'error': f'「{row["name"]}」已售完,請重新選擇'}), 400

        cur = conn.execute("""
            INSERT INTO orders (order_no, total, cash_received, change_given, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (order_no, total, cash, change))
        order_id = cur.lastrowid

        for it in items:
            conn.execute("""
                INSERT INTO order_items (order_id, menu_item_id, name, qty, unit_price, options)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order_id,
                it.get('menu_item_id'),
                it['name'],
                int(it['qty']),
                int(it['unit_price']),
                it.get('options', ''),
            ))

    return jsonify({
        'order_id': order_id,
        'order_no': order_no,
        'total': total,
        'cash_received': cash,
        'change_given': change,
        'status': 'pending',
    }), 201


# ========== 後台 API ==========
@app.route('/api/admin/menu', methods=['GET'])
def admin_get_menu():
    """後台取所有菜單(含已下架)。"""
    with db_cursor() as conn:
        rows = conn.execute("""
            SELECT * FROM menu_items ORDER BY category, sort_order, id
        """).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/menu', methods=['POST'])
def admin_create_menu():
    data = request.get_json(force=True)
    required = ['category', 'name', 'base_price']
    if not all(k in data and data[k] != '' for k in required):
        return jsonify({'error': '缺少必填欄位 (category, name, base_price)'}), 400

    with db_cursor() as conn:
        cur = conn.execute("""
            INSERT INTO menu_items
                (category, icon, name, description, base_price,
                 customizable, has_temp, has_sweet, is_available, sort_order)
            VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            data['category'],
            data.get('icon', '☕'),
            data['name'],
            data.get('description', ''),
            int(data['base_price']),
            int(data.get('customizable', 1)),
            int(data.get('has_temp', 1)),
            int(data.get('has_sweet', 1)),
            int(data.get('is_available', 1)),
            int(data.get('sort_order', 999)),
        ))
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM menu_items WHERE id=?", (new_id,)).fetchone()
    return jsonify(dict(row)), 201


@app.route('/api/admin/menu/<int:item_id>', methods=['PUT'])
def admin_update_menu(item_id):
    data = request.get_json(force=True)
    fields = ['category', 'icon', 'name', 'description', 'base_price',
              'customizable', 'has_temp', 'has_sweet', 'is_available', 'sort_order']
    sets, values = [], []
    for f in fields:
        if f in data:
            sets.append(f'{f}=?')
            values.append(data[f])
    if not sets:
        return jsonify({'error': '沒有要更新的欄位'}), 400
    values.append(item_id)

    with db_cursor() as conn:
        result = conn.execute(
            f"UPDATE menu_items SET {', '.join(sets)} WHERE id=?", values
        )
        if result.rowcount == 0:
            return jsonify({'error': '品項不存在'}), 404
        row = conn.execute("SELECT * FROM menu_items WHERE id=?", (item_id,)).fetchone()
    return jsonify(dict(row))


@app.route('/api/admin/menu/<int:item_id>', methods=['DELETE'])
def admin_delete_menu(item_id):
    with db_cursor() as conn:
        result = conn.execute("DELETE FROM menu_items WHERE id=?", (item_id,))
        if result.rowcount == 0:
            return jsonify({'error': '品項不存在'}), 404
    return jsonify({'ok': True})


@app.route('/api/admin/orders', methods=['GET'])
def admin_get_orders():
    """訂單列表。可加 ?status=pending&date=2026-05-14 篩選。"""
    status = request.args.get('status')
    date_str = request.args.get('date')

    sql = "SELECT * FROM orders WHERE 1=1"
    params = []
    if status:
        sql += " AND status=?"
        params.append(status)
    if date_str:
        sql += " AND date(created_at)=?"
        params.append(date_str)
    sql += " ORDER BY created_at DESC LIMIT 200"

    with db_cursor() as conn:
        orders = [dict(r) for r in conn.execute(sql, params).fetchall()]
        if orders:
            ids = tuple(o['id'] for o in orders)
            placeholders = ','.join('?' * len(ids))
            items = conn.execute(
                f"SELECT * FROM order_items WHERE order_id IN ({placeholders})",
                ids
            ).fetchall()
            items_by_order = {}
            for it in items:
                items_by_order.setdefault(it['order_id'], []).append(dict(it))
            for o in orders:
                o['items'] = items_by_order.get(o['id'], [])
    return jsonify(orders)


@app.route('/api/admin/orders/<int:order_id>/status', methods=['PUT'])
def admin_update_order_status(order_id):
    data = request.get_json(force=True)
    new_status = data.get('status')
    if new_status not in ORDER_STATUSES:
        return jsonify({'error': f'狀態須為 {ORDER_STATUSES} 之一'}), 400

    with db_cursor() as conn:
        result = conn.execute("""
            UPDATE orders SET status=?, updated_at=datetime('now', 'localtime')
            WHERE id=?
        """, (new_status, order_id))
        if result.rowcount == 0:
            return jsonify({'error': '訂單不存在'}), 404
    return jsonify({'ok': True, 'status': new_status})


@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """統計:今日營收、訂單數、各狀態筆數、熱銷排行(本日 + 全期)。"""
    today = date.today().isoformat()
    with db_cursor() as conn:
        today_summary = conn.execute("""
            SELECT
              COUNT(*)              AS order_count,
              COALESCE(SUM(total),0) AS revenue
            FROM orders
            WHERE date(created_at)=? AND status != 'cancelled'
        """, (today,)).fetchone()

        all_summary = conn.execute("""
            SELECT
              COUNT(*)              AS order_count,
              COALESCE(SUM(total),0) AS revenue
            FROM orders
            WHERE status != 'cancelled'
        """).fetchone()

        status_rows = conn.execute("""
            SELECT status, COUNT(*) AS n
            FROM orders
            WHERE date(created_at)=?
            GROUP BY status
        """, (today,)).fetchall()

        hot_today = conn.execute("""
            SELECT oi.name, SUM(oi.qty) AS qty, SUM(oi.qty * oi.unit_price) AS revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE date(o.created_at)=? AND o.status != 'cancelled'
            GROUP BY oi.name
            ORDER BY qty DESC
            LIMIT 8
        """, (today,)).fetchall()

        hot_all = conn.execute("""
            SELECT oi.name, SUM(oi.qty) AS qty, SUM(oi.qty * oi.unit_price) AS revenue
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.status != 'cancelled'
            GROUP BY oi.name
            ORDER BY qty DESC
            LIMIT 8
        """).fetchall()

        # 過去 7 天每日營收
        last7 = conn.execute("""
            SELECT date(created_at) AS d,
                   COUNT(*)              AS orders,
                   COALESCE(SUM(total),0) AS revenue
            FROM orders
            WHERE status != 'cancelled'
              AND date(created_at) >= date('now', 'localtime', '-6 days')
            GROUP BY date(created_at)
            ORDER BY d
        """).fetchall()

    return jsonify({
        'today': {
            'date': today,
            'order_count': today_summary['order_count'],
            'revenue': today_summary['revenue'],
        },
        'all_time': {
            'order_count': all_summary['order_count'],
            'revenue': all_summary['revenue'],
        },
        'today_status': {r['status']: r['n'] for r in status_rows},
        'hot_today': [dict(r) for r in hot_today],
        'hot_all': [dict(r) for r in hot_all],
        'last7': [dict(r) for r in last7],
    })


# ========== 啟動 ==========
if __name__ == '__main__':
    import os
    init_db()
    port = int(os.environ.get('PORT', 5001))
    print('==============================================')
    print('☕ 暖陽咖啡 點餐系統 啟動中...')
    print(f'   顧客點餐機:  http://localhost:{port}/')
    print(f'   後台管理頁:  http://localhost:{port}/admin')
    print('==============================================')
    app.run(host='0.0.0.0', port=port, debug=True)
