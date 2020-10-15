#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# TODO: connect to a local postgresql database
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    genres = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy='dynamic')

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))
    shows = db.relationship('Show', backref="artist", lazy='dynamic')

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
  __tablename__ = 'Show'

  id = db.Column(db.Integer, primary_key=True)
  start_time = db.Column(db.DateTime())
  venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
  artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.

  # Get number of areas(cities) available
  areas = Venue.query.with_entities(Venue.city, func.count(Venue.city)).group_by(Venue.city).all()

  data = []

  for area in areas:
    # Get all venues in this city
    venues = Venue.query.filter_by(city=area[0]).all()
    venues_data = []
    for venue in venues:

      venues_data.append({
        "id": venue.id,
        "name": venue.name,
        # filter shows having start_time after today's date
        "num_upcoming_shows": venue.shows.filter(Show.start_time >= datetime.now()).count()
      })
    
    data.append({
      "city": area[0],
      "state": venues[0].state,
      "venues": venues_data
    })
  
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term=request.form.get('search_term', '')

  venues = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()

  response = {
    "count": len(venues),
    "data": venues
  }

  return render_template('pages/search_venues.html', results=response, search_term=search_term)

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = Venue.query.get(venue_id)

  data.upcoming_shows = data.shows.filter(Show.start_time >= datetime.now()).all()
  data.upcoming_shows_count = len(data.upcoming_shows)

  if data.upcoming_shows_count > 0:
    for show in data.upcoming_shows:
      # Convert Datetime object to String for Template Parser
      show.start_time = show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
      show.artist_id = show.artist.id
      show.artist_image_link = show.artist.image_link
      show.artist_name = show.artist.name

  data.past_shows = data.shows.filter(Show.start_time < datetime.now()).all()
  data.past_shows_count = len(data.past_shows)

  if data.past_shows_count > 0:
    for show in data.past_shows:
      show.start_time = show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
      show.artist_id = show.artist.id
      show.artist_image_link = show.artist.image_link
      show.artist_name = show.artist.name

  data.genres = data.genres.split(',')

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  venue = Venue(name = request.form['name'], city = request.form['city'],
                state = request.form['state'], address = request.form['address'],
                phone = request.form['phone'], genres = (',').join(request.form.getlist('genres')),
                facebook_link = request.form['facebook_link'])
  try:
    db.session.add(venue)
    db.session.commit()

  # on successful db insert, flash success
    flash('Venue ' + venue.name + ' was successfully listed!')
  except:
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' + venue.name + ' could not be listed.')

  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  venue = Venue.query.get(venue_id)
  try:
    venue.delete()

    db.session.commit()
  except:
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = Artist.query.with_entities(Artist.id, Artist.name)

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term=request.form.get('search_term', '')

  artists = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()

  response = {
    "count": len(artists),
    "data": artists
  }

  return render_template('pages/search_artists.html', results=response, search_term=search_term)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  data = Artist.query.get(artist_id)

  data.upcoming_shows = data.shows.filter(Show.start_time >= datetime.now()).all()
  data.upcoming_shows_count = len(data.upcoming_shows)

  if data.upcoming_shows_count > 0:
    for show in data.upcoming_shows:
      # Convert Datetime object to String for Template Parser
      show.start_time = show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
      show.venue_id = show.venue.id
      show.venue_image_link = show.venue.image_link
      show.venue_name = show.venue.name

  data.past_shows = data.shows.filter(Show.start_time < datetime.now()).all()
  data.past_shows_count = len(data.past_shows)

  if data.past_shows_count > 0:
    for show in data.past_shows:
      show.start_time = show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
      show.venue_id = show.venue.id
      show.venue_image_link = show.venue.image_link
      show.venue_name = show.venue.name

  data.genres = data.genres.split(',')

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)

  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.get(artist_id)

  artist.name = request.form.get('name', '')
  artist.city = request.form.get('city', '')
  artist.state = request.form.get('state', '')
  artist.phone = request.form.get('phone', '')
  artist.facebook_link = request.form.get('facebook_link', '')
  artist.genres = (',').join(request.form.getlist('genres'))

  db.session.commit()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.get(venue_id)

  venue.name = request.form.get('name', '')
  venue.city = request.form.get('city', '')
  venue.state = request.form.get('state', '')
  venue.address = request.form.get('address', '')
  venue.phone = request.form.get('phone', '')
  venue.facebook_link = request.form.get('facebook_link', '')
  venue.genres = (',').join(request.form.getlist('genres'))

  db.session.commit()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  artist = Artist(name = request.form['name'], city = request.form['city'],
                state = request.form['state'], phone = request.form['phone'], 
                genres = (',').join(request.form.getlist('genres')),
                facebook_link = request.form['facebook_link'])
  try:
    db.session.add(artist)
    db.session.commit()

  # on successful db insert, flash success
    flash('Artist ' + artist.name + ' was successfully listed!')
  except:
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + artist.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data = Show.query.all()
  for show in data:
    show.venue_name = show.venue.name
    show.artist_name = show.artist.name
    show.artist_image_link = show.artist.image_link
    show.start_time = show.start_time.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  show = Show(artist_id = request.form['artist_id'],
              venue_id = request.form['venue_id'],
              start_time = request.form['start_time'])
  try:
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  except:
  # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Show could not be listed.')
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
