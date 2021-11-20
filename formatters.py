def make_caption(product):
    name = product["name"]
    description = product["description"]
    price = product["meta"]["display_price"]["with_tax"]["formatted"]
    stock_qty = product["meta"]["stock"]["level"]
    return f"{name}\n\n{price} per kg\n{stock_qty} kg in stock\n\n{description}"


def make_cart_repr(cart):
    products = []
    for item in cart["data"]:
        name = item["name"]
        description = item["description"]
        quantity = item["quantity"]
        price = item["meta"]["display_price"]["with_tax"]["unit"]["formatted"]
        value = item["meta"]["display_price"]["with_tax"]["value"]["formatted"]
        products.append(
            f"{name}\n{description}\n{price} per kg\n{quantity} kg in cart for {value}"
        )
    products.append(f'Total: {cart["meta"]["display_price"]["with_tax"]["formatted"]}')
    return "\n\n".join(products)