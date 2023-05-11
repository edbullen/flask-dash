import logging

from app import app
from flask import redirect, url_for, flash, render_template, session, request

# SQL Alchemy imports
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm.exc import NoResultFound

from flask_login import (
    LoginManager, UserMixin, current_user,
    login_required, login_user, logout_user, current_user
)

from functools import wraps

# Flask web-app data and web-form imports
from app.models import User
from app.models import OAuth
from app.models import Role
from app.models import UserRoles

from app.forms import EditProfileForm, FindUsersForm

# Utils for managing users
from app.utils import add_user_to_role
from app.utils import del_user_from_role

# Databricks connectivity
from app.databricks import SparkConnect

# Utils for generating chart JSON
from app.graph_utils import create_bar_plot
from app.graph_utils import simple_bar_plot

# pyspark imports
from pyspark.sql.types import LongType, IntegerType, StringType
from pyspark.sql.functions import udf

# db = SQLAlchemy()

# Decorator to check what role the user is in and return to /index if not a member
def access_required(role):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            roles = [r.name for r in current_user.roles]
            if role not in roles:
                flash("Permission Denied - not a member of the role \"{}\"".format(role), 'danger')
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return decorated_view

    return wrapper


# logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    # flash("Successfully logged out", "info")
    return redirect(url_for("index"))


# landing page for authenticated and non-authenticated users
@app.route("/")
def index():

    spark = SparkConnect.spark
    cluster_id = SparkConnect.cluster_id

    return render_template("index.html")


# example of page that session has to be logged in to see
@app.route("/protected")
@login_required
def protected():
    roles = [r.name for r in current_user.roles]

    return render_template("protected.html", roles=roles)


# user profile
@app.route('/profile/<email>')
@login_required
def profile(email):
    u = User.query.filter_by(email=email).first_or_404()

    user_roles = [r.name for r in u.roles]
    all_roles = [r.name for r in Role.query.all()]

    session["user_email"] = u.email

    if current_user.email != u.email and not current_user.is_admin:
        flash("Permission Denied", 'danger')
        return redirect(url_for('index'))
    else:
        return render_template('profile.html', user_roles=user_roles, all_roles=all_roles, user=u)


# user profile edit
@app.route('/profile_edit', methods=['GET', 'POST'])
@login_required
@access_required(role="admin")
def profile_edit():
    u = User.query.filter_by(email=session.get("user_email")).first_or_404()
    user_roles = [r.name for r in u.roles]
    all_roles = [r.name for r in Role.query.all()]

    # Initialise the form with the users email, roles available, current roles
    form = EditProfileForm(u.email, all_roles, user_roles)

    if form.validate_on_submit():
        new_roles = request.form.getlist('rolescheckbox')
        # process new roles and add if necessary
        for nr in new_roles:
            if nr not in user_roles:
                add_user_to_role(u.email, nr)
                # flash("Added {} to role \"{}\"".format(u.email, nr), "info")
        # process existing roles and remove if necessary
        for xr in user_roles:
            if xr not in new_roles:
                del_user_from_role(u.email, xr)
                # flash("Removed {} from role \"{}\"".format(u.email, xr), "info")

        # refresh the user_roles
        user_roles = [r.name for r in u.roles]
        return render_template('profile.html'
                               , title='Profile'
                               , user_roles=user_roles
                               , all_roles=all_roles
                               , user=u)

    elif request.method == 'GET':
        form.email.data = u.email

        return render_template('profile_edit.html'
                               , title='Edit Profile'
                               , form=form
                               , user_roles=user_roles
                               , all_roles=all_roles
                               , user=u)
    else:
        flash('Form submit error', 'danger')
        for field_name, error_messages in form.errors.items():
            for err in error_messages:
                app.logger.error("profile_edit() form submit error - Field: {}, Message: {}".format(field_name, err))

    return render_template('profile_edit.html'
                           , form=form
                           , title='Edit Profile'
                           , user_roles=user_roles
                           , all_roles=all_roles
                           , user=u)


# example of page that session has to be logged in to see and the user has to be a member of group "admin"
@app.route("/find_users", methods=['GET', 'POST'])
@login_required
@access_required(role="admin")
def find_users():
    # Initialise the form with the users email, roles available, current roles
    form = FindUsersForm()

    return render_template("find_users.html", form=form)


