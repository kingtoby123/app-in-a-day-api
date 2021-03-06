from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow
from flask_cors import CORS 

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] ="postgresql://ujtwpoarzwjpet:ca12a738a9d383736fa0aeca18f8c391ce713cd11fc8f7257012d9b2c7b5b4f7@ec2-54-196-33-23.compute-1.amazonaws.com:5432/d7verqcd0hd000"

db = SQLAlchemy(app)
ma = Marshmallow(app)
CORS(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String, nullable=False)
    collection = db.Column(db.String)
    name = db.Column(db.String, nullable=False, unique=True)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)
    featured_image = db.Column(db.String, nullable=False)
    images = db.relationship("Image", backref="product", cascade="all, delete, delete-orphan")

    def __init__(self, category, collection, name, description, price, featured_image):
        self.category = category
        self.collection = collection
        self.name = name
        self.description = description
        self.price = price
        self.featured_image = featured_image


class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_url = db.Column(db.String)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)

    def __init__(self, image_url, product_id):
        self.image_url = image_url
        self.product_id = product_id

class ImageSchema(ma.Schema):
    class Meta:
        fields = ("id", "image_url", "product_id")

image_schema = ImageSchema()
multi_image_schema = ImageSchema(many=True)

class ProductSchema(ma.Schema):
    class Meta:
        fields = ("id", "category", "collection", "name", "description", "price", "featured_image", "images")
    images = ma.Nested(multi_image_schema)

product_schema = ProductSchema()
multi_product_schema = ProductSchema(many=True)


# PRODUCT ENDPOINTS
@app.route("/product/add", methods=["POST"])
def add_product():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    data = request.get_json()
    category = data.get("category")
    collection = data.get("collection")
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    featured_image = data.get("featured_image")
    favorited_by = data.get("favorited_by")

    existing_product_check = db.session.query(Product).filter(Product.name == name).filter(Product.category == category).first()
    if existing_product_check is not None:
        return jsonify("Error: Product already exists")

    new_product = Product(category, collection, name, description, price, featured_image)
    db.session.add(new_product)
    db.session.commit()

    return jsonify(product_schema.dump(new_product))

@app.route("/product/add/multi", methods=["POST"])
def add_multi_products():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    data = request.get_json().get("data")

    new_products = []

    for product in data:
        category = product.get("category")
        collection = product.get("collection")
        name = product.get("name")
        description = product.get("description")
        price = product.get("price")
        featured_image = product.get("featured_image")

        existing_product_check = db.session.query(Product).filter(Product.name == name).filter(Product.category == category).first()
        if existing_product_check is None:

            new_product = Product(category, collection, name, description, price, featured_image)
            db.session.add(new_product)
            db.session.commit()
            new_products.append(new_product)

    return jsonify(multi_product_schema.dump(new_products))

@app.route("/product/get", methods=["GET"])
def get_products():
    all_products = db.session.query(Product).all()
    return jsonify(multi_product_schema.dump(all_products))

@app.route("/product/get/id/<id>", methods=["GET"])
def get_products_by_id(id):
    products = db.session.query(Product).filter(Product.id == id).first()
    return jsonify(product_schema.dump(products))

@app.route("/product/get/category/<category>", methods=["GET"])
def get_products_by_category(category):
    this_category = db.session.query(Product).filter(Product.category == category).all()
    return jsonify(multi_product_schema.dump(this_category))

@app.route("/product/get/collection/<collection>", methods=["GET"])
def get_products_by_collection(collection):
    this_collection = db.session.query(Product).filter(Product.collection == collection).all()
    return jsonify(multi_product_schema.dump(this_collection))

@app.route("/product/update/id/<id>", methods=["PUT"])
def update_product(id):
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as json")

    data = request.get_json()
    category = data.get("category")
    collection = data.get("collection")
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    featured_image = data.get("featured_image")

    product = db.session.query(Product).filter(Product.id == id).first()

    if category != None:
        product.category = category
    if collection != None:
        product.collection = collection
    if name != None:
        product.name = name
    if description != None:
        product.description = description
    if price != None:
        product.price = price
    if featured_image != None:
        product.featured_image = featured_image
    db.session.commit()

    return jsonify(product_schema.dump(product))

@app.route("/product/delete/id/<id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.query(Product).filter(Product.id == id).first()
    db.session.delete(product)
    db.session.commit()
    return jsonify("Product successfully deleted")


# IMAGE ENDPOINTS
@app.route("/image/add", methods=["POST"])
def add_images():
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    data = request.get_json()
    image_url = data.get("image_url")
    product_id = data.get("product_id")

    existing_image_check = db.session.query(Image).filter(Image.image_url == image_url).first()
    if existing_image_check is not None:
        return jsonify("Error: Duplicate image. Please check url.")

    new_image = Image(image_url, product_id)
    db.session.add(new_image)
    db.session.commit()

    return jsonify(image_schema.dump(new_image))

@app.route("/image/get", methods=["GET"])
def get_all_images():
    all_images = db.session.query(Image).all()
    return jsonify(multi_image_schema.dump(all_images))

@app.route("/image/get/all/<product_id>", methods=["GET"])
def get_all_images_by_product_id(product_id):
    images = db.session.query(Image).filter(Image.product_id == product_id).all()
    return jsonify(multi_image_schema.dump(images))

@app.route("/image/update/id/<id>", methods=["PUT"])
def update_image(id):
    if request.content_type != "application/json":
        return jsonify("Error: Data must be sent as JSON")

    image_url = request.get_json().get("image_url")

    image = db.session.query(Image).filter(Image.id == id).first()

    if image_url != None:
        image.image_url = image_url

    db.session.commit()

    return jsonify(image_schema.dump(image))

@app.route("/image/delete/id/<id>", methods=["DELETE"])
def delete_image(id):
    image = db.session.query(Image).filter(Image.id == id).first()
    db.session.delete(image)
    db.session.commit()
    return jsonify("Image successfully deleted")


if __name__ == "__main__":
    app.run(debug=True)