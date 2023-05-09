from app import db, app

# Charting dependencies
import plotly
import plotly.graph_objs as go
import json

"""
Utilities for listing and managing users and roles
"""

# import the database schema
from app.models import User
from app.models import OAuth
from app.models import Role
from app.models import UserRoles



def add_role(role_name):
    """add a new role"""
    role = Role(name=role_name)
    db.session.add(role)
    db.session.commit()


def add_user_to_role(email, role_name):
    """add user to role"""
    user = User.query.filter_by(email=email).first()
    role = Role.query.filter_by(name=role_name).first()
    user.roles.append(role)
    db.session.commit()
    app.logger.info("Add user {} to role {}".format(email, role_name))


def get_roles():
    roles = Role.query.all()
    for r in roles:
        print(f"{r.id}, {r.name}")


def count_users_in_role(role_name):
    result = db.session.execute("""SELECT count(*)
                                    FROM user
                                    LEFT JOIN user_roles ON user.id = user_roles.user_id
                                    JOIN role ON role.id = user_roles.role_id
                                    WHERE role.name = :val""", {'val': role_name})
    count = int(result.fetchall()[0][0])
    return count


def get_users():
    users = User.query.all()
    for u in users:
        print(f"{u.email}, {u.username}")

def get_user_roles(email):
    user = User.query.filter_by(email=email).first()
    for r in user.roles:
        print(f"{r.id}, {r.name}")

def del_role(role_name):
    """remove a role"""
    role = Role.query.filter_by(name=role_name).first()
    db.session.delete(role)
    db.session.commit()

def del_user_from_role(email, role_name):
    """remove user from role"""
    user = User.query.filter_by(email=email).first()
    role = Role.query.filter_by(name=role_name).first()
    user.roles.remove(role)
    db.session.commit()
    app.logger.info("Remove user {} from role {}".format(email, role_name))


def create_bar_plot(x_list
                    , y_list
                    , y_label=None
                    , y_range=None
                    , show_legend=True
                    , legend_bottom=False
                    , legend_labels=None
                    , line_dict_list=None
                    , stacked=False
                    , colors_list=None
                    , **kwargs):
    """
    Function for creating JSON encoding for Plotly bar charts.
    Supply a list of X categories or tick-marks and a list of y-vals for each x-tick.
    Ref:
    https://github.com/plotly/plotly.py/blob/master/doc/python/bar-charts.md
    https://plotly.com/python/reference/bar/
    https://plotly.com/python/configuration-options/ - configuration can be placed in the HTML template
    https://plotly.com/python/creating-and-updating-figures/

    Optionally pass in one or more line_dict to draw a horizntal line. EG:
        line_dict_list = {'x0':-0.5, 'x1':5.5, 'y0':3, 'y1':3, 'colour':"red", 'name':"target", 'type':"dash" }
        If line_dict_list is a list, not a dict, unpack a list of line_dicts and plot each one
        If it is just a dict, process the dict to plot a single line

    specify the colours of the bars by passing in a list of colours EG:
        colors_list
    """

    # function to see if this is a nested list
    depth = lambda L: isinstance(L, list) and max(map(depth, L)) + 1

    # If no colours supplied, generate a list as long as the x-list
    #if not colors_list:
    #    colors_list = ['#636EFA', ] * len(x_list)  # same colour for all bars defined in x-list

    # Create a Plotly Figure object
    fig = go.Figure()

    # add y values to a figure for single feature set or stacked/multi-feature chart, with legends if specified
    if depth(y_list) == 1:
        if legend_labels is None:
            show_legend = False
            legend_labels = ["0"]
        fig.add_trace((go.Bar(x=x_list, y=y_list, marker_color=colors_list, name=legend_labels[0], textposition='auto')))
    elif depth(y_list) == 2:
        if legend_labels is None:
            legend_labels = range(0, len(y_list))
        for i, y_stack in enumerate(y_list):
            fig.add_trace((go.Bar(x=x_list, y=y_stack, name=legend_labels[i], textposition="outside")))
    else:
        raise ValueError("y-axis values structure is invalid")

    if stacked:
        fig.update_layout(barmode='stack')

    # set the y-axis label
    fig.update_yaxes(title_text=y_label)

    if legend_bottom:
        fig.update_layout(legend=dict(orientation="h"))

    # y_range is a list with start and stop end-points i.e. [0, 20] to scale y-axis 0 to 20
    if y_range:
        fig.update_yaxes(range=y_range)

    # add remaining options to layout from kwargs - https://plotly.com/python/reference/bar/
    for arg, value in kwargs.items():
        # angle the x-axis labels
        if arg == 'xaxis_tickangle': fig.update_layout(xaxis_tickangle=value)
        # set the mouse-over hover mode
        if arg == 'hovermode': fig.update_layout(hovermode=value)


    # Option to add a horizontal line
    if line_dict_list:

        # if just a single dict, convert to list with one element to iterate over
        if isinstance(line_dict_list, dict):
            line_dicts = [line_dict_list]
        else:
            line_dicts = line_dict_list

        dash_type = 'solid'
        for line_dict in line_dicts:

            if 'type' in line_dict:
                dash_type = line_dict['type']

            fig.add_shape(type="line", x0=line_dict['x0'], y0=line_dict['y0'], x1=line_dict['x1'],
                          y1=line_dict['y1']
                          , line=dict(color=line_dict['colour'], dash=dash_type, width=3))
            if 'name' in line_dict:
                fig.add_annotation(x=line_dict['x1'], y=line_dict['y1'],
                                   text=line_dict['name'],
                                   showarrow=False,
                                   yshift=10)

    # Update Figure layout options
    fig.update_layout(
        margin=dict(l=60, r=60, t=20, b=20),
        paper_bgcolor="White", plot_bgcolor="White",
        showlegend=show_legend
    )

    # return a JSON object suitable for Plotly JavaScript plot libs
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)



