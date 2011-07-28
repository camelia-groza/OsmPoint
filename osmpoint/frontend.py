import flask
import yaml
import os
from flaskext.openid import OpenID
from wtforms import BooleanField, TextField, DecimalField, HiddenField
from wtforms import SelectField, Form, validators
from .database import db, Point
from .database import add_point, del_point, submit_points_to_osm


oid = OpenID()


class EditPointForm(Form):
    name = TextField('name', [validators.Required()])
    url = TextField('url')
    lat = DecimalField('lat', [validators.NumberRange(min=-90, max=90)])
    lon = DecimalField('lon', [validators.NumberRange(min=-180, max=180)])

    ops_file = os.path.join(os.path.dirname(__file__), 'amenities.yaml')
    options = yaml.load(file(ops_file, 'r'))
    for i, j in enumerate(options):
        options[i] = tuple(options[i])
    amenity = SelectField('amenity', choices=options)

    new_amenity = TextField('new_amenity')
    id = HiddenField('id', [validators.Optional()])


frontend = flask.Blueprint('frontend', __name__)

@frontend.before_request
def lookup_current_user():
    flask.g.user = None
    if 'openid' in flask.session:
        flask.g.user = flask.session['openid']

@frontend.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if flask.g.user is not None:
        return flask.redirect(oid.get_next_url())
    if flask.request.method == 'POST':
        openid = flask.request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email', 'fullname',
                                                  'nickname'])
    return flask.render_template('login.html',
                                 next=oid.get_next_url(),
                                 error=oid.fetch_error())

def is_admin():
    return  flask.g.user in flask.current_app.config['OSMPOINT_ADMINS']

@frontend.route('/logout')
def logout():
    if flask.g.user is None:
        return flask.abort(400)
    del flask.session['openid']
    return flask.redirect('/')

@oid.after_login
def create_or_login(resp):
    flask.session['openid'] = resp.identity_url
    return flask.redirect('/')

@frontend.route("/addPOI")
def init():
    return flask.render_template('home.html')

@frontend.route("/save_poi", methods=['POST'])
def save_poi():
    if flask.g.user is None:
        return flask.redirect('/login')

    form = EditPointForm(flask.request.form)

    if form.validate():
        if form.amenity.data == 'none' and form.new_amenity.data == "":
            ok_type = False
        else:
            if form.amenity.data == 'none':
                amenity = form.new_amenity.data
            else:
                amenity = form.amenity.data
            add_point(form.lat.data, form.lon.data, form.name.data,
                      form.url.data, amenity, flask.g.user)
            return flask.redirect('/thank_you')

    try:
        if ok_type is False:
            pass
    except UnboundLocalError:
        ok_type = form.amenity.validate(form)

    ok_name = form.name.validate(form)
    ok_coords = form.lat.validate(form) and form.lon.validate(form)
    return flask.render_template('edit.html', ok_coords=ok_coords,
                                 ok_name=ok_name, ok_type=ok_type)


@frontend.route("/thank_you")
def thank_you():
    return flask.render_template('thank_you.html')

@frontend.route("/")
def homepage():
    sent_points = Point.query.filter(Point.osm_id!=None).all()
    local_points = Point.query.filter(Point.osm_id==None).all()
    return flask.render_template('explore.html',
                                 sent_points=sent_points,
                                 local_points=local_points)

@frontend.route("/points")
def show_points():
    local_points = Point.query.filter(Point.osm_id==None).all()
    sent_points = Point.query.filter(Point.osm_id!=None).all()

    return flask.render_template('points.html',
                                 local_points=local_points,
                                 sent_points=sent_points)

@frontend.route("/points/<int:point_id>/delete", methods=['POST'])
def delete_point(point_id):
    form = flask.request.form
    point = Point.query.get_or_404(form['id'])

    if not is_admin():
        flask.abort(403)

    if form['confirm'] == "false":
        address = flask.url_for('.show_map', point_id=point.id)
        return flask.redirect(address)

    if form['confirm'] == "true":
        del_point(point)

    return flask.render_template('deleted.html', confirm=form['confirm'],
                                                 point=point)

@frontend.route("/points/<int:point_id>")
def show_map(point_id):
    point = Point.query.get_or_404(point_id)

    return flask.render_template('view.html', point=point,
                                  is_admin=is_admin())


@frontend.route("/points/<int:point_id>/edit", methods=['POST'])
def edit_point(point_id):
    form = EditPointForm(flask.request.form)
    point = Point.query.get_or_404(form.id.data)

    if not is_admin():
        flask.abort(403)

    if form.validate():
        if form.amenity.data == 'none' and form.new_amenity.data == "":
            ok_type = False
        else:
            if form.amenity.data == 'none':
                form.amenity.data = form.new_amenity.data
            form.populate_obj(point)
            point.latitude = form.lat.data
            point.longitude = form.lon.data

            db.session.add(point)
            db.session.commit()
            return flask.render_template('edit.html', ok_coords=1,
                                         ok_name=1, ok_type=1, id=point.id)

    try:
        if ok_type is False:
            pass
    except UnboundLocalError:
        ok_type = form.amenity.validate(form)

    ok_name = form.name.validate(form)
    ok_coords = form.lat.validate(form) and form.lon.validate(form)
    return flask.render_template('edit.html', ok_coords=ok_coords,
                                 ok_name=ok_name, ok_type=ok_type, id=point.id)

@frontend.route("/points/<int:point_id>/send", methods=['POST'])
def send_point(point_id):
    if not is_admin():
        flask.abort(403)

    form = flask.request.form
    point = Point.query.get_or_404(form['id'])

    if point.osm_id is not None:
        flask.abort(400)

    submit_points_to_osm(point)
    return flask.render_template('sent.html', id=point.id)

