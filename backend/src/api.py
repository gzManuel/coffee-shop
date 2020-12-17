import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
'''
# db_drop_and_create_all()

# ROUTES


@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()
    # If there's not drinks, abort(404).
    if len(drinks) == 0:
        abort(404)  # Not found.
    # Using list comprehension to get a list of drinks short model
    # representation.
    list_of_drinks = [drink.short() for drink in drinks]
    return jsonify({'success': True, 'drinks': list_of_drinks}), 200


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    drinks = Drink.query.all()
    # If there's not drinks, abort(404).
    if len(drinks) == 0:
        abort(404)  # Not found.
    # Using list comprehension to get a list of drinks long model
    # representation.
    list_of_drinks = [drink.long() for drink in drinks]

    return jsonify({'success': True, 'drinks': list_of_drinks}), 200


@app.route('/drinks', methods=["POST"])
@requires_auth('post:drinks')
def add_drink(jwt):
    title = request.json.get('title')
    recipe = request.json.get('recipe')

    # If the client don't send a title or a recipe data, then abort(400).
    if title is None or recipe is None:
        abort(400)  # Bad request.
    try:
        drink = Drink()
        drink.title = title
        # Formatting recipe, changing ' by " to avoid a bug with json.load().
        drink.recipe = str(recipe).replace("\'", "\"")
        drink.insert()
        return jsonify({"success": True, "drinks": drink.long()}), 200
    except exc.DataError:
        abort(422)  # Unprocessable entity.

@app.route('/drinks/<int:id>', methods=["PATCH"])
@requires_auth('patch:drinks')
def update_drink(jwt, id):
    try:
        drink = Drink.query.filter_by(id=id).one_or_none()
        # If the id recieved is not in the database, abort(404).
        if drink is None:
            abort(404)
        title = request.json.get('title')
        recipe = request.json.get('recipe')

        # If the client don't send any data to change the drink, abort(400).
        if title is None and recipe is None:
            abort(400)  # Bad request.
        # If title is not None we can change title with new title.
        if title is not None:
            drink.title = title
        # If recipe is not None we can change recipe with new recipe.
        if recipe is not None:
            # Formatting recipe, changing ' for " to avoid a bug
            # with json.load().
            drink.recipe = str(recipe).replace("\'", "\"")
        drink.update()
        return jsonify({"success": True, "drinks": drink.long()}), 200
    except exc.DataError:
        abort(422)  # Unprocessable entity.


@app.route('/drinks/<int:id>', methods=["DELETE"])
@requires_auth('delete:drinks')
def delete_drink(jwt, id):
    drink = Drink.query.filter_by(id=id).one_or_none()
    # If the id recieved is not in the database, abort(404).
    if drink is None:
        abort(404)
    drink.delete()
    return jsonify({"success": True, "delete": id})

# Error Handling


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422


@app.errorhandler(404)
def notfound(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


@app.errorhandler(400)
def bad_request(ex):
    return jsonify({
                    "success": False,
                    "error": 400,
                    "message": "bad request"
                    }), 400
