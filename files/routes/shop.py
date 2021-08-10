from files.__main__ import app
from files.helpers.wrappers import *
from files.classes.shop import *


@app.get("/shop")
@auth_required
def shop_index(v):

    return render_template("shop/shop.html", v=v)


@app.get("/api/items/all")
def shop_items_get():

    cats_only = bool(int(request.args.get("cats_only", "0")))

    # option to load only categories without items
    if cats_only:

        # don't need to load related items here - overwrite default load with lazy load
        queer = g.db.query(ShopCategory).options(lazyload('*')).all()

        return jsonify([x.json_noitems for x in queer])

    queer = g.db.query(ShopCategory).all()
    data = [x.json for x in queer]

    # option to auto-add a featured section
    if 'with_featured' in request.args:
        queer2 = g.db.query(ShopItemDef).filter_by(featured=True).all()

        featured = {
            "id": 0,
            "name": "New & Noteworthy",
            "description": "These items are now being featured.",
            "items": [x.json for x in queer2]
        }

        data.append(featured)
        data = sorted(data, key=lambda x: x['id'])

    return jsonify(data)


@app.get("/api/items/featured")
def shop_items_featured():

    queer = g.db.query(ShopItemDef).filter_by(featured=True).all()

    return jsonify([x.json for x in queer])


@app.get("/api/items/mine")
@auth_required
def items_mine(v):

    queer = g.db.query(ShopItem).filter_by(user_id=v.id).all()

    return jsonify([x.json for x in queer])


@app.post("/api/items/mine/<iid>")
@auth_required
@validate_formkey
def purchase_item(iid, v):

    item = g.db.query(ShopItemDef).filter_by(id=iid).first()

    if not item:
        return jsonify({"error": "Invalid item"}), 404

    if item.cost > v.coins:
        return jsonify({"error": f"You need {item.cost - v.coins} more coins to buy this item."}), 403

    new_item = ShopItem(
        user_id=v.id,
        item_id=item.id
    )

    g.db.add(new_item)

    v.coins -= item.cost
    v.coins_spent += item.cost

    g.db.add(v)

    return jsonify({"message": f"{item.name} purchased"}), 201


# toggle featured status on item
@app.patch("/api/items/<iid>/featured")
@auth_required
@validate_formkey
def toggle_item_featured(iid, v):

    if v.admin_level < 6:
        return jsonify({"error": "Nice try retard"}), 403

    item = g.db.query(ShopItemDef).filter_by(id=iid).first()

    if not item:
        return jsonify({"error": "You tried to feature an item that doesn't even exist. Please do better."}), 404

    return_msg = f"{item.name} removed from featured" if item.featured else f"{item.name} is now featured"

    item.featured = not item.featured

    g.db.add(item)

    return jsonify({"message": return_msg})