# example of page that session has to be logged in to see and the user has to be a member of group "admin"
@app.route("/admin")
@login_required
@access_required(role="admin")
def admin():
    # app.logger.info("Testing Info Logging")
    # app.logger.warn("Testing Warn Logging")
    # app.logger.error("Testing Error Logging")

    return render_template("admin.html")


# example of page that session has to be logged in to see and the user has to be a member of group "user"
@app.route("/homepage")
@login_required
@access_required(role="user")
def homepage():
    return render_template("homepage.html")


# example of a Plotly chart
@app.route("/bar_chart_sample")
@login_required
@access_required(role="user")
def bar_chart_sample():

    x_ticks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    x_ticks = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]

    # list of lists to pass plot multiple stacked or side-by-side bar charts for
    y_array = [
          [3, 2, 1, 4, 5, 4, 4, 0, 0, 1]
        , [1, 1, 1, 1, 1, 0, 2, 3, 4, 5]
        , [1, 2, 1, 2, 1, 2, 1, 2, 1, 0]
        , [1, 2, 1, 2, 1, 2, 1, 2, 1, 0]
    ]
    legend_labels = ["thing", "stuff", "other", "bits"]

    # example for a single set of y-vals
    y_array = [3, 2, 1, 4, 5, 4, 4, 0, 0, 1]
    legend_labels = ["thing"]

    # Create the JSON for Plotly bar chart for 2 sets of y-val for each x axis tick mark
    bar_chart_json = create_bar_plot(x_list=[x for x in x_ticks]
                                     , y_list=y_array
                                     , y_label="Y-Axis"
                                     #, show_legend=False
                                     , stacked=True
                                     , line_dict_list=None
                                     , colors_list=None
                                     , legend_bottom=True
                                     , legend_labels=legend_labels
                                     , xaxis_tickangle=-45
                                     #, hovermode=False
                                     )

    return render_template("bar_chart_sample.html", plot1=bar_chart_json)


# example of a Plotly chart generated from Databricks data source
@app.route("/databricks_chart_sample")
@login_required
@access_required(role="user")
def databricks_chart_sample():

    # get data from Databricks
    spark = SparkConnect.spark
    cluster_id = SparkConnect.cluster_id
    try:

        df = spark.sql("""
           SELECT fare_amount,
               SUM(trip_distance) as SumTripDistance,
               AVG(trip_distance) as AvgTripDistance
           FROM samples.nyctaxi.trips
           WHERE trip_distance > 0 AND fare_amount > 0
           GROUP BY fare_amount
           ORDER BY fare_amount
        """)

        # bucketizer function
        def bucketizer(fare):
            if fare < 10:
                return "0_to_10"
            elif fare < 20:
                return "10_to_20"
            elif fare < 30:
                return "20_to_30"
            elif fare < 40:
                return "30_to_40"
            elif fare < 50:
                return "40_to_50"
            elif fare < 60:
                return "50_to_60"
            elif fare < 70:
                return "70_to_80"
            elif fare < 80:
                return "80_to_90"
            elif fare < 99:
                return "90_to_98"
            else:
                return "99_plus"

        # pyspark operation to run buckting fn on Spark against the taxi data set
        bucket_udf = udf(bucketizer, StringType())
        bucketed = df.withColumn("bucket", bucket_udf("fare_amount"))

        fare_buckets_and_trip_distances = bucketed.groupby('bucket').mean('AvgTripDistance').sort('bucket') \
            .withColumnRenamed("bucket", "fare").withColumnRenamed("avg(AvgTripDistance)", "avg_distance").toPandas()

    except Exception as e:
        fare_buckets_and_trip_distances = None
        app.logger.info(f"Databricks connect error: {str(e)}")
        flash("Databricks Connect Error - check webserverlogs", 'danger')

    x_ticks = fare_buckets_and_trip_distances['fare']
    y_array = list(fare_buckets_and_trip_distances['avg_distance'])

    legend_labels = None

    # Create the JSON for Plotly bar chart for 2 sets of y-val for each x axis tick mark
    bar_chart_json = simple_bar_plot(x_list=[x for x in x_ticks]
                                     , y_list=y_array
                                     , x_label="Fare Bucket"
                                     , y_label="Avg Distance"
                                     )

    return render_template("bar_chart_sample.html", plot1=bar_chart_json)